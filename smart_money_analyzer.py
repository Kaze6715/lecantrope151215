"""Smart Money Indicators Module (30 points total)
Focuses on institutional trading patterns and volume analysis"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, List
from dataclasses import dataclass
from datetime import datetime
import logging

@dataclass
class SmartMoneySignal:
    signal_type: str           # BULLISH, BEARISH, NEUTRAL
    strength: float           # 0-30 points
    timestamp: datetime
    institutional_score: float # 0-15 points
    volume_score: float      # 0-10 points
    pressure_score: float    # 0-5 points
    levels: Dict[str, float]  # Key price levels
    metrics: Dict            # Additional metrics

class SmartMoneyAnalyzer:
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Constants for analysis
        self.INST_CANDLE_MIN_SIZE = 20  # Minimum pips for institutional candle
        self.VOL_PROFILE_BINS = 20      # Number of bins for volume profile
        self.PRESSURE_THRESHOLD = 0.65   # Threshold for buy/sell pressure

    def find_institutional_candles(self, df: pd.DataFrame) -> Tuple[float, str, Dict]:
        """Analyze institutional candle patterns (15 points max)
        Looks for:
        - Large engulfing candles (order blocks)
        - High volume relative to average
        - Clean rejection from levels
        """
        try:
            if len(df) < 20:
                return 0.0, "NEUTRAL", {}

            score = 0.0
            signal = "NEUTRAL"
            metrics = {}

            # Calculate candle sizes and averages
            body_sizes = abs(df['close'] - df['open'])
            shadows = df['high'] - df['low']
            avg_body = body_sizes.rolling(20).mean()
            avg_shadow = shadows.rolling(20).mean()
            volume = df['tick_volume']
            avg_volume = volume.rolling(20).mean()

            # Look for institutional candles in last 3 bars
            for i in range(-3, 0):
                candle = df.iloc[i]
                
                # 1. Large body relative to average (4 points)
                if body_sizes.iloc[i] > 2 * avg_body.iloc[i]:
                    score += 4
                    
                # 2. High volume confirmation (3 points)
                if volume.iloc[i] > 1.5 * avg_volume.iloc[i]:
                    score += 3
                    
                # 3. Clean rejection with small shadow (3 points)
                if shadows.iloc[i] < 1.2 * body_sizes.iloc[i]:
                    score += 3
                    
                # Determine direction
                if score > 0:
                    if candle['close'] > candle['open']:
                        signal = "BULLISH"
                    else:
                        signal = "BEARISH"

            # Record metrics
            metrics = {
                'last_body_size': float(body_sizes.iloc[-1]),
                'avg_body_size': float(avg_body.iloc[-1]),
                'last_volume': float(volume.iloc[-1]),
                'avg_volume': float(avg_volume.iloc[-1])
            }

            return min(15.0, score), signal, metrics

        except Exception as e:
            self.logger.error(f"Institutional candle analysis error: {e}")
            return 0.0, "NEUTRAL", {}

    def analyze_volume_profile(self, df: pd.DataFrame) -> Tuple[float, str, Dict]:
        """Volume profile analysis (10 points max)
        Analyzes:
        - Volume nodes (high volume areas)
        - Price acceptance/rejection
        - Volume delta at key levels
        """
        try:
            if len(df) < 50:
                return 0.0, "NEUTRAL", {}

            score = 0.0
            signal = "NEUTRAL"
            metrics = {}

            # Create volume profile
            price_range = df['high'].max() - df['low'].min()
            bin_size = price_range / self.VOL_PROFILE_BINS
            
            df['price_bin'] = pd.cut(df['close'], 
                                   bins=self.VOL_PROFILE_BINS,
                                   labels=False)
            
            volume_profile = df.groupby('price_bin')['tick_volume'].sum()
            
            # Find high volume nodes
            mean_vol = volume_profile.mean()
            std_vol = volume_profile.std()
            
            high_vol_nodes = volume_profile[volume_profile > mean_vol + std_vol]
            current_bin = pd.cut([df['close'].iloc[-1]], 
                               bins=self.VOL_PROFILE_BINS,
                               labels=False)[0]

            # Score based on current price position
            if current_bin in high_vol_nodes.index:
                score += 5  # At high volume node
                
                # Check if accepting or rejecting
                recent_close = df['close'].iloc[-1]
                recent_open = df['open'].iloc[-1]
                
                if recent_close > recent_open:  # Bullish at node
                    score += 5
                    signal = "BULLISH"
                elif recent_close < recent_open:  # Bearish at node
                    score += 5
                    signal = "BEARISH"

            metrics = {
                'high_vol_nodes': list(high_vol_nodes.index),
                'current_bin': int(current_bin),
                'mean_volume': float(mean_vol)
            }

            return min(10.0, score), signal, metrics

        except Exception as e:
            self.logger.error(f"Volume profile analysis error: {e}")
            return 0.0, "NEUTRAL", {}

    def analyze_pressure(self, df: pd.DataFrame) -> Tuple[float, str, Dict]:
        """Buy/sell pressure estimation (5 points max)
        Analyzes:
        - Delta volume (buy vs sell volume)
        - Price momentum with volume
        - Cumulative volume delta
        """
        try:
            if len(df) < 20:
                return 0.0, "NEUTRAL", {}

            score = 0.0
            signal = "NEUTRAL"
            metrics = {}

            # Calculate buying vs selling pressure
            buying_volume = df[df['close'] > df['open']]['tick_volume'].sum()
            selling_volume = df[df['close'] < df['open']]['tick_volume'].sum()
            total_volume = buying_volume + selling_volume

            if total_volume > 0:
                buy_ratio = buying_volume / total_volume
                
                # Strong buying pressure
                if buy_ratio > self.PRESSURE_THRESHOLD:
                    score += 5
                    signal = "BULLISH"
                # Strong selling pressure
                elif buy_ratio < (1 - self.PRESSURE_THRESHOLD):
                    score += 5
                    signal = "BEARISH"
                
                metrics = {
                    'buy_ratio': float(buy_ratio),
                    'total_volume': float(total_volume)
                }

            return min(5.0, score), signal, metrics

        except Exception as e:
            self.logger.error(f"Pressure analysis error: {e}")
            return 0.0, "NEUTRAL", {}

    def get_smart_money_signal(self, df: pd.DataFrame) -> SmartMoneySignal:
        """Aggregate all smart money analysis components"""
        try:
            # Get component scores
            inst_score, inst_signal, inst_metrics = self.find_institutional_candles(df)
            vol_score, vol_signal, vol_metrics = self.analyze_volume_profile(df)
            pressure_score, pressure_signal, pressure_metrics = self.analyze_pressure(df)

            # Calculate total score
            total_score = inst_score + vol_score + pressure_score

            # Determine final signal
            signals = [inst_signal, vol_signal, pressure_signal]
            bullish_count = signals.count("BULLISH")
            bearish_count = signals.count("BEARISH")

            final_signal = "NEUTRAL"
            if bullish_count > bearish_count:
                final_signal = "BULLISH"
            elif bearish_count > bullish_count:
                final_signal = "BEARISH"

            # Combine metrics
            all_metrics = {
                **inst_metrics,
                **vol_metrics,
                **pressure_metrics,
                'component_signals': {
                    'institutional': inst_signal,
                    'volume': vol_signal,
                    'pressure': pressure_signal
                }
            }

            # Key price levels
            levels = {
                'high_volume_level': vol_metrics.get('high_vol_nodes', [None])[0]
            }

            return SmartMoneySignal(
                signal_type=final_signal,
                strength=total_score,
                timestamp=datetime.utcnow(),
                institutional_score=inst_score,
                volume_score=vol_score,
                pressure_score=pressure_score,
                levels=levels,
                metrics=all_metrics
            )

        except Exception as e:
            self.logger.error(f"Smart money signal error: {e}")
            return SmartMoneySignal(
                signal_type="NEUTRAL",
                strength=0.0,
                timestamp=datetime.utcnow(),
                institutional_score=0.0,
                volume_score=0.0,
                pressure_score=0.0,
                levels={},
                metrics={}
            )