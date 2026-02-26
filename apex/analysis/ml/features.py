"""
Feature Engineering for Machine Learning
Creates features from OHLCV data for ML models.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class FeatureConfig:
    """Configuration for feature engineering"""
    # Price features
    include_returns: bool = True
    return_periods: List[int] = None
    
    # Moving average features
    include_ma_ratios: bool = True
    ma_periods: List[int] = None
    
    # Volatility features
    include_volatility: bool = True
    volatility_periods: List[int] = None
    
    # Technical indicator features
    include_rsi: bool = True
    include_macd: bool = True
    include_bollinger: bool = True
    include_atr: bool = True
    
    # Volume features
    include_volume: bool = True
    volume_periods: List[int] = None
    
    # Pattern features
    include_candlestick: bool = True
    
    def __post_init__(self):
        if self.return_periods is None:
            self.return_periods = [1, 3, 5, 10, 20]
        if self.ma_periods is None:
            self.ma_periods = [5, 10, 20, 50, 200]
        if self.volatility_periods is None:
            self.volatility_periods = [5, 10, 20]
        if self.volume_periods is None:
            self.volume_periods = [5, 10, 20]


class FeatureEngineer:
    """
    Creates machine learning features from price data.
    """
    
    def __init__(self, config: Optional[FeatureConfig] = None):
        self.config = config or FeatureConfig()
        self.feature_names: List[str] = []
    
    def create_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Create all configured features from price data.
        
        Args:
            data: DataFrame with OHLCV columns
            
        Returns:
            DataFrame with added feature columns
        """
        df = data.copy()
        
        # Price-based features
        if self.config.include_returns:
            df = self._add_return_features(df)
        
        # Moving average features
        if self.config.include_ma_ratios:
            df = self._add_ma_features(df)
        
        # Volatility features
        if self.config.include_volatility:
            df = self._add_volatility_features(df)
        
        # Technical indicators
        if self.config.include_rsi:
            df = self._add_rsi_features(df)
        
        if self.config.include_macd:
            df = self._add_macd_features(df)
        
        if self.config.include_bollinger:
            df = self._add_bollinger_features(df)
        
        if self.config.include_atr:
            df = self._add_atr_features(df)
        
        # Volume features
        if self.config.include_volume:
            df = self._add_volume_features(df)
        
        # Candlestick patterns
        if self.config.include_candlestick:
            df = self._add_candlestick_features(df)
        
        # Store feature names (exclude OHLCV and target columns)
        self.feature_names = [col for col in df.columns 
                             if col not in ['open', 'high', 'low', 'close', 'volume', 'timestamp']]
        
        return df
    
    def _add_return_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add return features for different periods"""
        for period in self.config.return_periods:
            df[f'return_{period}d'] = df['close'].pct_change(period)
            df[f'log_return_{period}d'] = np.log(df['close'] / df['close'].shift(period))
        
        # Price momentum (rate of change)
        df['momentum'] = df['close'] - df['close'].shift(10)
        df['momentum_pct'] = df['momentum'] / df['close'].shift(10)
        
        return df
    
    def _add_ma_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add moving average ratio features"""
        for period in self.config.ma_periods:
            df[f'sma_{period}'] = df['close'].rolling(window=period).mean()
            df[f'ema_{period}'] = df['close'].ewm(span=period, adjust=False).mean()
            
            # Price relative to MA
            df[f'price_to_sma_{period}'] = df['close'] / df[f'sma_{period}']
            df[f'price_to_ema_{period}'] = df['close'] / df[f'ema_{period}']
        
        # MA crossovers
        if 50 in self.config.ma_periods and 200 in self.config.ma_periods:
            df['golden_cross'] = (df['sma_50'] > df['sma_200']).astype(int)
            df['sma_ratio'] = df['sma_50'] / df['sma_200']
        
        return df
    
    def _add_volatility_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volatility features"""
        for period in self.config.volatility_periods:
            # Standard deviation of returns
            df[f'volatility_{period}d'] = df['close'].pct_change().rolling(window=period).std()
            
            # True Range
            high_low = df['high'] - df['low']
            high_close = abs(df['high'] - df['close'].shift())
            low_close = abs(df['low'] - df['close'].shift())
            df['true_range'] = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            
            # Average True Range
            df[f'atr_{period}'] = df['true_range'].rolling(window=period).mean()
        
        # Volatility regime
        df['volatility_regime'] = df['volatility_20d'] > df['volatility_20d'].rolling(window=50).mean()
        df['volatility_regime'] = df['volatility_regime'].astype(int)
        
        return df
    
    def _add_rsi_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add RSI and related features"""
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # RSI features
        df['rsi_normalized'] = df['rsi'] / 100.0
        df['rsi_oversold'] = (df['rsi'] < 30).astype(int)
        df['rsi_overbought'] = (df['rsi'] > 70).astype(int)
        df['rsi_slope'] = df['rsi'].diff(5)
        
        return df
    
    def _add_macd_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add MACD features"""
        ema_12 = df['close'].ewm(span=12, adjust=False).mean()
        ema_26 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = ema_12 - ema_26
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # MACD features
        df['macd_above_signal'] = (df['macd'] > df['macd_signal']).astype(int)
        df['macd_crossover'] = ((df['macd'] > df['macd_signal']) & 
                                (df['macd'].shift() <= df['macd_signal'].shift())).astype(int)
        df['macd_crossunder'] = ((df['macd'] < df['macd_signal']) & 
                                 (df['macd'].shift() >= df['macd_signal'].shift())).astype(int)
        
        return df
    
    def _add_bollinger_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add Bollinger Bands features"""
        sma_20 = df['close'].rolling(window=20).mean()
        std_20 = df['close'].rolling(window=20).std()
        
        df['bb_upper'] = sma_20 + (std_20 * 2)
        df['bb_lower'] = sma_20 - (std_20 * 2)
        df['bb_middle'] = sma_20
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / sma_20
        
        # Position within bands
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        df['bb_position'] = df['bb_position'].clip(0, 1)  # Clip to [0, 1]
        
        # Band squeeze (low volatility)
        df['bb_squeeze'] = (df['bb_width'] < df['bb_width'].rolling(window=50).mean() * 0.6).astype(int)
        
        return df
    
    def _add_atr_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add ATR-based features"""
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr_14'] = true_range.rolling(window=14).mean()
        
        # ATR features
        df['atr_ratio'] = df['atr_14'] / df['close']
        df['atr_normalized'] = df['atr_14'] / df['atr_14'].rolling(window=50).mean()
        
        return df
    
    def _add_volume_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volume-based features"""
        for period in self.config.volume_periods:
            df[f'volume_sma_{period}'] = df['volume'].rolling(window=period).mean()
            df[f'volume_ratio_{period}'] = df['volume'] / df[f'volume_sma_{period}']
        
        # Volume trend
        df['volume_trend'] = df['volume'].diff(5)
        df['volume_price_trend'] = np.where(
            (df['close'] > df['close'].shift()) & (df['volume'] > df['volume'].shift()),
            1,  # Bullish volume
            np.where(
                (df['close'] < df['close'].shift()) & (df['volume'] > df['volume'].shift()),
                -1,  # Bearish volume
                0  # Neutral
            )
        )
        
        # OBV (On-Balance Volume)
        df['obv'] = (np.sign(df['close'].diff()) * df['volume']).cumsum()
        df['obv_slope'] = df['obv'].diff(10)
        
        return df
    
    def _add_candlestick_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add candlestick pattern features"""
        # Body size
        df['body_size'] = abs(df['close'] - df['open'])
        df['body_pct'] = df['body_size'] / (df['high'] - df['low'] + 1e-10)
        
        # Upper and lower shadows
        df['upper_shadow'] = df['high'] - df[['close', 'open']].max(axis=1)
        df['lower_shadow'] = df[['close', 'open']].min(axis=1) - df['low']
        df['upper_shadow_pct'] = df['upper_shadow'] / (df['high'] - df['low'] + 1e-10)
        df['lower_shadow_pct'] = df['lower_shadow'] / (df['high'] - df['low'] + 1e-10)
        
        # Direction
        df['bullish'] = (df['close'] > df['open']).astype(int)
        
        # Doji pattern (small body)
        df['doji'] = (df['body_pct'] < 0.1).astype(int)
        
        # Hammer pattern (long lower shadow, small body at top)
        df['hammer'] = ((df['lower_shadow_pct'] > 0.6) & 
                        (df['body_pct'] < 0.3) & 
                        (df['bullish'] == 1)).astype(int)
        
        # Shooting star (long upper shadow, small body at bottom)
        df['shooting_star'] = ((df['upper_shadow_pct'] > 0.6) & 
                               (df['body_pct'] < 0.3) & 
                               (df['bullish'] == 0)).astype(int)
        
        # Engulfing patterns
        df['bullish_engulfing'] = ((df['bullish'] == 1) & 
                                   (df['bullish'].shift() == 0) &
                                   (df['open'] < df['close'].shift()) &
                                   (df['close'] > df['open'].shift())).astype(int)
        
        df['bearish_engulfing'] = ((df['bullish'] == 0) & 
                                   (df['bullish'].shift() == 1) &
                                   (df['open'] > df['close'].shift()) &
                                   (df['close'] < df['open'].shift())).astype(int)
        
        return df
    
    def create_target(self, df: pd.DataFrame, horizon: int = 5, 
                      threshold: float = 0.01) -> pd.DataFrame:
        """
        Create target variable for classification.
        
        Args:
            df: DataFrame with features
            horizon: Prediction horizon in periods
            threshold: Minimum return threshold for classification
            
        Returns:
            DataFrame with target column added
        """
        # Future return
        future_return = df['close'].shift(-horizon) / df['close'] - 1
        
        # Classification target
        df['target'] = np.where(
            future_return > threshold,
            1,  # Up
            np.where(
                future_return < -threshold,
                -1,  # Down
                0  # Neutral
            )
        )
        
        # Regression target
        df['target_return'] = future_return
        
        return df
    
    def get_feature_matrix(self, df: pd.DataFrame, drop_na: bool = True) -> tuple:
        """
        Get feature matrix X and target vector y.
        
        Args:
            df: DataFrame with features and target
            drop_na: Whether to drop rows with NaN values
            
        Returns:
            Tuple of (X, y) where X is feature matrix and y is target vector
        """
        if not self.feature_names:
            raise ValueError("Features not created yet. Call create_features() first.")
        
        X = df[self.feature_names].copy()
        y = df['target'].copy() if 'target' in df.columns else None
        
        if drop_na:
            mask = X.notna().all(axis=1)
            if y is not None:
                mask = mask & y.notna()
            X = X[mask]
            y = y[mask] if y is not None else None
        
        return X, y
    
    def get_feature_importance_report(self, feature_importance: np.ndarray) -> pd.DataFrame:
        """
        Create a feature importance report.
        
        Args:
            feature_importance: Array of feature importance scores
            
        Returns:
            DataFrame with feature names and importance scores
        """
        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': feature_importance
        })
        importance_df = importance_df.sort_values('importance', ascending=False)
        return importance_df
