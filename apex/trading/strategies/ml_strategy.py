"""
Machine Learning Strategy
Uses trained ML models to generate trading signals.
"""

from typing import List, Dict
import pandas as pd
import numpy as np
from datetime import datetime

from ..strategies.base import BaseStrategy, Signal, SignalType
from ..ml.features import FeatureEngineer, FeatureConfig
from ..ml.models import RandomForestPriceModel, ModelType, Prediction
from ..ml.anomaly import AnomalyDetector, MarketRegimeDetector


class MLStrategy(BaseStrategy):
    """
    Machine Learning-based trading strategy.
    
    Uses trained ML models to predict price movements and generate signals.
    Can adapt to different market regimes and detect anomalies.
    """
    
    def __init__(self, config: Dict):
        super().__init__(config)
        
        # Feature engineering
        feature_config = FeatureConfig(
            include_returns=config.get('include_returns', True),
            include_ma_ratios=config.get('include_ma_ratios', True),
            include_volatility=config.get('include_volatility', True),
            include_rsi=config.get('include_rsi', True),
            include_macd=config.get('include_macd', True),
            include_bollinger=config.get('include_bollinger', True),
            include_atr=config.get('include_atr', True),
            include_volume=config.get('include_volume', True),
            include_candlestick=config.get('include_candlestick', True)
        )
        self.feature_engineer = FeatureEngineer(feature_config)
        
        # ML Model
        self.model = RandomForestPriceModel(
            model_type=ModelType.CLASSIFICATION,
            n_estimators=config.get('n_estimators', 100),
            max_depth=config.get('max_depth', 10)
        )
        
        # Anomaly detection
        self.anomaly_detector = AnomalyDetector()
        self.regime_detector = MarketRegimeDetector()
        
        # Strategy parameters
        self.prediction_threshold = config.get('prediction_threshold', 0.6)
        self.min_confidence = config.get('min_confidence', 0.55)
        self.use_regime_filter = config.get('use_regime_filter', True)
        self.use_anomaly_filter = config.get('use_anomaly_filter', True)
        self.regime_preference = config.get('regime_preference', None)  # 'trending', 'ranging', None
        
        # Training state
        self.is_trained = False
        self.training_data_size = config.get('training_data_size', 500)
        
    def train(self, historical_data: pd.DataFrame) -> None:
        """
        Train the ML model on historical data.
        
        Args:
            historical_data: DataFrame with OHLCV data
        """
        print(f"Training ML model on {len(historical_data)} samples...")
        
        # Create features
        df = self.feature_engineer.create_features(historical_data)
        
        # Create target
        horizon = self.config.get('prediction_horizon', 5)
        threshold = self.config.get('return_threshold', 0.01)
        df = self.feature_engineer.create_target(df, horizon=horizon, threshold=threshold)
        
        # Get feature matrix
        X, y = self.feature_engineer.get_feature_matrix(df, drop_na=True)
        
        if len(X) < 100:
            print(f"Warning: Insufficient training data ({len(X)} samples)")
            return
        
        # Train model
        self.model.train(X, y)
        self.is_trained = True
        
        # Print feature importance
        importance_df = self.model.get_feature_importance()
        if not importance_df.empty:
            print("\nTop 10 Important Features:")
            print(importance_df.head(10).to_string(index=False))
        
        # Fit anomaly detector
        self.anomaly_detector.fit(historical_data, self.symbols[0] if self.symbols else 'UNKNOWN')
        
        print(f"Training complete. Model ready for predictions.")
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate ML features as indicators"""
        return self.feature_engineer.create_features(data)
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """Generate signals using ML predictions"""
        signals = []
        
        if len(data) < 50:
            return signals
        
        # Auto-train if not trained
        if not self.is_trained and len(data) >= self.training_data_size:
            self.train(data)
        
        if not self.is_trained:
            return signals
        
        # Create features for latest data
        df = self.feature_engineer.create_features(data)
        
        # Get latest features
        latest_features = df[self.feature_engineer.feature_names].iloc[-1:]
        
        # Check for NaN
        if latest_features.isna().any().any():
            return signals
        
        # Make prediction
        predictions = self.model.predict(latest_features)
        
        if not predictions:
            return signals
        
        prediction = predictions[0]
        
        # Detect anomalies
        anomalies = self.anomaly_detector.detect(data, self.symbols[0] if self.symbols else 'UNKNOWN')
        
        # Detect market regime
        regime_info = self.regime_detector.detect_regime(data)
        
        # Filter signals based on regime preference
        if self.use_regime_filter and self.regime_preference:
            if self.regime_preference == 'trending' and 'trend' not in regime_info['regime']:
                return signals
            if self.regime_preference == 'ranging' and regime_info['regime'] != 'ranging':
                return signals
        
        # Filter signals during high anomaly periods
        if self.use_anomaly_filter:
            high_severity_anomalies = [a for a in anomalies if a.severity > 0.8]
            if high_severity_anomalies:
                # Reduce confidence during anomalies
                prediction.confidence *= 0.5
        
        # Generate signal if confidence is high enough
        if prediction.confidence >= self.min_confidence and prediction.probability >= self.prediction_threshold:
            symbol = self.symbols[0] if self.symbols else 'UNKNOWN'
            current_price = data['close'].iloc[-1]
            
            if prediction.direction == 1:  # Up
                signals.append(Signal(
                    type=SignalType.BUY,
                    symbol=symbol,
                    timestamp=datetime.now(),
                    price=current_price,
                    confidence=prediction.confidence,
                    metadata={
                        'strategy': 'ml_prediction',
                        'prediction_probability': prediction.probability,
                        'expected_return': prediction.expected_return,
                        'market_regime': regime_info['regime'],
                        'regime_confidence': regime_info['confidence'],
                        'anomalies_detected': len(anomalies),
                        'model_type': 'random_forest'
                    }
                ))
            elif prediction.direction == -1:  # Down
                signals.append(Signal(
                    type=SignalType.SELL,
                    symbol=symbol,
                    timestamp=datetime.now(),
                    price=current_price,
                    confidence=prediction.confidence,
                    metadata={
                        'strategy': 'ml_prediction',
                        'prediction_probability': prediction.probability,
                        'expected_return': prediction.expected_return,
                        'market_regime': regime_info['regime'],
                        'regime_confidence': regime_info['confidence'],
                        'anomalies_detected': len(anomalies),
                        'model_type': 'random_forest'
                    }
                ))
        
        return signals
    
    def get_model_info(self) -> Dict:
        """Get information about the trained model"""
        if not self.is_trained:
            return {'status': 'not_trained'}
        
        importance_df = self.model.get_feature_importance()
        
        return {
            'status': 'trained',
            'model_type': 'RandomForest',
            'n_estimators': self.model.n_estimators,
            'max_depth': self.model.max_depth,
            'feature_count': len(self.feature_engineer.feature_names),
            'top_features': importance_df.head(5)['feature'].tolist() if not importance_df.empty else []
        }
    
    def save_model(self, filepath: str) -> None:
        """Save the trained model"""
        if self.is_trained:
            self.model.save(filepath)
    
    def load_model(self, filepath: str) -> None:
        """Load a trained model"""
        self.model.load(filepath)
        self.is_trained = True
    
    def __str__(self):
        status = "trained" if self.is_trained else "untrained"
        return f"MLStrategy({status}, confidence>={self.min_confidence})"
