"""
Anomaly Detection for Trading
Detects unusual patterns that may indicate market regime changes or opportunities.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class AnomalyType(Enum):
    """Types of anomalies"""
    PRICE_SPIKE = "price_spike"
    VOLUME_SPIKE = "volume_spike"
    VOLATILITY_REGIME_CHANGE = "volatility_regime_change"
    CORRELATION_BREAKDOWN = "correlation_breakdown"
    PATTERN_ANOMALY = "pattern_anomaly"


@dataclass
class Anomaly:
    """Anomaly detection result"""
    timestamp: datetime
    type: AnomalyType
    severity: float  # 0-1, higher is more severe
    description: str
    symbol: str
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class AnomalyDetector:
    """
    Detects anomalies in price and volume data.
    """
    
    def __init__(self, 
                 price_spike_threshold: float = 3.0,
                 volume_spike_threshold: float = 3.0,
                 volatility_window: int = 20,
                 lookback_window: int = 100):
        self.price_spike_threshold = price_spike_threshold
        self.volume_spike_threshold = volume_spike_threshold
        self.volatility_window = volatility_window
        self.lookback_window = lookback_window
        self.baseline_stats: Dict[str, Dict] = {}
    
    def fit(self, data: pd.DataFrame, symbol: str) -> None:
        """
        Calculate baseline statistics for anomaly detection.
        
        Args:
            data: Historical price data
            symbol: Symbol identifier
        """
        # Calculate returns
        returns = data['close'].pct_change().dropna()
        
        # Calculate volume changes
        volume_changes = data['volume'].pct_change().dropna()
        
        self.baseline_stats[symbol] = {
            'return_mean': returns.mean(),
            'return_std': returns.std(),
            'volume_mean': volume_changes.mean(),
            'volume_std': volume_changes.std(),
            'volatility_mean': returns.rolling(self.volatility_window).std().mean(),
            'volatility_std': returns.rolling(self.volatility_window).std().std(),
            'price_range_mean': ((data['high'] - data['low']) / data['close']).mean(),
            'price_range_std': ((data['high'] - data['low']) / data['close']).std()
        }
    
    def detect(self, data: pd.DataFrame, symbol: str) -> List[Anomaly]:
        """
        Detect anomalies in the latest data.
        
        Args:
            data: Recent price data
            symbol: Symbol identifier
            
        Returns:
            List of detected anomalies
        """
        if symbol not in self.baseline_stats:
            self.fit(data, symbol)
        
        anomalies = []
        
        # Get latest data point
        if len(data) == 0:
            return anomalies
        
        latest = data.iloc[-1]
        timestamp = latest.get('timestamp', datetime.now())
        
        # Price spike detection
        price_anomaly = self._detect_price_spike(data, symbol, timestamp)
        if price_anomaly:
            anomalies.append(price_anomaly)
        
        # Volume spike detection
        volume_anomaly = self._detect_volume_spike(data, symbol, timestamp)
        if volume_anomaly:
            anomalies.append(volume_anomaly)
        
        # Volatility regime change
        vol_anomaly = self._detect_volatility_regime(data, symbol, timestamp)
        if vol_anomaly:
            anomalies.append(vol_anomaly)
        
        # Pattern anomaly
        pattern_anomaly = self._detect_pattern_anomaly(data, symbol, timestamp)
        if pattern_anomaly:
            anomalies.append(pattern_anomaly)
        
        return anomalies
    
    def _detect_price_spike(self, data: pd.DataFrame, symbol: str, 
                           timestamp: datetime) -> Optional[Anomaly]:
        """Detect unusual price movements"""
        stats = self.baseline_stats[symbol]
        
        # Calculate recent return
        if len(data) < 2:
            return None
        
        recent_return = (data['close'].iloc[-1] / data['close'].iloc[-2]) - 1
        
        # Z-score of return
        z_score = (recent_return - stats['return_mean']) / (stats['return_std'] + 1e-10)
        
        if abs(z_score) > self.price_spike_threshold:
            severity = min(abs(z_score) / (self.price_spike_threshold * 2), 1.0)
            direction = "up" if recent_return > 0 else "down"
            
            return Anomaly(
                timestamp=timestamp,
                type=AnomalyType.PRICE_SPIKE,
                severity=severity,
                description=f"Price spike {direction}: {recent_return:.2%} (z-score: {z_score:.2f})",
                symbol=symbol,
                metadata={
                    'return': recent_return,
                    'z_score': z_score,
                    'direction': direction,
                    'threshold': self.price_spike_threshold
                }
            )
        
        return None
    
    def _detect_volume_spike(self, data: pd.DataFrame, symbol: str,
                            timestamp: datetime) -> Optional[Anomaly]:
        """Detect unusual volume activity"""
        stats = self.baseline_stats[symbol]
        
        if len(data) < 2:
            return None
        
        # Recent volume change
        recent_volume_change = (data['volume'].iloc[-1] / data['volume'].iloc[-2]) - 1
        
        # Z-score
        z_score = (recent_volume_change - stats['volume_mean']) / (stats['volume_std'] + 1e-10)
        
        if z_score > self.volume_spike_threshold:
            severity = min(z_score / (self.volume_spike_threshold * 2), 1.0)
            
            return Anomaly(
                timestamp=timestamp,
                type=AnomalyType.VOLUME_SPIKE,
                severity=severity,
                description=f"Volume spike: {recent_volume_change:.1%} above normal (z-score: {z_score:.2f})",
                symbol=symbol,
                metadata={
                    'volume_change': recent_volume_change,
                    'z_score': z_score,
                    'current_volume': data['volume'].iloc[-1],
                    'avg_volume': data['volume'].iloc[-10:].mean()
                }
            )
        
        return None
    
    def _detect_volatility_regime(self, data: pd.DataFrame, symbol: str,
                                 timestamp: datetime) -> Optional[Anomaly]:
        """Detect changes in volatility regime"""
        stats = self.baseline_stats[symbol]
        
        if len(data) < self.volatility_window:
            return None
        
        # Recent volatility
        recent_returns = data['close'].pct_change().dropna().tail(self.volatility_window)
        recent_volatility = recent_returns.std()
        
        # Z-score of volatility
        z_score = (recent_volatility - stats['volatility_mean']) / (stats['volatility_std'] + 1e-10)
        
        if abs(z_score) > 2.0:  # 2 sigma threshold
            severity = min(abs(z_score) / 4.0, 1.0)
            regime = "high" if recent_volatility > stats['volatility_mean'] else "low"
            
            return Anomaly(
                timestamp=timestamp,
                type=AnomalyType.VOLATILITY_REGIME_CHANGE,
                severity=severity,
                description=f"Volatility regime change to {regime} (z-score: {z_score:.2f})",
                symbol=symbol,
                metadata={
                    'recent_volatility': recent_volatility,
                    'baseline_volatility': stats['volatility_mean'],
                    'z_score': z_score,
                    'regime': regime
                }
            )
        
        return None
    
    def _detect_pattern_anomaly(self, data: pd.DataFrame, symbol: str,
                               timestamp: datetime) -> Optional[Anomaly]:
        """Detect unusual candlestick patterns"""
        if len(data) < 5:
            return None
        
        latest = data.iloc[-1]
        
        # Calculate candlestick metrics
        body_size = abs(latest['close'] - latest['open'])
        total_range = latest['high'] - latest['low']
        
        if total_range == 0:
            return None
        
        body_ratio = body_size / total_range
        upper_shadow = (latest['high'] - max(latest['close'], latest['open'])) / total_range
        lower_shadow = (min(latest['close'], latest['open']) - latest['low']) / total_range
        
        # Detect doji (very small body)
        if body_ratio < 0.1:
            return Anomaly(
                timestamp=timestamp,
                type=AnomalyType.PATTERN_ANOMALY,
                severity=0.5,
                description=f"Doji pattern detected (indecision)",
                symbol=symbol,
                metadata={
                    'pattern': 'doji',
                    'body_ratio': body_ratio,
                    'upper_shadow': upper_shadow,
                    'lower_shadow': lower_shadow
                }
            )
        
        # Detect hammer/inverted hammer
        if body_ratio > 0.2 and body_ratio < 0.6:
            if lower_shadow > 0.5 and upper_shadow < 0.1:
                return Anomaly(
                    timestamp=timestamp,
                    type=AnomalyType.PATTERN_ANOMALY,
                    severity=0.6,
                    description=f"Hammer pattern detected (potential reversal)",
                    symbol=symbol,
                    metadata={
                        'pattern': 'hammer',
                        'body_ratio': body_ratio,
                        'lower_shadow': lower_shadow
                    }
                )
            
            if upper_shadow > 0.5 and lower_shadow < 0.1:
                return Anomaly(
                    timestamp=timestamp,
                    type=AnomalyType.PATTERN_ANOMALY,
                    severity=0.6,
                    description=f"Inverted hammer pattern detected (potential reversal)",
                    symbol=symbol,
                    metadata={
                        'pattern': 'inverted_hammer',
                        'body_ratio': body_ratio,
                        'upper_shadow': upper_shadow
                    }
                )
        
        return None
    
    def get_anomaly_summary(self, anomalies: List[Anomaly]) -> Dict:
        """Get summary statistics of anomalies"""
        if not anomalies:
            return {'count': 0, 'types': {}, 'avg_severity': 0}
        
        type_counts = {}
        for anomaly in anomalies:
            type_counts[anomaly.type.value] = type_counts.get(anomaly.type.value, 0) + 1
        
        return {
            'count': len(anomalies),
            'types': type_counts,
            'avg_severity': sum(a.severity for a in anomalies) / len(anomalies),
            'high_severity_count': sum(1 for a in anomalies if a.severity > 0.7)
        }


class MarketRegimeDetector:
    """
    Detects market regimes (trending, ranging, volatile, etc.)
    """
    
    def __init__(self, lookback: int = 50):
        self.lookback = lookback
    
    def detect_regime(self, data: pd.DataFrame) -> Dict:
        """
        Detect current market regime.
        
        Returns:
            Dictionary with regime information
        """
        if len(data) < self.lookback:
            return {'regime': 'unknown', 'confidence': 0}
        
        recent = data.tail(self.lookback)
        
        # Calculate metrics
        returns = recent['close'].pct_change().dropna()
        
        # Trend strength (using linear regression slope)
        x = np.arange(len(recent))
        y = recent['close'].values
        slope = np.polyfit(x, y, 1)[0]
        slope_normalized = slope / recent['close'].mean()
        
        # Volatility
        volatility = returns.std() * np.sqrt(252)  # Annualized
        
        # Trend consistency (percentage of days in trend direction)
        trend_direction = 1 if slope > 0 else -1
        consistent_days = sum(1 for r in returns if np.sign(r) == trend_direction)
        trend_consistency = consistent_days / len(returns) if len(returns) > 0 else 0
        
        # ADX approximation (trend strength)
        adx_proxy = abs(slope_normalized) * 1000 * trend_consistency
        
        # Classify regime
        if adx_proxy > 25 and trend_consistency > 0.6:
            if slope > 0:
                regime = 'strong_uptrend'
            else:
                regime = 'strong_downtrend'
            confidence = min(adx_proxy / 50, 1.0)
        elif adx_proxy > 15:
            if slope > 0:
                regime = 'weak_uptrend'
            else:
                regime = 'weak_downtrend'
            confidence = min(adx_proxy / 30, 1.0)
        elif volatility > 0.5:  # High volatility
            regime = 'volatile'
            confidence = min(volatility, 1.0)
        else:
            regime = 'ranging'
            confidence = 1 - min(adx_proxy / 25, 1.0)
        
        return {
            'regime': regime,
            'confidence': confidence,
            'slope': slope_normalized,
            'volatility': volatility,
            'trend_consistency': trend_consistency,
            'adx_proxy': adx_proxy
        }
