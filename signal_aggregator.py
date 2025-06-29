"""Signal Aggregator untuk mengintegrasikan semua analisis"""

import pandas as pd
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime, timezone
import logging
import MetaTrader5 as mt5  # Jangan import dari MT5.py, langsung dari MetaTrader5

from price_action_analyzer import PriceActionAnalyzer
from multi_timeframe_analyzer import MultitimeframeAnalyzer
from volume_analyzer import VolumeAnalyzer
from statistical_analyzer import StatisticalAnalyzer
from velocity_analyzer import VelocityAnalyzer
from microstructure_analyzer import MicrostructureAnalyzer
from market_context_analyzer import MarketContextAnalyzer
from smart_money_analyzer import SmartMoneyAnalyzer
from liquidity_analyzer import LiquidityAnalyzer

@dataclass
class AggregatedSignal:
    signal_type: str          # BULLISH, BEARISH, NEUTRAL
    total_score: float        # 0-200 points total
    is_valid: bool            # Score >= 170 (85%)
    timestamp: datetime
    component_signals: Dict   # Signals dari semua analyzer
    component_scores: Dict    # Scores dari semua analyzer
    key_levels: Dict          # Combined key levels
    entry_price: float        # Recommended entry
    sl_price: float           # Recommended stop loss
    tp_levels: List[float]    # Multiple take profit levels
    metrics: Dict             # Combined metrics

class SignalAggregator:
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize semua analyzers
        self.price_action = PriceActionAnalyzer(config)
        self.multi_tf = MultitimeframeAnalyzer(config)
        self.volume = VolumeAnalyzer(config)
        self.statistical = StatisticalAnalyzer(config)
        self.velocity = VelocityAnalyzer(config)
        self.micro = MicrostructureAnalyzer(config)
        self.market_context = MarketContextAnalyzer(config)
        self.smart_money = SmartMoneyAnalyzer(config)
        self.liquidity = LiquidityAnalyzer(config)
        
        # Scoring thresholds
        self.ENTRY_THRESHOLD = 99  # 85% confidence UBAHH DISINI BAYUWAHIDIN
        self.MIN_COMPONENT_SCORES = {
            'price_action': 20,     # Min 20/30
            'multi_tf': 25,         # Min 25/35
            'volume': 20,           # Min 15/20
            'statistical': 15,      # Min 15/20
            'velocity': 18,         # Min 18/25
            'micro': 18,            # Min 18/25
            'market_context': 18,   # Min 18/25
            'smart_money': 22,      # Min 22/30
            'liquidity': 25         # Min 25/35
        }

    def get_aggregated_signal(self, data_handler) -> AggregatedSignal:
        """Get aggregated signal dari semua analyzers"""
        try:
            # Get data untuk analysis
            m1_data = data_handler.get_ohlcv_data(mt5.TIMEFRAME_M1, 2000)
            tick_data = data_handler.get_tick_data(1000)
            
            if m1_data.empty or tick_data.empty:
                raise ValueError("Insufficient data for analysis")

            # Collect signals dari semua analyzers
            pa_signal = self.price_action.get_price_action_signal(m1_data)
            mtf_signal = self.multi_tf.get_mtf_signal(m1_data)
            vol_signal = self.volume.get_volume_signal(m1_data)
            stat_signal = self.statistical.get_statistical_signal(m1_data)
            vel_signal = self.velocity.get_velocity_signal(m1_data)
            micro_signal = self.micro.get_microstructure_signal(m1_data, tick_data)
            context_signal = self.market_context.get_market_context_signal(m1_data)
            sm_signal = self.smart_money.get_smart_money_signal(m1_data)
            liq_signal = self.liquidity.get_liquidity_signal(m1_data)

            # Collect component scores
            component_scores = {
                'price_action': float(getattr(pa_signal, 'strength', 0.0)),
                'multi_tf': float(getattr(mtf_signal, 'strength', 0.0)),
                'volume': float(getattr(vol_signal, 'strength', 0.0)),
                'statistical': float(getattr(stat_signal, 'strength', 0.0)),
                'velocity': float(getattr(vel_signal, 'strength', 0.0)),
                'micro': float(getattr(micro_signal, 'strength', 0.0)),
                'market_context': float(getattr(context_signal, 'strength', 0.0)),
                'smart_money': float(getattr(sm_signal, 'strength', 0.0)),
                'liquidity': float(getattr(liq_signal, 'strength', 0.0))
            }

            # Collect component signals
            component_signals = {
                'price_action': pa_signal,
                'multi_tf': mtf_signal,
                'volume': vol_signal,
                'statistical': stat_signal,
                'velocity': vel_signal,
                'micro': micro_signal,
                'market_context': context_signal,
                'smart_money': sm_signal,
                'liquidity': liq_signal
            }

            # Calculate total score
            total_score = sum(component_scores.values())

            # Validate minimum component scores
            is_valid = True
            for component, score in component_scores.items():
                if score < self.MIN_COMPONENT_SCORES[component]:
                    is_valid = False
                    self.logger.warning(f"Component {component} score below threshold: {score} < {self.MIN_COMPONENT_SCORES[component]}")
                    component_signals[component].signal_type = "NEUTRAL"     # Set to NEUTRAL if below threshold
                else:
                    self.logger.info(f"Component {component} score: {score}") 
                    break

            # Determine final signal type
            signals = [getattr(s, 'signal_type', "NEUTRAL") for s in component_signals.values()]
            bullish_count = signals.count("BULLISH")
            bearish_count = signals.count("BEARISH")

            if bullish_count > bearish_count:
                final_signal = "BULLISH"
            elif bearish_count > bullish_count:
                final_signal = "BEARISH"
            else:
                final_signal = "NEUTRAL"

            # Combine key levels (merge support/resistance from all signals)
            key_levels = {}
            for name, signal in component_signals.items():
                if hasattr(signal, 'key_levels') and getattr(signal, 'key_levels', None):
                    for k, v in signal.key_levels.items():
                        if k not in key_levels:
                            key_levels[k] = []
                        if isinstance(v, list):
                            key_levels[k] += v
                        else:
                            key_levels[k].append(v)

            # Calculate entry, SL, and TP prices
            current_price = m1_data['close'].iloc[-1]
            entry_price = current_price

            # SL based on liquidity levels and ATR
            atr = self.calculate_atr(m1_data)
            sl_distance = max(atr * 1.5, 5.0)  # Min 5 pips
            
            if final_signal == "BULLISH":
                sl_price = entry_price - sl_distance
                tp_levels = [
                    entry_price + (sl_distance * 1.5),  # TP1: 1.5R
                    entry_price + (sl_distance * 2.0),  # TP2: 2.0R
                    entry_price + (sl_distance * 3.0)   # TP3: 3.0R
                ]
            elif final_signal == "BEARISH":
                sl_price = entry_price + sl_distance
                tp_levels = [
                    entry_price - (sl_distance * 1.5),  # TP1
                    entry_price - (sl_distance * 2.0),  # TP2
                    entry_price - (sl_distance * 3.0)   # TP3
                ]
            else:
                sl_price = 0.0
                tp_levels = []

            # Combine all metrics
            metrics = {
                'component_scores': component_scores,
                'min_scores_met': is_valid,
                'total_confidence': (total_score / 200) * 100,
                'signal_counts': {
                    'bullish': bullish_count,
                    'bearish': bearish_count,
                    'neutral': len(signals) - bullish_count - bearish_count
                },
                'atr': atr
            }

            return AggregatedSignal(
                signal_type=final_signal,
                total_score=total_score,
                is_valid=is_valid and total_score >= self.ENTRY_THRESHOLD,
                timestamp=datetime.now(timezone.utc),
                component_signals=component_signals,
                component_scores=component_scores,
                key_levels=key_levels,
                entry_price=entry_price,
                sl_price=sl_price,
                tp_levels=tp_levels,
                metrics=metrics
            )

        except Exception as e:
            self.logger.error(f"Signal aggregation error: {e}")
            return AggregatedSignal(
                signal_type="NEUTRAL",
                total_score=0.0,
                is_valid=False,
                timestamp=datetime.now(timezone.utc),
                component_signals={},
                component_scores={},
                key_levels={},
                entry_price=0.0,
                sl_price=0.0,
                tp_levels=[],
                metrics={}
            )

    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range"""
        try:
            high = df['high']
            low = df['low']
            close = df['close']
            
            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())
            
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(period).mean().iloc[-1]
            
            return float(atr)
        except:
            return 5.0  # Default 5 pips if calculation fails