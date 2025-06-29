"""Liquidity Mapping Module (35 points total)
Maps liquidity pools and potential stop clusters"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, List
from dataclasses import dataclass
from datetime import datetime
import logging

@dataclass
class LiquiditySignal:
    signal_type: str          # BULLISH, BEARISH, NEUTRAL
    strength: float          # 0-35 points
    timestamp: datetime
    sl_cluster_score: float  # 0-15 points
    round_number_score: float # 0-10 points
    swing_score: float       # 0-10 points
    levels: Dict[str, float] # Key liquidity levels
    metrics: Dict           # Additional metrics

class LiquidityAnalyzer:
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Constants for analysis
        self.CLUSTER_RANGE = 5     # Pips range for SL cluster
        self.SWING_PERIOD = 20     # Periods for swing points
        self.MIN_SWING_STRENGTH = 3 # Minimum swing strength

    def analyze_stop_clusters(self, df: pd.DataFrame) -> Tuple[float, str, Dict]:
        """Stop loss cluster estimation (15 points max)
        Identifies:
        - Potential stop loss clusters
        - Order block areas
        - Liquidity pools
        """
        try:
            if len(df) < 50:
                return 0.0, "NEUTRAL", {}

            score = 0.0
            signal = "NEUTRAL"
            metrics = {}

            # Find swing points
            highs = df['high'].rolling(self.SWING_PERIOD, center=True).max()
            lows = df['low'].rolling(self.SWING_PERIOD, center=True).min()
            
            # Identify potential stop clusters
            current_price = df['close'].iloc[-1]
            clusters = []
            
            # Above current price
            for i in range(-20, 0):
                if highs.iloc[i] == df['high'].iloc[i]:
                    clusters.append({
                        'price': highs.iloc[i],
                        'type': 'resistance',
                        'strength': len(df[df['high'] < highs.iloc[i]].index)
                    })
            
            # Below current price
            for i in range(-20, 0):
                if lows.iloc[i] == df['low'].iloc[i]:
                    clusters.append({
                        'price': lows.iloc[i],
                        'type': 'support',
                        'strength': len(df[df['low'] > lows.iloc[i]].index)
                    })

            # Score based on proximity to clusters
            for cluster in clusters:
                distance = abs(current_price - cluster['price'])
                if distance < self.CLUSTER_RANGE:
                    cluster_score = min(5.0, (self.CLUSTER_RANGE - distance))
                    score += cluster_score
                    
                    if cluster['type'] == 'resistance':
                        signal = "BEARISH"
                    else:
                        signal = "BULLISH"

            metrics = {
                'clusters': clusters,
                'current_price': current_price
            }

            return min(15.0, score), signal, metrics

        except Exception as e:
            self.logger.error(f"Stop cluster analysis error: {e}")
            return 0.0, "NEUTRAL", {}

    def analyze_round_numbers(self, df: pd.DataFrame) -> Tuple[float, str, Dict]:
        """Round number magnetism analysis (10 points max)
        Analyzes:
        - Proximity to psychological levels
        - Historical reaction at round numbers
        - Magnetism effect strength
        """
        try:
            if len(df) < 20:
                return 0.0, "NEUTRAL", {}

            score = 0.0
            signal = "NEUTRAL"
            metrics = {}

            current_price = df['close'].iloc[-1]
            
            # Define round number levels
            base_price = int(current_price)
            round_levels = []
            
            # Major levels (100s)
            for i in range(-2, 3):
                round_levels.append({
                    'price': base_price + (i * 100),
                    'type': 'major',
                    'weight': 4.0
                })
            
            # Minor levels (50s)
            for i in range(-4, 5):
                round_levels.append({
                    'price': base_price + (i * 50),
                    'type': 'minor',
                    'weight': 2.0
                })
            
            # Score based on proximity
            for level in round_levels:
                distance = abs(current_price - level['price'])
                if distance < 5:  # Within 5 pips
                    score += level['weight'] * (1 - distance/5)
                    
                    # Check historical reaction
                    reactions = df[abs(df['close'] - level['price']) < 2]
                    if len(reactions) > 0:
                        recent_reaction = reactions.iloc[-1]
                        if recent_reaction['close'] > recent_reaction['open']:
                            signal = "BULLISH"
                        else:
                            signal = "BEARISH"

            metrics = {
                'round_levels': round_levels,
                'current_price': current_price
            }

            return min(10.0, score), signal, metrics

        except Exception as e:
            self.logger.error(f"Round number analysis error: {e}")
            return 0.0, "NEUTRAL", {}

    def analyze_swing_points(self, df: pd.DataFrame) -> Tuple[float, str, Dict]:
        """Swing high/low analysis (10 points max)
        Analyzes:
        - Recent swing point formation
        - Swing point strength
        - Multiple timeframe confluence
        """
        try:
            if len(df) < 50:
                return 0.0, "NEUTRAL", {}

            score = 0.0
            signal = "NEUTRAL"
            metrics = {}

            # Find recent swing points
            window = self.SWING_PERIOD
            highs = df['high'].rolling(window=window, center=True).max()
            lows = df['low'].rolling(window=window, center=True).min()
            
            current_price = df['close'].iloc[-1]
            
            # Analyze recent swings
            recent_swings = []
            
            # High swings
            for i in range(-10, 0):
                if df['high'].iloc[i] == highs.iloc[i]:
                    strength = (df['high'].iloc[i] - df['low'].iloc[i:].min()) / df['high'].iloc[i]
                    if strength > self.MIN_SWING_STRENGTH / 100:  # Convert to percentage
                        recent_swings.append({
                            'price': df['high'].iloc[i],
                            'type': 'high',
                            'strength': strength
                        })
            
            # Low swings
            for i in range(-10, 0):
                if df['low'].iloc[i] == lows.iloc[i]:
                    strength = (df['high'].iloc[i:].max() - df['low'].iloc[i]) / df['low'].iloc[i]
                    if strength > self.MIN_SWING_STRENGTH / 100:
                        recent_swings.append({
                            'price': df['low'].iloc[i],
                            'type': 'low',
                            'strength': strength
                        })

            # Score based on swing points
            for swing in recent_swings:
                distance = abs(current_price - swing['price'])
                if distance < 10:  # Within 10 pips
                    score += swing['strength'] * 10
                    
                    if swing['type'] == 'high' and current_price < swing['price']:
                        signal = "BEARISH"
                    elif swing['type'] == 'low' and current_price > swing['price']:
                        signal = "BULLISH"

            metrics = {
                'swings': recent_swings,
                'current_price': current_price
            }

            return min(10.0, score), signal, metrics

        except Exception as e:
            self.logger.error(f"Swing point analysis error: {e}")
            return 0.0, "NEUTRAL", {}

    def get_liquidity_signal(self, df: pd.DataFrame) -> LiquiditySignal:
        """Aggregate all liquidity analysis components"""
        try:
            # Get component scores
            sl_score, sl_signal, sl_metrics = self.analyze_stop_clusters(df)
            round_score, round_signal, round_metrics = self.analyze_round_numbers(df)
            swing_score, swing_signal, swing_metrics = self.analyze_swing_points(df)

            # Calculate total score
            total_score = sl_score + round_score + swing_score

            # Determine final signal
            signals = [sl_signal, round_signal, swing_signal]
            bullish_count = signals.count("BULLISH")
            bearish_count = signals.count("BEARISH")

            final_signal = "NEUTRAL"
            if bullish_count > bearish_count:
                final_signal = "BULLISH"
            elif bearish_count > bullish_count:
                final_signal = "BEARISH"

            # Combine metrics
            all_metrics = {
                **sl_metrics,
                **round_metrics,
                **swing_metrics,
                'component_signals': {
                    'stop_clusters': sl_signal,
                    'round_numbers': round_signal,
                    'swing_points': swing_signal
                }
            }

            # Key liquidity levels
            levels = {}
            if 'clusters' in sl_metrics:
                for cluster in sl_metrics['clusters']:
                    levels[f"cluster_{cluster['type']}"] = cluster['price']
            if 'round_levels' in round_metrics:
                for level in round_metrics['round_levels']:
                    if abs(level['price'] - df['close'].iloc[-1]) < 10:
                        levels[f"round_{level['type']}"] = level['price']

            return LiquiditySignal(
                signal_type=final_signal,
                strength=total_score,
                timestamp=datetime.utcnow(),
                sl_cluster_score=sl_score,
                round_number_score=round_score,
                swing_score=swing_score,
                levels=levels,
                metrics=all_metrics
            )

        except Exception as e:
            self.logger.error(f"Liquidity signal error: {e}")
            return LiquiditySignal(
                signal_type="NEUTRAL",
                strength=0.0,
                timestamp=datetime.utcnow(),
                sl_cluster_score=0.0,
                round_number_score=0.0,
                swing_score=0.0,
                levels={},
                metrics={}
            )