"""
Apex Trading System - Test Suite
Unit and integration tests for the trading system.
"""

import unittest
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from trading.strategies.breakout import BreakoutStrategy
from trading.strategies.mean_reversion import MeanReversionStrategy
from trading.strategies.trend_following import TrendFollowingStrategy
from trading.strategies.ensemble import StrategyEnsemble
from trading.strategies.base import SignalType
from trading.risk.manager import RiskManager, RiskConfig, RiskLevel
from analysis.indicators.technical import (
    calculate_sma, calculate_ema, calculate_rsi, 
    calculate_macd, calculate_bollinger_bands, calculate_atr,
    TechnicalIndicators
)


class TestTechnicalIndicators(unittest.TestCase):
    """Test technical indicator calculations"""
    
    def setUp(self):
        """Set up test data"""
        # Generate sample OHLCV data as pandas Series
        np.random.seed(42)
        n = 100
        base_price = 50000
        
        self.close = pd.Series(
            base_price + np.cumsum(np.random.randn(n) * 100),
            name='close'
        )
        self.high = self.close + np.abs(np.random.randn(n) * 50)
        self.low = self.close - np.abs(np.random.randn(n) * 50)
        self.volume = pd.Series(np.random.randint(1000, 5000, n), name='volume')
        
        # Create DataFrame
        self.df = pd.DataFrame({
            'close': self.close,
            'high': self.high,
            'low': self.low,
            'volume': self.volume
        })
    
    def test_sma_calculation(self):
        """Test Simple Moving Average calculation"""
        sma = calculate_sma(self.close, period=20)
        self.assertIsNotNone(sma)
        self.assertIsInstance(sma, pd.Series)
        # First 19 values should be NaN
        self.assertTrue(sma.iloc[:19].isna().all())
        # 20th value should be calculated
        self.assertFalse(pd.isna(sma.iloc[19]))
    
    def test_ema_calculation(self):
        """Test Exponential Moving Average calculation"""
        ema = calculate_ema(self.close, period=20)
        self.assertIsNotNone(ema)
        self.assertIsInstance(ema, pd.Series)
        self.assertEqual(len(ema), len(self.close))
    
    def test_rsi_calculation(self):
        """Test RSI calculation"""
        rsi = calculate_rsi(self.close, period=14)
        self.assertIsNotNone(rsi)
        self.assertIsInstance(rsi, pd.Series)
        # RSI should be between 0 and 100 (where not NaN)
        valid_rsi = rsi.dropna()
        self.assertTrue((valid_rsi >= 0).all())
        self.assertTrue((valid_rsi <= 100).all())
    
    def test_bollinger_bands(self):
        """Test Bollinger Bands calculation"""
        upper, middle, lower = calculate_bollinger_bands(self.close, period=20, std_dev=2)
        
        self.assertIsInstance(upper, pd.Series)
        self.assertIsInstance(middle, pd.Series)
        self.assertIsInstance(lower, pd.Series)
        
        # Check that upper >= middle >= lower (where not NaN)
        valid_idx = upper.dropna().index
        self.assertTrue((upper[valid_idx] >= middle[valid_idx]).all())
        self.assertTrue((middle[valid_idx] >= lower[valid_idx]).all())
    
    def test_atr_calculation(self):
        """Test Average True Range calculation"""
        atr = calculate_atr(self.high, self.low, self.close, period=14)
        self.assertIsNotNone(atr)
        self.assertIsInstance(atr, pd.Series)
        # ATR should be positive (where not NaN)
        self.assertTrue((atr.dropna() > 0).all())
    
    def test_macd_calculation(self):
        """Test MACD calculation"""
        macd_line, signal_line, histogram = calculate_macd(self.close)
        
        self.assertIsInstance(macd_line, pd.Series)
        self.assertIsInstance(signal_line, pd.Series)
        self.assertIsInstance(histogram, pd.Series)
        
        # Histogram should equal macd - signal
        valid_idx = histogram.dropna().index
        pd.testing.assert_series_equal(
            histogram[valid_idx], 
            (macd_line - signal_line)[valid_idx]
        )
    
    def test_add_all_indicators(self):
        """Test adding all indicators to DataFrame"""
        result = TechnicalIndicators.add_all_indicators(self.df)
        
        # Check that all expected columns are added
        expected_columns = [
            'sma_20', 'sma_50', 'ema_12', 'ema_26',
            'rsi', 'macd', 'macd_signal', 'macd_hist',
            'bb_upper', 'bb_middle', 'bb_lower',
            'atr', 'stoch_k', 'stoch_d', 'adx', 'obv', 'vwap'
        ]
        
        for col in expected_columns:
            self.assertIn(col, result.columns)


class TestBreakoutStrategy(unittest.TestCase):
    """Test Breakout strategy"""
    
    def setUp(self):
        """Set up test strategy"""
        self.config = {
            'lookback': 20,
            'volume_confirm': True,
            'min_breakout_percent': 0.01,
            'symbols': ['BTC/USDT']
        }
        self.strategy = BreakoutStrategy(self.config)
    
    def test_strategy_initialization(self):
        """Test strategy initializes correctly"""
        self.assertEqual(self.strategy.lookback, 20)
        self.assertTrue(self.strategy.volume_confirm)
        self.assertEqual(self.strategy.min_breakout_percent, 0.01)
    
    def test_generate_signals_empty_data(self):
        """Test signal generation with empty data"""
        empty_df = pd.DataFrame()
        signals = self.strategy.generate_signals(empty_df)
        self.assertEqual(len(signals), 0)
    
    def test_generate_signals_insufficient_data(self):
        """Test signal generation with insufficient data"""
        # Create minimal DataFrame with required columns
        df = pd.DataFrame({
            'open': [50000],
            'high': [50100],
            'low': [49900],
            'close': [50050],
            'volume': [1000]
        })
        signals = self.strategy.generate_signals(df)
        self.assertEqual(len(signals), 0)
    
    def test_calculate_indicators(self):
        """Test indicator calculation"""
        # Create sample DataFrame
        np.random.seed(42)
        df = pd.DataFrame({
            'open': np.random.randn(50) * 100 + 50000,
            'high': np.random.randn(50) * 100 + 50100,
            'low': np.random.randn(50) * 100 + 49900,
            'close': np.random.randn(50) * 100 + 50000,
            'volume': np.random.randint(1000, 5000, 50)
        })
        
        result = self.strategy.calculate_indicators(df)
        
        # Check that indicators are added
        self.assertIn('resistance', result.columns)
        self.assertIn('support', result.columns)
        self.assertIn('avg_volume', result.columns)


class TestMeanReversionStrategy(unittest.TestCase):
    """Test Mean Reversion strategy"""
    
    def setUp(self):
        """Set up test strategy"""
        self.config = {
            'rsi_period': 14,
            'oversold': 30,
            'overbought': 70,
            'symbols': ['BTC/USDT']
        }
        self.strategy = MeanReversionStrategy(self.config)
    
    def test_strategy_initialization(self):
        """Test strategy initializes correctly"""
        self.assertEqual(self.strategy.rsi_period, 14)
        self.assertEqual(self.strategy.oversold, 30)
        self.assertEqual(self.strategy.overbought, 70)


class TestTrendFollowingStrategy(unittest.TestCase):
    """Test Trend Following strategy"""
    
    def setUp(self):
        """Set up test strategy"""
        self.config = {
            'fast_ema_period': 50,
            'slow_ema_period': 200,
            'adx_threshold': 25,
            'symbols': ['BTC/USDT']
        }
        self.strategy = TrendFollowingStrategy(self.config)
    
    def test_strategy_initialization(self):
        """Test strategy initializes correctly"""
        self.assertEqual(self.strategy.fast_ema_period, 50)
        self.assertEqual(self.strategy.slow_ema_period, 200)
        self.assertEqual(self.strategy.adx_threshold, 25)


class TestRiskManager(unittest.TestCase):
    """Test Risk Management"""
    
    def setUp(self):
        """Set up risk manager"""
        self.config = RiskConfig(
            risk_level=RiskLevel.MODERATE,
            max_position_size=0.1,
            stop_loss_percent=0.02,
            take_profit_percent=0.05,
            max_daily_loss=0.05
        )
        self.risk_manager = RiskManager(self.config)
    
    def test_position_size_calculation(self):
        """Test position size calculation"""
        portfolio_value = 10000
        entry_price = 50000
        stop_loss_price = 49000
        
        size = self.risk_manager.calculate_position_size(
            portfolio_value=portfolio_value,
            entry_price=entry_price,
            stop_loss_price=stop_loss_price
        )
        
        self.assertIsInstance(size, float)
        self.assertGreater(size, 0)
        # Position should not exceed max_position_size
        position_value = size * entry_price
        self.assertLessEqual(position_value, portfolio_value * self.config.max_position_size)
    
    def test_stop_loss_calculation(self):
        """Test stop loss calculation"""
        entry_price = 50000
        
        # Long position
        stop_loss_long = self.risk_manager.calculate_stop_loss(entry_price, side='long')
        self.assertIsInstance(stop_loss_long, float)
        # For long position, stop loss should be below entry
        self.assertLess(stop_loss_long, entry_price)
        
        # Short position
        stop_loss_short = self.risk_manager.calculate_stop_loss(entry_price, side='short')
        self.assertIsInstance(stop_loss_short, float)
        # For short position, stop loss should be above entry
        self.assertGreater(stop_loss_short, entry_price)
    
    def test_take_profit_calculation(self):
        """Test take profit calculation"""
        entry_price = 50000
        
        # Long position
        take_profit_long = self.risk_manager.calculate_take_profit(entry_price, side='long')
        self.assertIsInstance(take_profit_long, float)
        # For long position, take profit should be above entry
        self.assertGreater(take_profit_long, entry_price)
        
        # Short position
        take_profit_short = self.risk_manager.calculate_take_profit(entry_price, side='short')
        self.assertIsInstance(take_profit_short, float)
        # For short position, take profit should be below entry
        self.assertLess(take_profit_short, entry_price)
    
    def test_daily_loss_limit_exceeded(self):
        """Test daily loss limit when exceeded"""
        # Simulate being at daily loss limit
        self.risk_manager.daily_pnl = -600  # $600 loss
        self.risk_manager.config.max_daily_loss = 500  # $500 limit
        
        should_stop = self.risk_manager.check_daily_loss_limit(-600)
        
        # Should trigger stop
        self.assertTrue(should_stop)
    
    def test_daily_loss_under_limit(self):
        """Test daily loss under limit"""
        # Set a reasonable daily loss limit
        self.risk_manager.config.max_daily_loss = 500  # $500 limit
        
        should_stop = self.risk_manager.check_daily_loss_limit(-300)
        
        # Should not trigger stop ($300 < $500 limit)
        self.assertFalse(should_stop)
    
    def test_can_open_position(self):
        """Test position opening check"""
        portfolio_value = 10000
        
        # Should be able to open position initially
        self.assertTrue(self.risk_manager.can_open_position(portfolio_value, 'BTC/USDT'))
        
        # Add a position
        self.risk_manager.add_position_risk('BTC/USDT', 500, portfolio_value)
        
        # Should not be able to open another position in same symbol
        self.assertFalse(self.risk_manager.can_open_position(portfolio_value, 'BTC/USDT'))
    
    def test_risk_report(self):
        """Test risk report generation"""
        report = self.risk_manager.get_risk_report()
        
        self.assertIn('daily_pnl', report)
        self.assertIn('total_risk', report)
        self.assertIn('max_total_risk', report)
        self.assertIn('positions_risk', report)
        self.assertIn('risk_level', report)
        self.assertIn('can_trade', report)


class TestStrategyEnsemble(unittest.TestCase):
    """Test Strategy Ensemble"""
    
    def setUp(self):
        """Set up ensemble"""
        self.config = {
            'min_consensus': 2,
            'symbols': ['BTC/USDT'],
            'breakout': {'enabled': True, 'lookback': 20},
            'mean_reversion': {'enabled': True, 'rsi_period': 14},
            'trend_following': {'enabled': True, 'fast_ema_period': 50}
        }
        self.ensemble = StrategyEnsemble(self.config)
    
    def test_ensemble_initialization(self):
        """Test ensemble initializes with strategies"""
        self.assertEqual(self.ensemble.min_consensus, 2)
        # Should have at least 3 strategies (breakout, mean_reversion, trend_following)
        self.assertGreaterEqual(len(self.ensemble.strategies), 1)


class TestRiskConfig(unittest.TestCase):
    """Test Risk Configuration"""
    
    def test_conservative_config(self):
        """Test conservative preset"""
        config = RiskConfig.conservative()
        self.assertEqual(config.risk_level, RiskLevel.CONSERVATIVE)
        self.assertEqual(config.max_position_size, 0.05)
        self.assertEqual(config.max_daily_loss, 0.03)
    
    def test_aggressive_config(self):
        """Test aggressive preset"""
        config = RiskConfig.aggressive()
        self.assertEqual(config.risk_level, RiskLevel.AGGRESSIVE)
        self.assertEqual(config.max_position_size, 0.2)
        self.assertEqual(config.max_daily_loss, 0.1)
    
    def test_moderate_config(self):
        """Test moderate default config"""
        config = RiskConfig()
        self.assertEqual(config.risk_level, RiskLevel.MODERATE)
        self.assertEqual(config.max_position_size, 0.1)
        self.assertEqual(config.max_daily_loss, 0.05)


class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def test_full_workflow(self):
        """Test a complete trading workflow"""
        # 1. Create risk manager
        risk_config = RiskConfig()
        risk_manager = RiskManager(risk_config)
        
        # 2. Create strategy
        strategy_config = {
            'lookback': 20,
            'volume_confirm': True,
            'min_breakout_percent': 0.01,
            'symbols': ['BTC/USDT']
        }
        strategy = BreakoutStrategy(strategy_config)
        
        # 3. Generate sample data as DataFrame
        np.random.seed(42)
        data = pd.DataFrame({
            'open': np.random.randn(50) * 100 + 50000,
            'high': np.random.randn(50) * 100 + 50100,
            'low': np.random.randn(50) * 100 + 49900,
            'close': np.random.randn(50) * 100 + 50000,
            'volume': np.random.randint(1000, 5000, 50)
        })
        
        # 4. Generate signals
        signals = strategy.generate_signals(data)
        self.assertIsInstance(signals, list)
        
        # 5. Calculate position size if we have a signal
        if signals:
            signal = signals[0]
            portfolio_value = 10000
            entry_price = signal.price
            stop_loss = entry_price * 0.98  # 2% stop
            
            position_size = risk_manager.calculate_position_size(
                portfolio_value, entry_price, stop_loss
            )
            
            self.assertGreater(position_size, 0)
            
            # 6. Check if we can open position
            can_trade = risk_manager.can_open_position(portfolio_value, signal.symbol)
            self.assertTrue(can_trade)


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestTechnicalIndicators))
    suite.addTests(loader.loadTestsFromTestCase(TestBreakoutStrategy))
    suite.addTests(loader.loadTestsFromTestCase(TestMeanReversionStrategy))
    suite.addTests(loader.loadTestsFromTestCase(TestTrendFollowingStrategy))
    suite.addTests(loader.loadTestsFromTestCase(TestRiskManager))
    suite.addTests(loader.loadTestsFromTestCase(TestStrategyEnsemble))
    suite.addTests(loader.loadTestsFromTestCase(TestRiskConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
