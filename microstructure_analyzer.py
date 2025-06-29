"""Market Microstructure Analysis Module"""
import pandas as pd
from typing import Dict
from datetime import datetime, timezone
import logging
datetime.now(timezone.utc)
class MicrostructureSignal:
    def __init__(self):
        self.signal_type = "NEUTRAL"
        self.strength = 0.0  # 0-25 points
        self.timestamp = datetime.now(timezone.utc)
        self.levels = {}
        self.metrics = {}

class MicrostructureAnalyzer:
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)

    def get_microstructure_signal(self, data_handler, df: pd.DataFrame) -> MicrostructureSignal:
        """Analyze market microstructure"""
        try:
            signal = MicrostructureSignal()
            
            if len(df) < 20:
                return signal

            # Analyze bid-ask spread and tick data
            if 'spread' in df.columns:
                avg_spread = df['spread'].mean()
                current_spread = df['spread'].iloc[-1]
                
                if current_spread < avg_spread * 0.8:  # Tight spread
                    if df['close'].iloc[-1] > df['open'].iloc[-1]:
                        signal.signal_type = "BULLISH"
                        signal.strength = 18.0
                    elif df['close'].iloc[-1] < df['open'].iloc[-1]:
                        signal.signal_type = "BEARISH"
                        signal.strength = 18.0
            
            return signal

        except Exception as e:
            self.logger.error(f"Microstructure analysis error: {e}")
            return MicrostructureSignal()