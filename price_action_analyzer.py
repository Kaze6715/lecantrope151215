"""
Price Action Analysis Module
Author: Kaztanaifreedom
Version: 2.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime, timezone
import logging
import talib

class PriceActionSignal:
    def __init__(self):
        self.signal_type = None
        self.strength = 0.0
        self.patterns = []
        self.key_levels = {}
        self.entry_price = None
        self.stop_loss = None
        self.take_profit = None

class PriceActionAnalyzer:
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Configuration parameters
        self.swing_period = 20
        self.trend_period = 200
        self.vol_period = 14
        self.min_pattern_size = 3
        
        # Pattern score weights
        self.weights = {
            'trend': 8.0,         # Max 8 points
            'patterns': 7.0,      # Max 7 points
            'momentum': 6.0,      # Max 5 points
            'support_res': 6.0,   # Max 5 points
            'volatility': 5.0     # Max 5 points
        }

    def identify_candlestick_patterns(self, df: pd.DataFrame) -> List[str]:
        """Identify Japanese candlestick patterns"""
        patterns = []
        
        # Single Candlestick Patterns
        doji = talib.CDLDOJI(df['open'], df['high'], df['low'], df['close'])
        hammer = talib.CDLHAMMER(df['open'], df['high'], df['low'], df['close'])
        shooting_star = talib.CDLSHOOTINGSTAR(df['open'], df['high'], df['low'], df['close'])
        
        # Multiple Candlestick Patterns
        engulfing = talib.CDLENGULFING(df['open'], df['high'], df['low'], df['close'])
        evening_star = talib.CDLEVENINGSTAR(df['open'], df['high'], df['low'], df['close'])
        morning_star = talib.CDLMORNINGSTAR(df['open'], df['high'], df['low'], df['close'])
        
        # Check last 3 candles for patterns
        last_idx = len(df) - 1
        if doji[last_idx] != 0: patterns.append(('Doji', doji[last_idx]))
        if hammer[last_idx] != 0: patterns.append(('Hammer', hammer[last_idx]))
        if shooting_star[last_idx] != 0: patterns.append(('Shooting Star', shooting_star[last_idx]))
        if engulfing[last_idx] != 0: patterns.append(('Engulfing', engulfing[last_idx]))
        if evening_star[last_idx] != 0: patterns.append(('Evening Star', evening_star[last_idx]))
        if morning_star[last_idx] != 0: patterns.append(('Morning Star', morning_star[last_idx]))
        
        return patterns

    def analyze_trend(self, df: pd.DataFrame) -> Dict:
        """Analyze price trend"""
        trend_info = {'direction': 'NEUTRAL', 'strength': 0}
        
        # Calculate EMAs
        ema20 = talib.EMA(df['close'], timeperiod=20)
        ema50 = talib.EMA(df['close'], timeperiod=50)
        ema200 = talib.EMA(df['close'], timeperiod=200)
        
        current_price = df['close'].iloc[-1]
        
        # Determine trend direction
        if current_price > ema20.iloc[-1] > ema50.iloc[-1] > ema200.iloc[-1]:
            trend_info['direction'] = 'BULLISH'
            trend_info['strength'] = 8.0
        elif current_price < ema20.iloc[-1] < ema50.iloc[-1] < ema200.iloc[-1]:
            trend_info['direction'] = 'BEARISH'
            trend_info['strength'] = 8.0
        elif current_price > ema20.iloc[-1] and ema20.iloc[-1] > ema50.iloc[-1]:
            trend_info['direction'] = 'BULLISH'
            trend_info['strength'] = 6.0
        elif current_price < ema20.iloc[-1] and ema20.iloc[-1] < ema50.iloc[-1]:
            trend_info['direction'] = 'BEARISH'
            trend_info['strength'] = 6.0
            
        return trend_info

    def find_support_resistance(self, df: pd.DataFrame) -> Dict:
        """Find support and resistance levels"""
        levels = {'support': [], 'resistance': []}
        
        # Find swing highs and lows
        for i in range(2, len(df)-2):
            if df['high'].iloc[i] > df['high'].iloc[i-1] and \
               df['high'].iloc[i] > df['high'].iloc[i-2] and \
               df['high'].iloc[i] > df['high'].iloc[i+1] and \
               df['high'].iloc[i] > df['high'].iloc[i+2]:
                levels['resistance'].append(df['high'].iloc[i])
                
            if df['low'].iloc[i] < df['low'].iloc[i-1] and \
               df['low'].iloc[i] < df['low'].iloc[i-2] and \
               df['low'].iloc[i] < df['low'].iloc[i+1] and \
               df['low'].iloc[i] < df['low'].iloc[i+2]:
                levels['support'].append(df['low'].iloc[i])
        
        return levels

    def calculate_momentum(self, df: pd.DataFrame) -> float:
        """Calculate price momentum"""
        # RSI
        rsi = talib.RSI(df['close'], timeperiod=14)
        
        # MACD
        macd, signal, _ = talib.MACD(df['close'])
        
        # Momentum score based on RSI and MACD
        momentum_score = 0.0
        
        # RSI conditions
        if rsi.iloc[-1] > 70:
            momentum_score -= 2.5
        elif rsi.iloc[-1] < 30:
            momentum_score += 2.5
            
        # MACD conditions
        if macd.iloc[-1] > signal.iloc[-1] and macd.iloc[-1] > 0:
            momentum_score += 2.5
        elif macd.iloc[-1] < signal.iloc[-1] and macd.iloc[-1] < 0:
            momentum_score -= 2.5
            
        return momentum_score

    def get_price_action_signal(self, df: pd.DataFrame) -> PriceActionSignal:
        """Get comprehensive price action signal"""
        try:
            signal = PriceActionSignal()
            
            if len(df) < self.trend_period:
                return signal
                
            # 1. Analyze Trend
            trend = self.analyze_trend(df)
            
            # 2. Find Candlestick Patterns
            patterns = self.identify_candlestick_patterns(df)
            pattern_score = sum([1.0 for p in patterns]) * (self.weights['patterns'] / 3)
            
            # 3. Calculate Momentum
            momentum_score = self.calculate_momentum(df)
            
            # 4. Find Support/Resistance
            key_levels = self.find_support_resistance(df)
            sr_score = len(key_levels['support']) + len(key_levels['resistance'])
            sr_score = min(sr_score * 0.5, self.weights['support_res'])
            
            # 5. Calculate Volatility
            atr = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
            volatility_score = min(5.0, (atr.iloc[-1] / atr.mean()) * 2.5)
            
            # Aggregate scores and determine signal
            total_score = (trend['strength'] + pattern_score + 
                         abs(momentum_score) + sr_score + volatility_score)
            
            # Set signal properties
            signal.strength = min(30.0, total_score)
            signal.patterns = [p[0] for p in patterns]
            signal.key_levels = key_levels
            
            # Determine signal direction
            if trend['direction'] == 'BULLISH' and total_score > 15:
                signal.signal_type = "BULLISH"
                signal.entry_price = df['close'].iloc[-1]
                signal.stop_loss = min(df['low'].iloc[-5:])
                signal.take_profit = signal.entry_price + (signal.entry_price - signal.stop_loss) * 1.5
            elif trend['direction'] == 'BEARISH' and total_score > 15:
                signal.signal_type = "BEARISH"
                signal.entry_price = df['close'].iloc[-1]
                signal.stop_loss = max(df['high'].iloc[-5:])
                signal.take_profit = signal.entry_price - (signal.stop_loss - signal.entry_price) * 1.5
                
            signal.metrics = {
                'trend_strength': trend['strength'],
                'pattern_score': pattern_score,
                'momentum': momentum_score,
                'volatility': volatility_score
            }
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Price action analysis error: {e}")
            return PriceActionSignal()

    def __str__(self):
        return "Price Action Analyzer"