"""
Mean Reversion Trading Strategy
Enters positions when price deviates significantly from mean.
"""

import pandas as pd
import numpy as np
from typing import List
from datetime import datetime

from .base import BaseStrategy, Signal, SignalType


class MeanReversionStrategy(BaseStrategy):
    """
    Mean reversion strategy based on RSI and Bollinger Bands.
    
    Configuration:
        - rsi_period: RSI calculation period (default: 14)
        - oversold: RSI oversold threshold (default: 30)
        - overbought: RSI overbought threshold (default: 70)
        - bb_period: Bollinger Bands period (default: 20)
        - bb_std: Bollinger Bands standard deviation (default: 2)
    """
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.rsi_period = config.get('rsi_period', 14)
        self.oversold = config.get('oversold', 30)
        self.overbought = config.get('overbought', 70)
        self.bb_period = config.get('bb_period', 20)
        self.bb_std = config.get('bb_std', 2)
        
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_bollinger_bands(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate Bollinger Bands"""
        df = data.copy()
        df['sma'] = df['close'].rolling(window=self.bb_period).mean()
        df['std'] = df['close'].rolling(window=self.bb_period).std()
        df['upper_band'] = df['sma'] + (df['std'] * self.bb_std)
        df['lower_band'] = df['sma'] - (df['std'] * self.bb_std)
        df['band_width'] = df['upper_band'] - df['lower_band']
        df['percent_b'] = (df['close'] - df['lower_band']) / df['band_width']
        return df
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate RSI and Bollinger Bands.
        """
        df = data.copy()
        
        # Calculate RSI
        df['rsi'] = self.calculate_rsi(df['close'], self.rsi_period)
        
        # Calculate Bollinger Bands
        df = self.calculate_bollinger_bands(df)
        
        # Mean reversion signals
        df['oversold_signal'] = (df['rsi'] < self.oversold) & (df['close'] <= df['lower_band'])
        df['overbought_signal'] = (df['rsi'] > self.overbought) & (df['close'] >= df['upper_band'])
        
        return df
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """
        Generate buy signals when oversold, sell when overbought.
        """
        signals = []
        
        if not self.validate_data(data):
            return signals
            
        df = self.calculate_indicators(data)
        
        if len(df) < 2:
            return signals
            
        current = df.iloc[-1]
        previous = df.iloc[-2]
        symbol = self.symbols[0]
        
        # Check for oversold condition (BUY signal)
        if current['oversold_signal'] and not previous['oversold_signal']:
            confidence = (self.oversold - current['rsi']) / self.oversold * 0.5 + 0.5
            
            signal = Signal(
                type=SignalType.BUY,
                symbol=symbol,
                timestamp=datetime.now(),
                price=current['close'],
                confidence=min(confidence, 0.9),
                metadata={
                    'rsi': current['rsi'],
                    'lower_band': current['lower_band'],
                    'percent_b': current['percent_b'],
                    'strategy': 'mean_reversion'
                }
            )
            signals.append(signal)
            self.signals.append(signal)
        
        # Check for overbought condition (SELL signal)
        elif current['overbought_signal'] and not previous['overbought_signal']:
            confidence = (current['rsi'] - self.overbought) / (100 - self.overbought) * 0.5 + 0.5
            
            signal = Signal(
                type=SignalType.SELL,
                symbol=symbol,
                timestamp=datetime.now(),
                price=current['close'],
                confidence=min(confidence, 0.9),
                metadata={
                    'rsi': current['rsi'],
                    'upper_band': current['upper_band'],
                    'percent_b': current['percent_b'],
                    'strategy': 'mean_reversion'
                }
            )
            signals.append(signal)
            self.signals.append(signal)
        
        return signals
