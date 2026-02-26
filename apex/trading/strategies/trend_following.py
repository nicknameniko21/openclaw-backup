"""
Trend Following Strategy
Follows established trends using moving averages and ADX.
"""

from typing import List, Dict
import pandas as pd
import numpy as np
from datetime import datetime

from .base import BaseStrategy, Signal, SignalType


class TrendFollowingStrategy(BaseStrategy):
    """
    Trend following strategy using moving averages and ADX.
    
    Entry Conditions:
    - LONG: Price > EMA50 > EMA200, ADX > 25, price pulls back to EMA50
    - SHORT: Price < EMA50 < EMA200, ADX > 25, price rallies to EMA50
    
    Exit Conditions:
    - Trend reversal (price crosses opposite EMA)
    - ADX drops below 20 (trend weakening)
    """
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.fast_ema_period = config.get('fast_ema_period', 50)
        self.slow_ema_period = config.get('slow_ema_period', 200)
        self.adx_threshold = config.get('adx_threshold', 25)
        self.adx_exit_threshold = config.get('adx_exit_threshold', 20)
        self.pullback_threshold = config.get('pullback_threshold', 0.02)
        
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate EMAs and ADX for trend detection"""
        # Calculate EMAs
        data['ema_fast'] = data['close'].ewm(span=self.fast_ema_period, adjust=False).mean()
        data['ema_slow'] = data['close'].ewm(span=self.slow_ema_period, adjust=False).mean()
        
        # Calculate ADX
        data['adx'] = self._calculate_adx(data, period=14)
        
        # Trend direction
        data['trend_up'] = (data['close'] > data['ema_fast']) & (data['ema_fast'] > data['ema_slow'])
        data['trend_down'] = (data['close'] < data['ema_fast']) & (data['ema_fast'] < data['ema_slow'])
        
        # Pullback/rally detection
        data['distance_from_fast_ema'] = abs(data['close'] - data['ema_fast']) / data['ema_fast']
        data['near_fast_ema'] = data['distance_from_fast_ema'] < self.pullback_threshold
        
        return data
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """Generate trend following signals"""
        signals = []
        
        if len(data) < 2:
            return signals
        
        current = data.iloc[-1]
        previous = data.iloc[-2]
        
        for symbol in self.symbols:
            # LONG signal: Strong uptrend + pullback to EMA50
            if (current['trend_up'] and 
                current['adx'] > self.adx_threshold and
                current['near_fast_ema'] and
                not previous['near_fast_ema']):
                
                signals.append(Signal(
                    type=SignalType.BUY,
                    symbol=symbol,
                    timestamp=datetime.now(),
                    price=current['close'],
                    confidence=min(current['adx'] / 50, 1.0),  # Higher ADX = higher confidence
                    metadata={
                        'strategy': 'trend_following',
                        'trend': 'up',
                        'adx': current['adx'],
                        'ema_fast': current['ema_fast'],
                        'ema_slow': current['ema_slow']
                    }
                ))
            
            # SHORT signal: Strong downtrend + rally to EMA50
            elif (current['trend_down'] and 
                  current['adx'] > self.adx_threshold and
                  current['near_fast_ema'] and
                  not previous['near_fast_ema']):
                
                signals.append(Signal(
                    type=SignalType.SELL,
                    symbol=symbol,
                    timestamp=datetime.now(),
                    price=current['close'],
                    confidence=min(current['adx'] / 50, 1.0),
                    metadata={
                        'strategy': 'trend_following',
                        'trend': 'down',
                        'adx': current['adx'],
                        'ema_fast': current['ema_fast'],
                        'ema_slow': current['ema_slow']
                    }
                ))
            
            # Check for exit signals on existing positions
            position = self.get_position(symbol)
            if position:
                # Exit on trend reversal
                if position.side == 'long' and not current['trend_up']:
                    signals.append(Signal(
                        type=SignalType.SELL,
                        symbol=symbol,
                        timestamp=datetime.now(),
                        price=current['close'],
                        confidence=0.8,
                        metadata={'reason': 'trend_reversal', 'strategy': 'trend_following'}
                    ))
                elif position.side == 'short' and not current['trend_down']:
                    signals.append(Signal(
                        type=SignalType.BUY,
                        symbol=symbol,
                        timestamp=datetime.now(),
                        price=current['close'],
                        confidence=0.8,
                        metadata={'reason': 'trend_reversal', 'strategy': 'trend_following'}
                    ))
                
                # Exit on weak trend
                if current['adx'] < self.adx_exit_threshold:
                    exit_type = SignalType.SELL if position.side == 'long' else SignalType.BUY
                    signals.append(Signal(
                        type=exit_type,
                        symbol=symbol,
                        timestamp=datetime.now(),
                        price=current['close'],
                        confidence=0.6,
                        metadata={'reason': 'weak_trend', 'adx': current['adx']}
                    ))
        
        return signals
    
    def _calculate_adx(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average Directional Index"""
        high = data['high']
        low = data['low']
        close = data['close']
        
        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Plus Directional Movement (+DM)
        plus_dm = high.diff()
        plus_dm = plus_dm.where((plus_dm > 0) & (plus_dm > -low.diff()), 0)
        
        # Minus Directional Movement (-DM)
        minus_dm = -low.diff()
        minus_dm = minus_dm.where((minus_dm > 0) & (minus_dm > high.diff()), 0)
        
        # Smooth TR, +DM, -DM
        atr = tr.rolling(window=period).mean()
        plus_di = 100 * plus_dm.rolling(window=period).mean() / atr
        minus_di = 100 * minus_dm.rolling(window=period).mean() / atr
        
        # Directional Movement Index (DX)
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        
        # Average Directional Index (ADX)
        adx = dx.rolling(window=period).mean()
        
        return adx
    
    def __str__(self):
        return f"TrendFollowingStrategy(EMA{self.fast_ema_period}/EMA{self.slow_ema_period}, ADX>{self.adx_threshold})"
