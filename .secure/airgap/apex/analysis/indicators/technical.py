"""
Technical Indicators Library
Common technical analysis indicators for trading strategies.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional


def calculate_sma(data: pd.Series, period: int) -> pd.Series:
    """Simple Moving Average"""
    return data.rolling(window=period).mean()


def calculate_ema(data: pd.Series, period: int) -> pd.Series:
    """Exponential Moving Average"""
    return data.ewm(span=period, adjust=False).mean()


def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """
    Relative Strength Index
    
    Args:
        data: Price series
        period: RSI period (default: 14)
        
    Returns:
        RSI values (0-100)
    """
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd(data: pd.Series, 
                   fast: int = 12, 
                   slow: int = 26, 
                   signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Moving Average Convergence Divergence
    
    Args:
        data: Price series
        fast: Fast EMA period
        slow: Slow EMA period
        signal: Signal line period
        
    Returns:
        Tuple of (MACD line, Signal line, Histogram)
    """
    ema_fast = calculate_ema(data, fast)
    ema_slow = calculate_ema(data, slow)
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal)
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram


def calculate_bollinger_bands(data: pd.Series, 
                              period: int = 20, 
                              std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Bollinger Bands
    
    Args:
        data: Price series
        period: Moving average period
        std_dev: Standard deviation multiplier
        
    Returns:
        Tuple of (Upper band, Middle band, Lower band)
    """
    middle = calculate_sma(data, period)
    std = data.rolling(window=period).std()
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    
    return upper, middle, lower


def calculate_atr(high: pd.Series, 
                  low: pd.Series, 
                  close: pd.Series, 
                  period: int = 14) -> pd.Series:
    """
    Average True Range
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: ATR period
        
    Returns:
        ATR values
    """
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    return atr


def calculate_stochastic(high: pd.Series,
                        low: pd.Series,
                        close: pd.Series,
                        k_period: int = 14,
                        d_period: int = 3) -> Tuple[pd.Series, pd.Series]:
    """
    Stochastic Oscillator
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        k_period: %K period
        d_period: %D period
        
    Returns:
        Tuple of (%K, %D)
    """
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    
    k = 100 * (close - lowest_low) / (highest_high - lowest_low)
    d = k.rolling(window=d_period).mean()
    
    return k, d


def calculate_adx(high: pd.Series,
                 low: pd.Series,
                 close: pd.Series,
                 period: int = 14) -> pd.Series:
    """
    Average Directional Index
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: ADX period
        
    Returns:
        ADX values
    """
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


def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """
    On-Balance Volume
    
    Args:
        close: Close prices
        volume: Volume
        
    Returns:
        OBV values
    """
    obv = (np.sign(close.diff()) * volume).cumsum()
    return obv


def calculate_vwap(high: pd.Series,
                  low: pd.Series,
                  close: pd.Series,
                  volume: pd.Series) -> pd.Series:
    """
    Volume Weighted Average Price
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        volume: Volume
        
    Returns:
        VWAP values
    """
    typical_price = (high + low + close) / 3
    vwap = (typical_price * volume).cumsum() / volume.cumsum()
    return vwap


class TechnicalIndicators:
    """
    Helper class to calculate all technical indicators at once.
    """
    
    @staticmethod
    def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        Add all technical indicators to a DataFrame.
        
        Args:
            df: DataFrame with OHLCV columns
            
        Returns:
            DataFrame with added indicator columns
        """
        data = df.copy()
        
        # Moving Averages
        data['sma_20'] = calculate_sma(data['close'], 20)
        data['sma_50'] = calculate_sma(data['close'], 50)
        data['ema_12'] = calculate_ema(data['close'], 12)
        data['ema_26'] = calculate_ema(data['close'], 26)
        
        # RSI
        data['rsi'] = calculate_rsi(data['close'])
        
        # MACD
        data['macd'], data['macd_signal'], data['macd_hist'] = calculate_macd(data['close'])
        
        # Bollinger Bands
        data['bb_upper'], data['bb_middle'], data['bb_lower'] = calculate_bollinger_bands(data['close'])
        
        # ATR
        data['atr'] = calculate_atr(data['high'], data['low'], data['close'])
        
        # Stochastic
        data['stoch_k'], data['stoch_d'] = calculate_stochastic(data['high'], data['low'], data['close'])
        
        # ADX
        data['adx'] = calculate_adx(data['high'], data['low'], data['close'])
        
        # OBV
        data['obv'] = calculate_obv(data['close'], data['volume'])
        
        # VWAP
        data['vwap'] = calculate_vwap(data['high'], data['low'], data['close'], data['volume'])
        
        return data
