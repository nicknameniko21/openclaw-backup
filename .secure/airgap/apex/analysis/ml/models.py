"""
Price Prediction Models
Machine learning models for predicting future price movements.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import pickle
from pathlib import Path


class ModelType(Enum):
    """Types of prediction models"""
    CLASSIFICATION = "classification"  # Predict up/down/neutral
    REGRESSION = "regression"  # Predict future return
    PROBABILITY = "probability"  # Predict probability of up/down


@dataclass
class Prediction:
    """Prediction result"""
    direction: int  # -1, 0, 1 for down, neutral, up
    probability: float  # Probability of predicted direction
    confidence: float  # Model confidence (0-1)
    expected_return: float  # Expected return
    metadata: Dict[str, Any] = None


class BasePriceModel:
    """Base class for price prediction models"""
    
    def __init__(self, model_type: ModelType = ModelType.CLASSIFICATION):
        self.model_type = model_type
        self.model = None
        self.is_trained = False
        self.feature_names: List[str] = []
        
    def train(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Train the model"""
        raise NotImplementedError
    
    def predict(self, X: pd.DataFrame) -> List[Prediction]:
        """Make predictions"""
        raise NotImplementedError
    
    def predict_single(self, features: Dict[str, float]) -> Prediction:
        """Make prediction for a single sample"""
        X = pd.DataFrame([features])
        predictions = self.predict(X)
        return predictions[0] if predictions else None
    
    def save(self, filepath: str) -> None:
        """Save model to file"""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'model_type': self.model_type,
                'feature_names': self.feature_names,
                'is_trained': self.is_trained
            }, f)
    
    def load(self, filepath: str) -> None:
        """Load model from file"""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
            self.model = data['model']
            self.model_type = data['model_type']
            self.feature_names = data['feature_names']
            self.is_trained = data['is_trained']


class RandomForestPriceModel(BasePriceModel):
    """
    Random Forest model for price prediction.
    Good for capturing non-linear relationships and feature interactions.
    """
    
    def __init__(self, model_type: ModelType = ModelType.CLASSIFICATION,
                 n_estimators: int = 100, max_depth: int = 10,
                 min_samples_split: int = 5, random_state: int = 42):
        super().__init__(model_type)
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.random_state = random_state
        
    def train(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Train Random Forest model"""
        try:
            from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
            from sklearn.model_selection import cross_val_score
            
            self.feature_names = list(X.columns)
            
            if self.model_type == ModelType.CLASSIFICATION:
                self.model = RandomForestClassifier(
                    n_estimators=self.n_estimators,
                    max_depth=self.max_depth,
                    min_samples_split=self.min_samples_split,
                    random_state=self.random_state,
                    n_jobs=-1
                )
            else:
                self.model = RandomForestRegressor(
                    n_estimators=self.n_estimators,
                    max_depth=self.max_depth,
                    min_samples_split=self.min_samples_split,
                    random_state=self.random_state,
                    n_jobs=-1
                )
            
            self.model.fit(X, y)
            self.is_trained = True
            
            # Calculate cross-validation score
            if self.model_type == ModelType.CLASSIFICATION:
                scores = cross_val_score(self.model, X, y, cv=5, scoring='accuracy')
                print(f"Cross-validation accuracy: {scores.mean():.3f} (+/- {scores.std()*2:.3f})")
            
        except ImportError:
            print("scikit-learn not installed. Using mock model.")
            self._train_mock(X, y)
    
    def _train_mock(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Train a simple mock model when sklearn is not available"""
        self.feature_names = list(X.columns)
        self.is_trained = True
        
        # Store class distribution for classification
        if self.model_type == ModelType.CLASSIFICATION:
            self.model = {'class_distribution': y.value_counts().to_dict()}
        else:
            self.model = {'mean': y.mean(), 'std': y.std()}
    
    def predict(self, X: pd.DataFrame) -> List[Prediction]:
        """Make predictions using Random Forest"""
        if not self.is_trained:
            raise ValueError("Model not trained yet")
        
        predictions = []
        
        if isinstance(self.model, dict):  # Mock model
            return self._predict_mock(X)
        
        if self.model_type == ModelType.CLASSIFICATION:
            # Get class probabilities
            probs = self.model.predict_proba(X)
            classes = self.model.classes_
            
            for i, prob in enumerate(probs):
                # Find class with highest probability
                max_idx = np.argmax(prob)
                direction = int(classes[max_idx])
                probability = prob[max_idx]
                
                # Calculate confidence based on probability spread
                confidence = (prob[max_idx] - np.mean(prob)) / (np.std(prob) + 1e-10)
                confidence = min(max(confidence, 0), 1)  # Clip to [0, 1]
                
                predictions.append(Prediction(
                    direction=direction,
                    probability=probability,
                    confidence=confidence,
                    expected_return=direction * probability * 0.01,  # Rough estimate
                    metadata={'class_probabilities': dict(zip(classes, prob))}
                ))
        else:
            # Regression
            y_pred = self.model.predict(X)
            
            for pred in y_pred:
                direction = 1 if pred > 0.005 else (-1 if pred < -0.005 else 0)
                predictions.append(Prediction(
                    direction=direction,
                    probability=0.5 + abs(pred) * 10,  # Rough probability estimate
                    confidence=min(abs(pred) * 50, 1.0),
                    expected_return=pred
                ))
        
        return predictions
    
    def _predict_mock(self, X: pd.DataFrame) -> List[Prediction]:
        """Mock predictions when sklearn is not available"""
        predictions = []
        
        for _ in range(len(X)):
            if self.model_type == ModelType.CLASSIFICATION:
                # Random prediction based on class distribution
                direction = np.random.choice([-1, 0, 1])
                predictions.append(Prediction(
                    direction=direction,
                    probability=0.33,
                    confidence=0.3,
                    expected_return=0
                ))
            else:
                # Random return prediction
                expected_return = np.random.normal(0, 0.01)
                direction = 1 if expected_return > 0 else -1
                predictions.append(Prediction(
                    direction=direction,
                    probability=0.5,
                    confidence=0.3,
                    expected_return=expected_return
                ))
        
        return predictions
    
    def get_feature_importance(self) -> pd.DataFrame:
        """Get feature importance from the model"""
        if not self.is_trained or isinstance(self.model, dict):
            return pd.DataFrame()
        
        importance = self.model.feature_importances_
        return pd.DataFrame({
            'feature': self.feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False)


class GradientBoostingPriceModel(BasePriceModel):
    """
    Gradient Boosting model for price prediction.
    Often more accurate than Random Forest for tabular data.
    """
    
    def __init__(self, model_type: ModelType = ModelType.CLASSIFICATION,
                 n_estimators: int = 100, learning_rate: float = 0.1,
                 max_depth: int = 6, random_state: int = 42):
        super().__init__(model_type)
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.max_depth = max_depth
        self.random_state = random_state
    
    def train(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Train Gradient Boosting model"""
        try:
            from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
            
            self.feature_names = list(X.columns)
            
            if self.model_type == ModelType.CLASSIFICATION:
                self.model = GradientBoostingClassifier(
                    n_estimators=self.n_estimators,
                    learning_rate=self.learning_rate,
                    max_depth=self.max_depth,
                    random_state=self.random_state
                )
            else:
                self.model = GradientBoostingRegressor(
                    n_estimators=self.n_estimators,
                    learning_rate=self.learning_rate,
                    max_depth=self.max_depth,
                    random_state=self.random_state
                )
            
            self.model.fit(X, y)
            self.is_trained = True
            
            # Print training score
            train_score = self.model.score(X, y)
            print(f"Training score: {train_score:.3f}")
            
        except ImportError:
            print("scikit-learn not installed. Using mock model.")
            self._train_mock(X, y)
    
    def _train_mock(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Mock training"""
        self.feature_names = list(X.columns)
        self.is_trained = True
        self.model = {'mock': True}
    
    def predict(self, X: pd.DataFrame) -> List[Prediction]:
        """Make predictions"""
        if not self.is_trained:
            raise ValueError("Model not trained yet")
        
        if isinstance(self.model, dict):
            return self._predict_mock(X)
        
        predictions = []
        
        if self.model_type == ModelType.CLASSIFICATION:
            probs = self.model.predict_proba(X)
            classes = self.model.classes_
            
            for prob in probs:
                max_idx = np.argmax(prob)
                direction = int(classes[max_idx])
                predictions.append(Prediction(
                    direction=direction,
                    probability=prob[max_idx],
                    confidence=prob[max_idx],
                    expected_return=direction * prob[max_idx] * 0.01
                ))
        else:
            y_pred = self.model.predict(X)
            for pred in y_pred:
                direction = 1 if pred > 0 else -1
                predictions.append(Prediction(
                    direction=direction,
                    probability=0.5 + abs(pred),
                    confidence=min(abs(pred) * 10, 1.0),
                    expected_return=pred
                ))
        
        return predictions
    
    def _predict_mock(self, X: pd.DataFrame) -> List[Prediction]:
        """Mock predictions"""
        return [Prediction(direction=0, probability=0.33, confidence=0.3, expected_return=0) 
                for _ in range(len(X))]
    
    def get_feature_importance(self) -> pd.DataFrame:
        """Get feature importance"""
        if not self.is_trained or isinstance(self.model, dict):
            return pd.DataFrame()
        
        return pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)


class EnsemblePriceModel(BasePriceModel):
    """
    Ensemble of multiple models for more robust predictions.
    """
    
    def __init__(self, models: Optional[List[BasePriceModel]] = None):
        super().__init__(ModelType.CLASSIFICATION)
        self.models = models or []
        self.weights: List[float] = []
    
    def add_model(self, model: BasePriceModel, weight: float = 1.0) -> None:
        """Add a model to the ensemble"""
        self.models.append(model)
        self.weights.append(weight)
    
    def train(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Train all models in the ensemble"""
        for i, model in enumerate(self.models):
            print(f"Training model {i+1}/{len(self.models)}...")
            model.train(X, y)
        self.is_trained = True
    
    def predict(self, X: pd.DataFrame) -> List[Prediction]:
        """Make ensemble predictions"""
        if not self.is_trained:
            raise ValueError("Models not trained yet")
        
        # Collect predictions from all models
        all_predictions = []
        for model in self.models:
            preds = model.predict(X)
            all_predictions.append(preds)
        
        # Weighted average
        predictions = []
        for i in range(len(X)):
            # Aggregate predictions
            directions = []
            probabilities = []
            confidences = []
            expected_returns = []
            
            for j, model_preds in enumerate(all_predictions):
                pred = model_preds[i]
                weight = self.weights[j] if j < len(self.weights) else 1.0
                
                directions.append(pred.direction * weight)
                probabilities.append(pred.probability * weight)
                confidences.append(pred.confidence * weight)
                expected_returns.append(pred.expected_return * weight)
            
            total_weight = sum(self.weights) if self.weights else len(self.models)
            
            # Final prediction
            avg_direction = sum(directions) / total_weight
            final_direction = 1 if avg_direction > 0.2 else (-1 if avg_direction < -0.2 else 0)
            
            predictions.append(Prediction(
                direction=final_direction,
                probability=sum(probabilities) / total_weight,
                confidence=sum(confidences) / total_weight,
                expected_return=sum(expected_returns) / total_weight
            ))
        
        return predictions


class ModelManager:
    """
    Manages multiple models for different symbols/timeframes.
    """
    
    def __init__(self, model_dir: str = 'apex/models'):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.models: Dict[str, BasePriceModel] = {}
    
    def get_model_key(self, symbol: str, timeframe: str, model_type: str) -> str:
        """Generate a unique key for a model"""
        return f"{symbol.replace('/', '_')}_{timeframe}_{model_type}"
    
    def register_model(self, symbol: str, timeframe: str, 
                       model: BasePriceModel, model_name: str = "rf") -> None:
        """Register a model for a symbol/timeframe"""
        key = self.get_model_key(symbol, timeframe, model_name)
        self.models[key] = model
    
    def get_model(self, symbol: str, timeframe: str, 
                  model_name: str = "rf") -> Optional[BasePriceModel]:
        """Get a model for a symbol/timeframe"""
        key = self.get_model_key(symbol, timeframe, model_name)
        return self.models.get(key)
    
    def save_all(self) -> None:
        """Save all registered models"""
        for key, model in self.models.items():
            filepath = self.model_dir / f"{key}.pkl"
            model.save(str(filepath))
            print(f"Saved model: {filepath}")
    
    def load_all(self) -> None:
        """Load all models from directory"""
        for filepath in self.model_dir.glob("*.pkl"):
            key = filepath.stem
            # Determine model type from filename or default to RF
            model = RandomForestPriceModel()
            model.load(str(filepath))
            self.models[key] = model
            print(f"Loaded model: {key}")
