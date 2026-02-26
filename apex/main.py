"""
Apex Trading System - Main Entry Point
Unified interface for backtesting, paper trading, and live trading.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from trading.strategies.breakout import BreakoutStrategy
from trading.strategies.mean_reversion import MeanReversionStrategy
from trading.strategies.trend_following import TrendFollowingStrategy
from trading.strategies.multi_timeframe import MultiTimeframeStrategy
from trading.strategies.ensemble import StrategyEnsemble
from trading.risk.manager import RiskManager, RiskConfig, RiskLevel
from execution.exchanges.binance import BinanceConnector
from backtest import run_backtest


def load_config(config_path: str = 'apex/config.json') -> Dict:
    """Load configuration from JSON file"""
    default_config = {
        'risk_management': {
            'risk_level': 'moderate',
            'max_position_size': 0.1,
            'stop_loss_percent': 0.02,
            'take_profit_percent': 0.05,
            'max_daily_loss': 0.05
        },
        'strategies': {
            'breakout': {
                'enabled': True,
                'timeframe': '1h',
                'symbols': ['BTC/USDT'],
                'lookback': 20,
                'volume_confirm': True,
                'min_breakout_percent': 0.01
            },
            'mean_reversion': {
                'enabled': False,
                'timeframe': '15m',
                'symbols': ['BTC/USDT'],
                'rsi_period': 14,
                'oversold': 30,
                'overbought': 70
            }
        },
        'exchanges': {
            'binance': {
                'enabled': True,
                'testnet': True,
                'api_key_env': 'BINANCE_API_KEY',
                'api_secret_env': 'BINANCE_SECRET'
            }
        },
        'trading': {
            'initial_capital': 10000.0,
            'commission': 0.001,
            'slippage': 0.0005
        }
    }
    
    if Path(config_path).exists():
        with open(config_path, 'r') as f:
            return json.load(f)
    
    # Create default config file
    Path(config_path).parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w') as f:
        json.dump(default_config, f, indent=2)
    
    print(f"Created default config at {config_path}")
    return default_config


def create_strategy(strategy_name: str, config: Dict):
    """Create strategy instance by name"""
    strategies_config = config.get('strategies', {})

    if strategy_name == 'breakout':
        strategy_config = strategies_config.get('breakout', {})
        return BreakoutStrategy(strategy_config)

    elif strategy_name == 'mean_reversion':
        strategy_config = strategies_config.get('mean_reversion', {})
        return MeanReversionStrategy(strategy_config)

    elif strategy_name == 'trend_following':
        strategy_config = strategies_config.get('trend_following', {})
        return TrendFollowingStrategy(strategy_config)

    elif strategy_name == 'multi_timeframe':
        strategy_config = strategies_config.get('multi_timeframe', {})
        return MultiTimeframeStrategy(strategy_config)

    elif strategy_name == 'ensemble':
        strategy_config = strategies_config.get('ensemble', {})
        return StrategyEnsemble(strategy_config)

    else:
        raise ValueError(f"Unknown strategy: {strategy_name}")


def cmd_backtest(args, config: Dict):
    """Run backtest command"""
    print(f"\n{'='*60}")
    print(f"APEX BACKTEST - {args.strategy.upper()}")
    print('='*60)
    
    # Create strategy
    strategy = create_strategy(args.strategy, config)
    
    # Run backtest
    result = run_backtest(
        strategy=strategy,
        symbol=args.symbol,
        timeframe=args.timeframe,
        days=args.days,
        initial_capital=args.capital
    )
    
    # Save results
    if result and args.output:
        result.save_results(result, args.output)
    
    return result


def cmd_paper(args, config: Dict):
    """Run paper trading command"""
    print(f"\n{'='*60}")
    print(f"APEX PAPER TRADING - {args.strategy.upper()}")
    print('='*60)
    print("Mode: PAPER (no real money at risk)")
    print(f"Strategy: {args.strategy}")
    print(f"Symbol: {args.symbol}")
    print(f"Timeframe: {args.timeframe}")
    print('-'*60)
    
    # Create strategy
    strategy = create_strategy(args.strategy, config)
    
    # Create risk manager
    risk_config = RiskConfig(
        risk_level=RiskLevel(config['risk_management'].get('risk_level', 'moderate'))
    )
    risk_manager = RiskManager(risk_config)
    
    # Create exchange connector (always testnet for paper trading)
    exchange = BinanceConnector(testnet=True)
    
    print("\nStarting paper trading session...")
    print("Press Ctrl+C to stop\n")
    
    try:
        # Main trading loop
        while True:
            # Fetch latest data
            data = exchange.fetch_ohlcv(args.symbol, args.timeframe, limit=100)
            
            if data is not None and len(data) > 0:
                # Generate signals
                signals = strategy.generate_signals(data)
                
                # Process signals
                for signal in signals:
                    print(f"[{signal.timestamp}] {signal.type.value.upper()} signal for {signal.symbol}")
                    print(f"  Price: ${signal.price:,.2f}")
                    print(f"  Confidence: {signal.confidence:.1%}")
                    print(f"  Metadata: {signal.metadata}")
                    print()
            
            # Sleep until next candle
            import time
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        print("\n\nPaper trading session ended.")


def cmd_live(args, config: Dict):
    """Run live trading command"""
    print(f"\n{'='*60}")
    print(f"APEX LIVE TRADING - {args.strategy.upper()}")
    print('='*60)
    print("⚠️  WARNING: REAL MONEY AT RISK!")
    print('-'*60)
    
    # Safety check
    if not args.confirm:
        print("\n❌ Live trading requires --confirm flag")
        print("Please confirm you understand the risks:")
        print("  python apex/main.py live --strategy breakout --confirm")
        return
    
    # Double-check with user
    confirm = input("\nType 'LIVE' to confirm live trading with real funds: ")
    if confirm != 'LIVE':
        print("Confirmation failed. Exiting.")
        return
    
    print(f"\nStrategy: {args.strategy}")
    print(f"Symbol: {args.symbol}")
    print(f"Risk Level: {args.risk}")
    print('-'*60)
    
    # Create strategy
    strategy = create_strategy(args.strategy, config)
    
    # Create risk manager
    risk_level = RiskLevel(args.risk)
    risk_config = RiskConfig(risk_level=risk_level)
    risk_manager = RiskManager(risk_config)
    
    # Create exchange connector (live mode)
    exchange = BinanceConnector(testnet=False)
    
    print("\n⚠️  LIVE TRADING STARTED")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            # Similar to paper trading but with real orders
            data = exchange.fetch_ohlcv(args.symbol, args.timeframe, limit=100)
            
            if data is not None and len(data) > 0:
                signals = strategy.generate_signals(data)
                
                for signal in signals:
                    # Check risk management
                    if risk_manager.can_open_position(100000, signal.symbol):
                        print(f"🚀 EXECUTING {signal.type.value.upper()} ORDER")
                        print(f"   Symbol: {signal.symbol}")
                        print(f"   Price: ${signal.price:,.2f}")
                        # TODO: Execute actual order
                    else:
                        print(f"⛔ Risk management blocked {signal.type.value} signal")
            
            import time
            time.sleep(60)
            
    except KeyboardInterrupt:
        print("\n\nLive trading session ended.")


def cmd_status(args, config: Dict):
    """Show system status"""
    print(f"\n{'='*60}")
    print("APEX TRADING SYSTEM - STATUS")
    print('='*60)
    
    print("\n📊 Configuration:")
    print(f"  Risk Level: {config['risk_management'].get('risk_level', 'moderate')}")
    print(f"  Max Position Size: {config['risk_management'].get('max_position_size', 0.1):.1%}")
    print(f"  Stop Loss: {config['risk_management'].get('stop_loss_percent', 0.02):.1%}")
    print(f"  Take Profit: {config['risk_management'].get('take_profit_percent', 0.05):.1%}")
    
    print("\n🤖 Strategies:")
    for name, strat_config in config.get('strategies', {}).items():
        status = "✅ Enabled" if strat_config.get('enabled') else "❌ Disabled"
        print(f"  {name}: {status}")
    
    print("\n🏦 Exchanges:")
    for name, exch_config in config.get('exchanges', {}).items():
        testnet = "testnet" if exch_config.get('testnet') else "LIVE"
        print(f"  {name}: {testnet}")
    
    print("\n📁 Files:")
    files_to_check = [
        'apex/config.json',
        'apex/trading/strategies/base.py',
        'apex/trading/strategies/breakout.py',
        'apex/analysis/indicators/technical.py',
        'apex/execution/exchanges/binance.py',
        'apex/backtest.py'
    ]
    
    for filepath in files_to_check:
        exists = "✅" if Path(filepath).exists() else "❌"
        print(f"  {exists} {filepath}")
    
    print('\n' + '='*60)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Apex Trading System - Automated Cryptocurrency Trading',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run backtest
  python apex/main.py backtest --strategy breakout --days 30

  # Run paper trading
  python apex/main.py paper --strategy breakout --symbol BTC/USDT

  # Show system status
  python apex/main.py status

  # Run live trading (⚠️ REAL MONEY)
  python apex/main.py live --strategy breakout --risk conservative --confirm
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Backtest command
    backtest_parser = subparsers.add_parser('backtest', help='Run backtest on historical data')
    backtest_parser.add_argument('--strategy', type=str, default='breakout',
                                choices=['breakout', 'mean_reversion', 'trend_following', 'multi_timeframe', 'ensemble'],
                                help='Trading strategy to use')
    backtest_parser.add_argument('--symbol', type=str, default='BTC/USDT',
                                help='Trading pair (e.g., BTC/USDT)')
    backtest_parser.add_argument('--timeframe', type=str, default='1h',
                                help='Candle timeframe (e.g., 1h, 4h, 1d)')
    backtest_parser.add_argument('--days', type=int, default=30,
                                help='Number of days to backtest')
    backtest_parser.add_argument('--capital', type=float, default=10000.0,
                                help='Initial capital for backtest')
    backtest_parser.add_argument('--output', type=str, default='apex/logs/backtest_results.json',
                                help='Output file for results')

    # Paper trading command
    paper_parser = subparsers.add_parser('paper', help='Run paper trading simulation')
    paper_parser.add_argument('--strategy', type=str, default='breakout',
                             choices=['breakout', 'mean_reversion', 'trend_following', 'multi_timeframe', 'ensemble'],
                             help='Trading strategy to use')
    paper_parser.add_argument('--symbol', type=str, default='BTC/USDT',
                             help='Trading pair')
    paper_parser.add_argument('--timeframe', type=str, default='1h',
                             help='Candle timeframe')

    # Live trading command
    live_parser = subparsers.add_parser('live', help='Run live trading (REAL MONEY)')
    live_parser.add_argument('--strategy', type=str, default='breakout',
                            choices=['breakout', 'mean_reversion', 'trend_following', 'multi_timeframe', 'ensemble'],
                            help='Trading strategy to use')
    live_parser.add_argument('--symbol', type=str, default='BTC/USDT',
                            help='Trading pair')
    live_parser.add_argument('--risk', type=str, default='conservative',
                            choices=['conservative', 'moderate', 'aggressive'],
                            help='Risk level')
    live_parser.add_argument('--confirm', action='store_true',
                            help='Confirm live trading (required)')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show system status')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Load configuration
    config = load_config()
    
    # Execute command
    if args.command == 'backtest':
        cmd_backtest(args, config)
    elif args.command == 'paper':
        cmd_paper(args, config)
    elif args.command == 'live':
        cmd_live(args, config)
    elif args.command == 'status':
        cmd_status(args, config)


if __name__ == '__main__':
    main()
