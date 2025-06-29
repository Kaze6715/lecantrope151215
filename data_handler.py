"""Data Handler for MT5 connection and data retrieval"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from typing import Dict, Optional, Union
import logging
from datetime import datetime, timedelta

class DataHandler:
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.symbol = config['trading']['symbol']
        self.timeframe_map = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1
        }

    def initialize_mt5(self) -> bool:
        """Initialize MT5 connection"""
        try:
            if not mt5.initialize(
                login=self.config['mt5']['login'],
                server=self.config['mt5']['server'],
                password=self.config['mt5']['password'],
                timeout=self.config['mt5']['timeout']
            ):
                raise ValueError(f"MT5 initialization failed: {mt5.last_error()}")
            
            # Select symbol
            if not mt5.symbol_select(self.symbol, True):
                raise ValueError(f"Symbol {self.symbol} selection failed")
            
            self.logger.info(f"MT5 initialized successfully. Connected to {self.config['mt5']['server']}")
            return True
            
        except Exception as e:
            self.logger.error(f"MT5 initialization error: {e}")
            return False

    def get_ohlcv_data(self, 
                       timeframe: Union[str, int], 
                       count: int = 1000) -> pd.DataFrame:
        """Get OHLCV data for specified timeframe"""
        try:
            # Convert timeframe string to MT5 timeframe
            if isinstance(timeframe, str):
                if timeframe not in self.timeframe_map:
                    raise ValueError(f"Invalid timeframe: {timeframe}")
                tf = self.timeframe_map[timeframe]
            else:
                tf = timeframe
            
            # Request OHLCV data
            rates = mt5.copy_rates_from_pos(self.symbol, tf, 0, count)
            if rates is None:
                raise ValueError(f"Failed to get OHLCV data: {mt5.last_error()}")
            
            # Convert to DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            return df
            
        except Exception as e:
            self.logger.error(f"OHLCV data retrieval error: {e}")
            return pd.DataFrame()

    def get_tick_data(self, count: int = 1000) -> pd.DataFrame:
        """Get recent tick data"""
        try:
            ticks = mt5.copy_ticks_from(
                self.symbol,
                datetime.now() - timedelta(minutes=5),
                count,
                mt5.COPY_TICKS_ALL
            )
            if ticks is None:
                raise ValueError(f"Failed to get tick data: {mt5.last_error()}")
            
            df = pd.DataFrame(ticks)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            return df
            
        except Exception as e:
            self.logger.error(f"Tick data retrieval error: {e}")
            return pd.DataFrame()

    def get_symbol_info(self) -> Optional[Dict]:
        """Get symbol information"""
        try:
            info = mt5.symbol_info(self.symbol)
            if info is None:
                raise ValueError(f"Failed to get symbol info: {mt5.last_error()}")
            
            return {
                'spread': info.spread,
                'tick_size': info.trade_tick_size,
                'tick_value': info.trade_tick_value,
                'volume_min': info.volume_min,
                'volume_max': info.volume_max,
                'volume_step': info.volume_step
            }
            
        except Exception as e:
            self.logger.error(f"Symbol info retrieval error: {e}")
            return None

    def get_account_info(self) -> Optional[Dict]:
        """Get account information"""
        try:
            info = mt5.account_info()
            if info is None:
                raise ValueError(f"Failed to get account info: {mt5.last_error()}")
            
            return {
                'balance': info.balance,
                'equity': info.equity,
                'margin': info.margin,
                'free_margin': info.margin_free,
                'profit': info.profit
            }
            
        except Exception as e:
            self.logger.error(f"Account info retrieval error: {e}")
            return None

    def shutdown(self):
        """Shutdown MT5 connection"""
        try:
            mt5.shutdown()
            self.logger.info("MT5 connection closed")
        except Exception as e:
            self.logger.error(f"MT5 shutdown error: {e}")