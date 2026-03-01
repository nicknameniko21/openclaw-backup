"""
Apex Trading System - Backtesting Engine
Test trading strategies against historical data.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json

from ..trading.strategies.base import BaseStrategy, Signal, SignalType, Position
from ..trading.risk.manager import RiskManager, RiskConfig
from ..execution.exchanges.binance import BinanceConnector


@dataclass
class Trade:
    """Record of a completed trade"""
    entry_time: datetime
    exit_time: datetime
    symbol: str
    side: str
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    pnl_percent: float
    exit_reason: str  # 'stop_loss', 'take_profit', 'signal', 'end_of_data'


@dataclass
class BacktestResult:
    """Complete backtest results"""
    strategy_name: str
    symbol: str
    timeframe: str
    start_date: datetime
    end_date: datetime
    
    # Performance metrics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    
    # P&L
    total_pnl: float = 0.0
    total_pnl_percent: float = 0.0
    avg_profit: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    
    # Risk metrics
    max_drawdown: float = 0.0
    max_drawdown_percent: float = 0.0
    sharpe_ratio: float = 0.0
    
    # Equity curve
    initial_capital: float = 10000.0
    final_capital: float = 10000.0
    equity_curve: List[Dict] = field(default_factory=list)
    trades: List[Trade] = field(default_factory=list)
    
    def calculate_metrics(self):
        """Calculate all performance metrics"""
        if self.total_trades == 0:
            return
        
        self.win_rate = self.winning_trades / self.total_trades
        
        profits = [t.pnl for t in self.trades if t.pnl > 0]
        losses = [t.pnl for t in self.trades if t.pnl < 0]
        
        self.avg_profit = np.mean(profits) if profits else 0
        self.avg_loss = np.mean(losses) if losses else 0
        
        total_profits = sum(profits) if profits else 0
        total_losses = abs(sum(losses)) if losses else 0
        
        self.profit_factor = total_profits / total_losses if total_losses > 0 else float('inf')
        
        # Calculate max drawdown
        peak = self.initial_capital
        max_dd = 0
        max_dd_pct = 0
        
        for point in self.equity_curve:
            capital = point['equity']
            if capital > peak:
                peak = capital
            dd = peak - capital
            dd_pct = dd / peak
            if dd > max_dd:
                max_dd = dd
                max_dd_pct = dd_pct
        
        self.max_drawdown = max_dd
        self.max_drawdown_percent = max_dd_pct
        
        # Calculate Sharpe ratio (simplified)
        if len(self.equity_curve) > 1:
            returns = []
            for i in range(1, len(self.equity_curve)):
                prev = self.equity_curve[i-1]['equity']
                curr = self.equity_curve[i]['equity']
                returns.append((curr - prev) / prev)
            
            if len(returns) > 1 and np.std(returns) > 0:
                self.sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252)
    
    def to_dict(self) -> Dict:
        """Convert results to dictionary"""
        return {
            'strategy_name': self.strategy_name,
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'initial_capital': self.initial_capital,
            'final_capital': self.final_capital,
            'total_pnl': self.total_pnl,
            'total_pnl_percent': self.total_pnl_percent,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': self.win_rate,
            'avg_profit': self.avg_profit,
            'avg_loss': self.avg_loss,
            'profit_factor': self.profit_factor,
            'max_drawdown': self.max_drawdown,
            'max_drawdown_percent': self.max_drawdown_percent,
            'sharpe_ratio': self.sharpe_ratio,
        }
    
    def print_summary(self):
        """Print formatted backtest summary"""
        print("\n" + "="*60)
        print(f"BACKTEST RESULTS: {self.strategy_name}")
        print("="*60)
        print(f"Symbol: {self.symbol}")
        print(f"Timeframe: {self.timeframe}")
        print(f"Period: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
        print("-"*60)
        print(f"Initial Capital: ${self.initial_capital:,.2f}")
        print(f"Final Capital:   ${self.final_capital:,.2f}")
        print(f"Total P&L:       ${self.total_pnl:,.2f} ({self.total_pnl_percent:.2%})")
        print("-"*60)
        print(f"Total Trades:    {self.total_trades}")
        print(f"Winning Trades:  {self.winning_trades}")
        print(f"Losing Trades:   {self.losing_trades}")
        print(f"Win Rate:        {self.win_rate:.2%}")
        print("-"*60)
        print(f"Avg Profit:      ${self.avg_profit:,.2f}")
        print(f"Avg Loss:        ${self.avg_loss:,.2f}")
        print(f"Profit Factor:   {self.profit_factor:.2f}")
        print("-"*60)
        print(f"Max Drawdown:    ${self.max_drawdown:,.2f} ({self.max_drawdown_percent:.2%})")
        print(f"Sharpe Ratio:    {self.sharpe_ratio:.2f}")
        print("="*60)


class BacktestEngine:
    """
    Backtesting engine for trading strategies.
    
    Simulates trading on historical data with realistic execution.
    """
    
    def __init__(self, 
                 strategy: BaseStrategy,
                 initial_capital: float = 10000.0,
                 commission: float = 0.001,  # 0.1% per trade
                 slippage: float = 0.0005):  # 0.05% slippage
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        
        self.capital = initial_capital
        self.equity_curve = []
        self.trades = []
        self.current_position: Optional[Position] = None
        
    def run(self, data: pd.DataFrame, symbol: str) -> BacktestResult:
        """
        Run backtest on historical data.
        
        Args:
            data: DataFrame with OHLCV data
            symbol: Trading symbol
            
        Returns:
            BacktestResult with complete performance metrics
        """
        result = BacktestResult(
            strategy_name=self.strategy.name,
            symbol=symbol,
            timeframe=self.strategy.timeframe,
            start_date=data.index[0],
            end_date=data.index[-1],
            initial_capital=self.initial_capital
        )
        
        self.capital = self.initial_capital
        self.equity_curve = []
        self.trades = []
        self.current_position = None
        
        # Process each candle
        for i in range(len(data)):
            current_data = data.iloc[:i+1]
            current_candle = data.iloc[i]
            current_time = data.index[i]
            
            # Update equity curve
            equity = self._calculate_equity(current_candle['close'])
            self.equity_curve.append({
                'timestamp': current_time,
                'equity': equity,
                'price': current_candle['close']
            })
            
            # Check stop loss / take profit for open position
            if self.current_position:
                exit_price = None
                exit_reason = None
                
                if self.current_position.side == 'long':
                    # Check stop loss
                    if current_candle['low'] <= self.current_position.stop_loss:
                        exit_price = self.current_position.stop_loss
                        exit_reason = 'stop_loss'
                    # Check take profit
                    elif current_candle['high'] >= self.current_position.take_profit:
                        exit_price = self.current_position.take_profit
                        exit_reason = 'take_profit'
                
                if exit_price:
                    self._close_position(current_time, exit_price, exit_reason, result)
                    continue
            
            # Generate signals
            signals = self.strategy.generate_signals(current_data)
            
            for signal in signals:
                if signal.type == SignalType.BUY and not self.current_position:
                    self._open_position(signal, current_candle, 'long')
                    
                elif signal.type == SignalType.SELL and self.current_position:
                    if self.current_position.side == 'long':
                        self._close_position(
                            current_time, 
                            current_candle['close'], 
                            'signal',
                            result
                        )
        
        # Close any open position at end of data
        if self.current_position:
            final_price = data.iloc[-1]['close']
            self._close_position(
                data.index[-1],
                final_price,
                'end_of_data',
                result
            )
        
        # Populate results
        result.equity_curve = self.equity_curve
        result.trades = self.trades
        result.final_capital = self.capital
        result.total_pnl = self.capital - self.initial_capital
        result.total_pnl_percent = result.total_pnl / self.initial_capital
        result.total_trades = len(self.trades)
        result.winning_trades = len([t for t in self.trades if t.pnl > 0])
        result.losing_trades = len([t for t in self.trades if t.pnl < 0])
        
        result.calculate_metrics()
        
        return result
    
    def _open_position(self, signal: Signal, candle: pd.Series, side: str):
        """Open a new position"""
        # Apply slippage
        if side == 'long':
            entry_price = candle['close'] * (1 + self.slippage)
            stop_loss = signal.metadata.get('stop_loss', entry_price * 0.98)
            take_profit = signal.metadata.get('take_profit', entry_price * 1.05)
        else:
            entry_price = candle['close'] * (1 - self.slippage)
            stop_loss = signal.metadata.get('stop_loss', entry_price * 1.02)
            take_profit = signal.metadata.get('take_profit', entry_price * 0.95)
        
        # Calculate position size (use 95% of capital for simplicity)
        position_value = self.capital * 0.95
        quantity = position_value / entry_price
        
        self.current_position = Position(
            symbol=signal.symbol,
            side=side,
            entry_price=entry_price,
            quantity=quantity,
            timestamp=signal.timestamp,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
    
    def _close_position(self, exit_time: datetime, exit_price: float, 
                       exit_reason: str, result: BacktestResult):
        """Close the current position and record the trade"""
        if not self.current_position:
            return
        
        # Apply slippage
        if self.current_position.side == 'long':
            exit_price = exit_price * (1 - self.slippage)
        else:
            exit_price = exit_price * (1 + self.slippage)
        
        # Calculate P&L
        if self.current_position.side == 'long':
            pnl = (exit_price - self.current_position.entry_price) * self.current_position.quantity
        else:
            pnl = (self.current_position.entry_price - exit_price) * self.current_position.quantity
        
        # Apply commission (entry and exit)
        commission_cost = (self.current_position.entry_price + exit_price) * \
                         self.current_position.quantity * self.commission
        pnl -= commission_cost
        
        # Update capital
        self.capital += pnl
        
        # Calculate P&L percentage
        position_value = self.current_position.entry_price * self.current_position.quantity
        pnl_percent = pnl / position_value
        
        # Create trade record
        trade = Trade(
            entry_time=self.current_position.timestamp,
            exit_time=exit_time,
            symbol=self.current_position.symbol,
            side=self.current_position.side,
            entry_price=self.current_position.entry_price,
            exit_price=exit_price,
            quantity=self.current_position.quantity,
            pnl=pnl,
            pnl_percent=pnl_percent,
            exit_reason=exit_reason
        )
        
        self.trades.append(trade)
        self.current_position = None
    
    def _calculate_equity(self, current_price: float) -> float:
        """Calculate current equity including open position"""
        equity = self.capital
        
        if self.current_position:
            if self.current_position.side == 'long':
                unrealized_pnl = (current_price - self.current_position.entry_price) * \
                               self.current_position.quantity
            else:
                unrealized_pnl = (self.current_position.entry_price - current_price) * \
                               self.current_position.quantity
            equity += unrealized_pnl
        
        return equity
    
    def save_results(self, result: BacktestResult, filepath: str):
        """Save backtest results to JSON file"""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
        
        print(f"Results saved to {filepath}")


def run_backtest(strategy: BaseStrategy, 
                 symbol: str = 'BTC/USDT',
                 timeframe: str = '1h',
                 days: int = 30,
                 initial_capital: float = 10000.0) -> BacktestResult:
    """
    Convenience function to run a backtest.
    
    Args:
        strategy: Trading strategy instance
        symbol: Trading pair
        timeframe: Candle timeframe
        days: Number of days to backtest
        initial_capital: Starting capital
        
    Returns:
        BacktestResult
    """
    # Create exchange connector (uses mock data)
    exchange = BinanceConnector(testnet=True)
    
    # Fetch historical data
    print(f"Fetching {days} days of {timeframe} data for {symbol}...")
    data = exchange.fetch_ohlcv(symbol, timeframe, limit=days*24)
    
    if data is None or len(data) == 0:
        print("Error: Could not fetch data")
        return None
    
    print(f"Running backtest with {len(data)} candles...")
    
    # Create and run backtest engine
    engine = BacktestEngine(strategy, initial_capital=initial_capital)
    result = engine.run(data, symbol)
    
    # Print results
    result.print_summary()
    
    return result


if __name__ == '__main__':
    # Example usage
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from trading.strategies.breakout import BreakoutStrategy
    
    # Create strategy
    config = {
        'enabled': True,
        'timeframe': '1h',
        'symbols': ['BTC/USDT'],
        'lookback': 20,
        'volume_confirm': True,
        'min_breakout_percent': 0.01
    }
    
    strategy = BreakoutStrategy(config)
    
    # Run backtest
    result = run_backtest(
        strategy=strategy,
        symbol='BTC/USDT',
        timeframe='1h',
        days=30,
        initial_capital=10000.0
    )
    
    # Save results
    if result:
        result.save_results(result, 'apex/logs/backtest_results.json')
