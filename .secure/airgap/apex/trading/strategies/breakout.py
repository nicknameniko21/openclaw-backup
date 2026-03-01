"""
Breakout Trading Strategy
Enters positions when price breaks above resistance or below support.
"""

import pandas as pd
import numpy as np
from typing import List
from datetime import datetime

from .base import BaseStrategy, Signal, SignalType


class BreakoutStrategy(BaseStrategy):
    """
    Breakout strategy based on price breaking through support/resistance levels.
    
    Configuration:
        - lookback: Number of periods to calculate support/resistance (default: 20)
        - volume_confirm: Require volume confirmation (default: True)
        - min_breakout_percent: Minimum breakout percentage (default: 0.01)
    """
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.lookback = config.get('lookback', 20)
        self.volume_confirm = config.get('volume_confirm', True)
        self.min_breakout_percent = config.get('min_breakout_percent', 0.01)
        
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate support, resistance, and volume indicators.
        """
        df = data.copy()
        
        # Calculate support and resistance
        df['resistance'] = df['high'].rolling(window=self.lookback).max()
        df['support'] = df['low'].rolling(window=self.lookback).min()
        
        # Calculate average volume
        df['avg_volume'] = df['volume'].rolling(window=self.lookback).mean()
        
        # Calculate breakout thresholds
        df['resistance_break'] = df['close'] > df['resistance'].shift(1) * (1 + self.min_breakout_percent)
        df['support_break'] = df['close'] < df['support'].shift(1) * (1 - self.min_breakout_percent)
        
        # Volume confirmation
        df['volume_confirm'] = df['volume'] > df['avg_volume'] * 1.2
        
        return df
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """
        Generate buy signals on resistance breakout, sell on support breakout.
        """
        signals = []
        
        if not self.validate_data(data):
            return signals
            
        df = self.calculate_indicators(data)
        
        # Get the last row for signal generation
        if len(df) < 2:
            return signals
            
        current = df.iloc[-1]
        previous = df.iloc[-2]
        symbol = self.symbols[0]  # Use first symbol for now
        
        # Check for resistance breakout (BUY signal)
        if current['resistance_break']:
            volume_ok = not self.volume_confirm or current['volume_confirm']
            
            if volume_ok:
                signal = Signal(
                    type=SignalType.BUY,
                    symbol=symbol,
                    timestamp=datetime.now(),
                    price=current['close'],
                    confidence=0.7,
                    metadata={
                        'resistance': current['resistance'],
                        'volume_ratio': current['volume'] / current['avg_volume'],
                        'strategy': 'breakout'
                    }
                )
                signals.append(signal)
                self.signals.append(signal)
        
        # Check for support breakdown (SELL signal)
        elif current['support_break']:
            volume_ok = not self.volume_confirm or current['volume_confirm']
            
            if volume_ok:
                signal = Signal(
                    type=SignalType.SELL,
                    symbol=symbol,
                    timestamp=datetime.now(),
                    price=current['close'],
                    confidence=0.7,
                    metadata={
                        'support': current['support'],
                        'volume_ratio': current['volume'] / current['avg_volume'],
                        'strategy': 'breakout'
                    }
                )
                signals.append(signal)
                self.signals.append(signal)
        
        return signals
