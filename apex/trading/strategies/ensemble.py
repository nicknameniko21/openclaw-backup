"""
Strategy Ensemble
Combines multiple strategies for consensus-based trading.
"""

from typing import List, Dict
import pandas as pd
from datetime import datetime

from .base import BaseStrategy, Signal, SignalType
from .breakout import BreakoutStrategy
from .mean_reversion import MeanReversionStrategy
from .trend_following import TrendFollowingStrategy


class StrategyEnsemble(BaseStrategy):
    """
    Ensemble strategy that combines signals from multiple strategies.
    
    Only generates signals when multiple strategies agree.
    
    Consensus levels:
    - Strong: 3+ strategies agree
    - Moderate: 2 strategies agree
    - Weak: Single strategy (filtered out by default)
    """
    
    def __init__(self, config: Dict):
        super().__init__(config)
        
        # Initialize component strategies
        self.strategies: List[BaseStrategy] = []
        self.min_consensus = config.get('min_consensus', 2)
        
        # Add breakout strategy
        if config.get('breakout', {}).get('enabled', True):
            self.strategies.append(BreakoutStrategy(config.get('breakout', {})))
        
        # Add mean reversion strategy
        if config.get('mean_reversion', {}).get('enabled', True):
            self.strategies.append(MeanReversionStrategy(config.get('mean_reversion', {})))
        
        # Add trend following strategy
        if config.get('trend_following', {}).get('enabled', True):
            self.strategies.append(TrendFollowingStrategy(config.get('trend_following', {})))
        
        self.logger.info(f"Ensemble initialized with {len(self.strategies)} strategies")
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate indicators for all component strategies"""
        for strategy in self.strategies:
            data = strategy.calculate_indicators(data)
        return data
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """Generate consensus-based signals"""
        all_signals: List[Signal] = []
        
        # Collect signals from all strategies
        for strategy in self.strategies:
            try:
                signals = strategy.generate_signals(data)
                all_signals.extend(signals)
            except Exception as e:
                self.logger.error(f"Error in {strategy.name}: {e}")
        
        # Group signals by symbol and type
        buy_votes: Dict[str, List[Signal]] = {}
        sell_votes: Dict[str, List[Signal]] = {}
        
        for signal in all_signals:
            if signal.type == SignalType.BUY:
                if signal.symbol not in buy_votes:
                    buy_votes[signal.symbol] = []
                buy_votes[signal.symbol].append(signal)
            elif signal.type == SignalType.SELL:
                if signal.symbol not in sell_votes:
                    sell_votes[signal.symbol] = []
                sell_votes[signal.symbol].append(signal)
        
        # Generate consensus signals
        consensus_signals: List[Signal] = []
        current_price = data.iloc[-1]['close'] if len(data) > 0 else 0
        
        # Check buy consensus
        for symbol, votes in buy_votes.items():
            if len(votes) >= self.min_consensus:
                avg_confidence = sum(v.confidence for v in votes) / len(votes)
                contributing_strategies = [v.metadata.get('strategy', 'unknown') for v in votes]
                
                consensus_signals.append(Signal(
                    type=SignalType.BUY,
                    symbol=symbol,
                    timestamp=datetime.now(),
                    price=current_price,
                    confidence=avg_confidence * (len(votes) / len(self.strategies)),
                    metadata={
                        'strategy': 'ensemble',
                        'consensus_count': len(votes),
                        'contributing_strategies': contributing_strategies,
                        'consensus_strength': 'strong' if len(votes) >= 3 else 'moderate'
                    }
                ))
        
        # Check sell consensus
        for symbol, votes in sell_votes.items():
            if len(votes) >= self.min_consensus:
                avg_confidence = sum(v.confidence for v in votes) / len(votes)
                contributing_strategies = [v.metadata.get('strategy', 'unknown') for v in votes]
                
                consensus_signals.append(Signal(
                    type=SignalType.SELL,
                    symbol=symbol,
                    timestamp=datetime.now(),
                    price=current_price,
                    confidence=avg_confidence * (len(votes) / len(self.strategies)),
                    metadata={
                        'strategy': 'ensemble',
                        'consensus_count': len(votes),
                        'contributing_strategies': contributing_strategies,
                        'consensus_strength': 'strong' if len(votes) >= 3 else 'moderate'
                    }
                ))
        
        return consensus_signals
    
    def get_strategy_performance(self) -> Dict:
        """Get performance metrics for all component strategies"""
        performance = {}
        for strategy in self.strategies:
            performance[strategy.name] = strategy.get_performance_metrics()
        return performance
    
    def __str__(self):
        strategy_names = [s.name for s in self.strategies]
        return f"StrategyEnsemble({', '.join(strategy_names)}, min_consensus={self.min_consensus})"
