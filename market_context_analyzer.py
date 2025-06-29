"""Market Context Enhancement Module (25 points max)"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
from dataclasses import dataclass
from datetime import datetime, time
import logging

@dataclass
class MarketContextSignal:
    signal_type: str
    strength: float  # 0-25 points
    timestamp: datetime
    session_info: Dict
    details: Dict

class MarketContextAnalyzer:
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Session times (UTC)
        self.sessions = {
            'asian': {
                'start': time(1, 0),  # 08:00 +7UTC ( indonesia )
                'end': time(5, 0)      # 11:00 +7UTC ( indonesia )
            },
            'london': {
                'start': time(6, 0),   # 08:00 +7UTC ( indonesia )
                'end': time(9, 0)     # 16:00 +7UTC ( indonesia )
            },
            'new_york': {
                'start': time(11, 0),  # 13:00 +7UTC ( indonesia )
                'end': time(22, 0)     # 22:00 +7UTC ( indonesia )
            }
        }
    
    def analyze_session_timing(self, current_time: datetime) -> Tuple[float, str, Dict]:
        """Analyze session timing (10 points max)"""
        try:
            score = 0
            signal = "NEUTRAL"
            session_info = {}
            
            current_utc = current_time.time()
            
            # Determine current session(s)
            active_sessions = []
            for session, times in self.sessions.items():
                if times['start'] <= current_utc <= times['end']:
                    active_sessions.append(session)
            
            session_info['active_sessions'] = active_sessions
            
            # Score based on session activity
            if len(active_sessions) > 1:  # Session overlap
                score += 5  # Higher volatility expected
                if 'london' in active_sessions and 'new_york' in active_sessions:
                    score += 3  # Most active overlap
            elif len(active_sessions) == 1:
                if active_sessions[0] == 'asian':
                    score += 3  # Usually range-bound
                else:
                    score += 4  # Active session
            
            # Check for session transitions
            for session, times in self.sessions.items():
                mins_to_start = ((times['start'].hour * 60 + times['start'].minute) - 
                               (current_utc.hour * 60 + current_utc.minute)) % 1440
                if mins_to_start <= 30:  # Within 30 mins of session start
                    score += 2
            
            return min(10.0, score), signal, session_info
            
        except Exception as e:
            self.logger.error(f"Session timing analysis error: {e}")
            return 0.0, "NEUTRAL", {}
    
    def analyze_high_low_proximity(self, df: pd.DataFrame) -> Tuple[float, str, Dict]:
        """Analyze previous day H/L proximity (10 points max)"""
        try:
            if len(df) < 1440:  # Need full day of M1 data
                return 0.0, "NEUTRAL", {}
            
            score = 0
            signal = "NEUTRAL"
            metrics = {}
            
            # Get previous day's range
            prev_day = df.iloc[-1440:-1]
            prev_high = prev_day['high'].max()
            prev_low = prev_day['low'].min()
            prev_range = prev_high - prev_low
            
            current_price = df['close'].iloc[-1]
            
            # Calculate distances
            dist_to_high = abs(current_price - prev_high)
            dist_to_low = abs(current_price - prev_low)
            
            metrics.update({
                'prev_day_high': prev_high,
                'prev_day_low': prev_low,
                'dist_to_high': dist_to_high,
                'dist_to_low': dist_to_low
            })
            
            # Score based on proximity
            if dist_to_high < prev_range * 0.1:  # Within 10% of high
                score += 5
                signal = "BEARISH"  # Potential resistance
            elif dist_to_low < prev_range * 0.1:  # Within 10% of low
                score += 5
                signal = "BULLISH"  # Potential support
            
            # Score based on range position
            range_position = (current_price - prev_low) / prev_range
            metrics['range_position'] = range_position
            
            if 0.4 <= range_position <= 0.6:  # Mid-range
                score += 5
            
            return min(10.0, score), signal, metrics
            
        except Exception as e:
            self.logger.error(f"H/L proximity analysis error: {e}")
            return 0.0, "NEUTRAL", {}
    
    def analyze_asian_range_breakout(self, df: pd.DataFrame) -> Tuple[float, str, Dict]:
        """Analyze Asian range breakout validation (5 points max)"""
        try:
            if len(df) < 600:  # Need at least 10 hours of M1 data
                return 0.0, "NEUTRAL", {}
            
            score = 0
            signal = "NEUTRAL"
            metrics = {}
            
            # Define Asian session (last Asian session)
            asian_session = df.iloc[-600:-240]  # 22:00-08:00 UTC
            asian_high = asian_session['high'].max()
            asian_low = asian_session['low'].min()
            asian_range = asian_high - asian_low
            
            current_price = df['close'].iloc[-1]
            
            metrics.update({
                'asian_high': asian_high,
                'asian_low': asian_low,
                'asian_range': asian_range
            })
            
            # Check for breakout
            if current_price > asian_high:
                breakout_size = (current_price - asian_high) / asian_range
                if breakout_size > 0.5:  # Strong breakout
                    score += 3
                    signal = "BULLISH"
                score += 2
                signal = "BULLISH"
            elif current_price < asian_low:
                breakout_size = (asian_low - current_price) / asian_range
                if breakout_size > 0.5:  # Strong breakout
                    score += 3
                    signal = "BEARISH"
                score += 2
                signal = "BEARISH"
            
            return min(5.0, score), signal, metrics
            
        except Exception as e:
            self.logger.error(f"Asian range breakout analysis error: {e}")
            return 0.0, "NEUTRAL", {}
    
    def get_market_context_signal(self, df: pd.DataFrame) -> MarketContextSignal:
        """Get complete market context analysis"""
        try:
            current_time = datetime.utcnow()
            
            # Get individual scores
            session_score, session_signal, session_info = self.analyze_session_timing(current_time)
            hl_score, hl_signal, hl_metrics = self.analyze_high_low_proximity(df)
            asian_score, asian_signal, asian_metrics = self.analyze_asian_range_breakout(df)
            
            # Calculate total score
            total_score = sum([session_score, hl_score, asian_score])
            
            # Determine final signal
            signals = [session_signal, hl_signal, asian_signal]
            bullish_count = signals.count("BULLISH")
            bearish_count = signals.count("BEARISH")
            
            if bullish_count > bearish_count:
                final_signal = "BULLISH"
            elif bearish_count > bullish_count:
                final_signal = "BEARISH"
            else:
                final_signal = "NEUTRAL"
            
            details = {
                'session_timing': session_score,
                'hl_proximity': hl_score,
                'asian_breakout': asian_score,
                'signals': {
                    'session': session_signal,
                    'hl': hl_signal,
                    'asian': asian_signal
                }
            }
            
            # Combine all metrics
            session_info.update(hl_metrics)
            session_info.update(asian_metrics)
            
            return MarketContextSignal(
                signal_type=final_signal,
                strength=total_score,
                timestamp=current_time,
                session_info=session_info,
                details=details
            )
            
        except Exception as e:
            self.logger.error(f"Market context analysis error: {e}")
            return MarketContextSignal(
                signal_type="NEUTRAL",
                strength=0.0,
                timestamp=datetime.utcnow(),
                session_info={},
                details={}
            )