"""
Multi-Timeframe Analysis Strategy
Analyzes multiple timeframes for confluence.
"""

from typing import List, Dict
import pandas as pd
import numpy as np
from datetime import datetime

from .base import BaseStrategy, Signal, SignalType


class MultiTimeframeStrategy(BaseStrategy):
    """
    Multi-timeframe analysis strategy.
    
    Only enters when higher timeframe trend aligns with lower timeframe signal.
    
    Timeframes:
    - Higher: 4H (trend direction)
    - Medium: 1H (setup)
    - Lower: 15m (entry trigger)
    """
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.timeframes = config.get('timeframes', ['4h', '1h', '15m'])
        self.ema_period = config.get('ema_period', 20)
        self.rsi_period = config.get('rsi_period', 14)
        self.rsi_oversold = config.get('rsi_oversold', 30)
        self.rsi_overbought = config.get('rsi_overbought', 70)
        
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate indicators for current timeframe"""
        # EMA for trend
        data['ema'] = data['close'].ewm(span=self.ema_period, adjust=False).mean()
        data['trend_up'] = data['close'] > data['ema']
        
        # RSI for momentum
        data['rsi'] = self._calculate_rsi(data['close'], self.rsi_period)
        
        # MACD for confirmation
        data['macd'], data['macd_signal'], data['macd_hist'] = self._calculate_macd(data['close'])
        
        return data
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """
        Generate signals based on multi-timeframe confluence.
        
        This is a simplified version - in production, you'd fetch data
        from all timeframes and compare them.
        """
        signals = []
        
        if len(data) < 3:
            return signals
        
        current = data.iloc[-1]
        previous = data.iloc[-2]
        
        for symbol in self.symbols:
            # Bullish confluence: uptrend + RSI oversold bounce + MACD bullish
            if (current['trend_up'] and
                current['rsi'] > self.rsi_oversold and
                previous['rsi'] <= self.rsi_oversold and
                current['macd_hist'] > 0):
                
                signals.append(Signal(
                    type=SignalType.BUY,
                    symbol=symbol,
                    timestamp=datetime.now(),
                    price=current['close'],
                    confidence=self._calculate_confidence(current, 'bullish'),
                    metadata={
                        'strategy': 'multi_timeframe',
                        'trend': 'up',
                        'rsi': current['rsi'],
                        'macd_hist': current['macd_hist'],
                        'confluence_score': 3  # All 3 conditions met
                    }
                ))
            
            # Bearish confluence: downtrend + RSI overbought rejection + MACD bearish
            elif (not current['trend_up'] and
                  current['rsi'] < self.rsi_overbought and
                  previous['rsi'] >= self.rsi_overbought and
                  current['macd_hist'] < 0):
                
                signals.append(Signal(
                    type=SignalType.SELL,
                    symbol=symbol,
                    timestamp=datetime.now(),
                    price=current['close'],
                    confidence=self._calculate_confidence(current, 'bearish'),
                    metadata={
                        'strategy': 'multi_timeframe',
                        'trend': 'down',
                        'rsi': current['rsi'],
                        'macd_hist': current['macd_hist'],
                        'confluence_score': 3
                    }
                ))
        
        return signals
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, prices: pd.Series, 
                       fast: int = 12, slow: int = 26, signal: int = 9) -> tuple:
        """Calculate MACD"""
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    def _calculate_confidence(self, data: pd.Series, direction: str) -> float:
        """Calculate signal confidence based on indicator strength"""
        confidence = 0.5
        
        # RSI extreme adds confidence
        if direction == 'bullish':
            if data['rsi'] < 35:
                confidence += 0.2
            if data['macd_hist'] > 0:
                confidence += 0.15
            if data['close'] > data['ema'] * 1.01:  # Price well above EMA
                confidence += 0.15
        else:  # bearish
            if data['rsi'] > 65:
                confidence += 0.2
            if data['macd_hist'] < 0:
                confidence += 0.15
            if data['close'] < data['ema'] * 0.99:
                confidence += 0.15
        
        return min(confidence, 1.0)
    
    def __str__(self):
        return f"MultiTimeframeStrategy({','.join(self.timeframes)})"
