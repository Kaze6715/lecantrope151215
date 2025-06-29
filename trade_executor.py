"""Trade Executor untuk mengeksekusi dan mengelola trades"""

import MetaTrader5 as mt5
from typing import Dict, List
import logging
from datetime import datetime
# Import AggregatedSignal dari signal_aggregator
from signal_aggregator import AggregatedSignal

class TradeExecutor:
    def __init__(self, config: Dict):
        self.config = config
        self.symbol = config['trading']['symbol']
        self.risk_percent = config['trading']['risk_percent']
        self.max_spread = config['trading']['max_spread']
        self.min_volume = config['trading']['min_volume']
        self.max_volume = config['trading']['max_volume']
        self.slippage = config['trading']['slippage']
        self.logger = logging.getLogger(__name__)

    def calculate_position_size(self, 
                              entry_price: float, 
                              sl_price: float, 
                              risk_amount: float) -> float:
        """Calculate position size based on risk"""
        try:
            if not entry_price or not sl_price:
                return self.min_volume

            # Get account info
            account_info = mt5.account_info()
            if not account_info:
                raise ValueError("Could not get account info")

            balance = account_info.balance
            
            # Calculate risk amount
            risk_amount = balance * (self.risk_percent / 100)
            
            # Calculate stop loss in pips
            sl_pips = abs(entry_price - sl_price)
            if sl_pips == 0:
                return self.min_volume

            # Get symbol info
            symbol_info = mt5.symbol_info(self.symbol)
            if not symbol_info:
                raise ValueError(f"Could not get {self.symbol} info")

            # Calculate position size
            tick_value = symbol_info.trade_tick_value
            tick_size = symbol_info.trade_tick_size
            
            position_size = (risk_amount / sl_pips) * (tick_size / tick_value)
            
            # Normalize to symbol lots step
            position_size = round(position_size / symbol_info.volume_step) * symbol_info.volume_step
            
            # Apply limits
            position_size = max(min(position_size, self.max_volume), self.min_volume)
            
            return position_size

        except Exception as e:
            self.logger.error(f"Position size calculation error: {e}")
            return self.min_volume

    def execute_trade(self, signal: AggregatedSignal) -> Dict:
        """Execute trade based on signal"""
        try:
            if not signal.is_valid or signal.signal_type == "NEUTRAL":
                return {
                    'success': False,
                    'message': "Invalid or neutral signal"
                }

            # Check spread
            symbol_info = mt5.symbol_info(self.symbol)
            if not symbol_info:
                return {
                    'success': False,
                    'message': f"Could not get {self.symbol} info"
                }

            if symbol_info.spread > self.max_spread:
                return {
                    'success': False,
                    'message': f"Spread too high: {symbol_info.spread}"
                }

            # Calculate position size
            position_size = self.calculate_position_size(
                signal.entry_price,
                signal.sl_price,
                self.risk_percent
            )

            if position_size < self.min_volume:
                return {
                    'success': False,
                    'message': f"Position size too small: {position_size}"
                }

            # Prepare trade request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.symbol,
                "volume": position_size,
                "type": mt5.ORDER_TYPE_BUY if signal.signal_type == "BULLISH" else mt5.ORDER_TYPE_SELL,
                "price": signal.entry_price,
                "sl": signal.sl_price,
                "tp": signal.tp_levels[0] if signal.tp_levels else 0.0,
                "deviation": self.slippage,
                "magic": 123456,
                "comment": f"Anti-Sweep Bot Score:{signal.total_score:.1f}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_FOK,
            }

            # Send trade
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return {
                    'success': False,
                    'message': f"Order failed: {result.comment}"
                }

            # If first TP hit, modify remaining position
            if len(signal.tp_levels) > 1:
                # Split position for multiple TPs
                self.modify_position_for_multiple_tps(
                    result.order,
                    signal.tp_levels,
                    position_size
                )

            return {
                'success': True,
                'message': "Order executed successfully",
                'order_id': result.order,
                'volume': position_size,
                'entry': signal.entry_price,
                'sl': signal.sl_price,
                'tp_levels': signal.tp_levels
            }

        except Exception as e:
            self.logger.error(f"Trade execution error: {e}")
            return {
                'success': False,
                'message': f"Execution error: {str(e)}"
            }

    def modify_position_for_multiple_tps(self, 
                                       order_id: int, 
                                       tp_levels: List[float],
                                       original_volume: float):
        """Modify position for multiple take profits"""
        try:
            position = mt5.positions_get(ticket=order_id)
            if not position:
                return
            
            position = position[0]
            
            # Calculate volumes for each TP level
            volumes = [
                original_volume * 0.5,  # 50% at TP1
                original_volume * 0.3,  # 30% at TP2
                original_volume * 0.2   # 20% at TP3
            ]

            # Modify main position for TP1
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": order_id,
                "symbol": self.symbol,
                "sl": position.sl,
                "tp": tp_levels[0],
                "magic": 123456
            }
            
            mt5.order_send(request)

            # Create additional orders for TP2 and TP3
            for i, (tp, vol) in enumerate(zip(tp_levels[1:], volumes[1:]), 1):
                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": self.symbol,
                    "volume": vol,
                    "type": position.type,
                    "price": position.price_open,
                    "sl": position.sl,
                    "tp": tp,
                    "deviation": self.slippage,
                    "magic": 123456,
                    "comment": f"TP{i+1} Anti-Sweep",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_FOK,
                }
                
                mt5.order_send(request)

        except Exception as e:
            self.logger.error(f"Multiple TP modification error: {e}")