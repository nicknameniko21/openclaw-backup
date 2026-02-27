# Apex Trading System - API Documentation

## Overview

The Apex Trading System provides a comprehensive framework for automated cryptocurrency trading with support for backtesting, paper trading, and live trading.

## Modules

### 1. Trading Module (`trading/`)

#### Strategies (`trading/strategies/`)

**Base Strategy Class**
```python
from trading.strategies.base import BaseStrategy

class MyStrategy(BaseStrategy):
    def generate_signal(self, data: List[Dict]) -> Dict:
        # Implement signal generation logic
        return {
            'signal': 'BUY' | 'SELL' | 'NEUTRAL',
            'confidence': float,
            'metadata': Dict
        }
```

**Available Strategies:**

1. **BreakoutStrategy** - Identifies price breakouts from consolidation ranges
   - Config: `lookback`, `volume_confirm`, `min_breakout_percent`

2. **MeanReversionStrategy** - Trades price reversions to mean
   - Config: `rsi_period`, `oversold`, `overbought`

3. **TrendFollowingStrategy** - Follows established trends
   - Config: `fast_ema_period`, `slow_ema_period`, `adx_threshold`

4. **MultiTimeframeStrategy** - Analyzes multiple timeframes
   - Config: `timeframes`, `ema_period`, `rsi_period`

5. **StrategyEnsemble** - Combines multiple strategies
   - Config: `min_consensus`, strategy-specific configs

6. **MLStrategy** - Machine learning based predictions
   - Config: `min_confidence`, `n_estimators`, `use_regime_filter`

#### Risk Management (`trading/risk/`)

```python
from trading.risk.manager import RiskManager, RiskConfig, RiskLevel

config = RiskConfig(
    risk_level=RiskLevel.MODERATE,  # CONSERVATIVE, MODERATE, AGGRESSIVE
    max_position_size=0.1,          # 10% of account
    stop_loss_percent=0.02,         # 2% stop loss
    take_profit_percent=0.05,       # 5% take profit
    max_daily_loss=0.05             # 5% max daily loss
)

risk_manager = RiskManager(config)

# Calculate position size
size = risk_manager.calculate_position_size(
    account_value=10000,
    entry_price=50000,
    stop_loss=49000
)
```

### 2. Analysis Module (`analysis/`)

#### Technical Indicators (`analysis/indicators/`)

```python
from analysis.indicators.technical import TechnicalIndicators

# Simple Moving Average
sma = TechnicalIndicators.sma(data, period=20)

# Exponential Moving Average
ema = TechnicalIndicators.ema(data, period=20)

# Relative Strength Index
rsi = TechnicalIndicators.rsi(data, period=14)

# Bollinger Bands
bb = TechnicalIndicators.bollinger_bands(data, period=20, std_dev=2)

# MACD
macd = TechnicalIndicators.macd(data, fast=12, slow=26, signal=9)

# Average True Range
atr = TechnicalIndicators.atr(data, period=14)

# Volume Profile
vp = TechnicalIndicators.volume_profile(data, bins=20)
```

#### Machine Learning (`analysis/ml/`)

```python
from analysis.ml.models import MLModel
from analysis.ml.features import FeatureEngineering
from analysis.ml.anomaly import AnomalyDetector

# Feature engineering
features = FeatureEngineering.create_features(data)

# Train model
model = MLModel(n_estimators=100, max_depth=10)
model.train(features, labels)

# Predict
prediction = model.predict(features)
confidence = model.get_confidence(features)

# Anomaly detection
detector = AnomalyDetector(contamination=0.01)
anomalies = detector.detect(features)
```

### 3. Execution Module (`execution/`)

#### Exchange Connectors (`execution/exchanges/`)

```python
from execution.exchanges.binance import BinanceConnector
from execution.exchanges.coinbase import CoinbaseConnector
from execution.exchanges.kraken import KrakenConnector

# Initialize connector
binance = BinanceConnector(
    api_key='your_key',
    api_secret='your_secret',
    testnet=True
)

# Get balance
balance = binance.get_balance()

# Place order
order = binance.place_market_order(
    symbol='BTC/USDT',
    side='buy',
    amount=0.001
)

# Get order status
status = binance.get_order_status(order_id)
```

#### Order Management (`execution/orders/`)

```python
from execution.orders.manager import OrderManager
from execution.orders.advanced import AdvancedOrderManager
from execution.orders.algorithms import ExecutionEngine, AlgoType

# Advanced orders
adv_orders = AdvancedOrderManager(exchange_connector)

# Iceberg order
iceberg = adv_orders.place_iceberg_order(
    symbol='BTC/USDT',
    side='buy',
    total_amount=1.0,
    display_size=0.1,
    price=50000
)

# Trailing stop
trailing = adv_orders.place_trailing_stop(
    symbol='BTC/USDT',
    side='sell',
    amount=0.5,
    trail_percent=2.0
)

# Execution algorithms
engine = ExecutionEngine(exchange_connector)

# TWAP execution
twap_orders = engine.execute_twap(
    symbol='BTC/USDT',
    side='buy',
    total_quantity=1.0,
    num_slices=10,
    duration_minutes=60
)
```

#### Smart Order Routing (`execution/routing.py`)

```python
from execution.routing import SmartOrderRouter

router = SmartOrderRouter(exchange_manager)

# Route order to best exchange
route = router.route_order(
    symbol='BTC/USDT',
    side='buy',
    amount=0.1,
    priority='price'  # 'price', 'fees', 'speed', 'liquidity', 'reliability'
)

# Check for arbitrage opportunities
arbitrage = router.check_arbitrage('BTC/USDT', min_profit_pct=0.1)
```

### 4. Automation Module (`automation/`)

#### Alerts (`automation/alerts.py`)

```python
from automation.alerts import AlertManager

alerts = AlertManager()

# Configure channels
alerts.configure_telegram(bot_token='xxx', chat_id='xxx')
alerts.configure_discord(webhook_url='xxx')

# Send alert
alerts.send_alert(
    level='INFO',  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    title='Trade Executed',
    message='Bought 0.1 BTC at $50,000',
    channels=['telegram', 'discord']
)

# Schedule recurring checks
alerts.schedule_price_alert(
    symbol='BTC/USDT',
    condition='above',
    price=60000,
    message='BTC broke $60k!'
)
```

#### Dashboard (`automation/dashboard.py`)

```python
from automation.dashboard import DashboardGenerator

dashboard = DashboardGenerator()

# Generate HTML dashboard
dashboard.generate(
    output_path='apex/dashboard.html',
    include_charts=True,
    include_performance=True
)
```

#### Scheduler (`automation/scheduler.py`)

```python
from automation.scheduler import TradingScheduler

scheduler = TradingScheduler()

# Schedule strategy execution
scheduler.schedule_strategy(
    strategy_name='breakout',
    cron_expression='0 */4 * * *',  # Every 4 hours
    symbols=['BTC/USDT', 'ETH/USDT']
)

# Schedule backtest
scheduler.schedule_backtest(
    cron_expression='0 0 * * 0',  # Weekly on Sunday
    strategy='ensemble',
    days=90
)
```

## Configuration

### Full Configuration Example

```json
{
  "risk_management": {
    "risk_level": "moderate",
    "max_position_size": 0.1,
    "stop_loss_percent": 0.02,
    "take_profit_percent": 0.05,
    "max_daily_loss": 0.05
  },
  "strategies": {
    "breakout": {
      "enabled": true,
      "timeframe": "1h",
      "symbols": ["BTC/USDT", "ETH/USDT"],
      "lookback": 20,
      "volume_confirm": true,
      "min_breakout_percent": 0.01
    },
    "ml": {
      "enabled": false,
      "timeframe": "1h",
      "symbols": ["BTC/USDT", "ETH/USDT"],
      "min_confidence": 0.55,
      "n_estimators": 100,
      "max_depth": 10,
      "use_regime_filter": true,
      "use_anomaly_filter": true
    }
  },
  "exchanges": {
    "binance": {
      "enabled": true,
      "testnet": true,
      "rate_limit": true,
      "priority": 1
    }
  },
  "routing": {
    "enabled": true,
    "default_priority": "price",
    "arbitrage_min_profit_pct": 0.1,
    "failover_enabled": true
  },
  "logging": {
    "level": "INFO",
    "file": "apex/logs/trading.log",
    "max_size_mb": 100,
    "backup_count": 5
  },
  "backtest": {
    "initial_capital": 10000,
    "commission": 0.001,
    "slippage": 0.001
  }
}
```

## CLI Usage

### Status Check
```bash
python apex/main.py status
```

### Backtesting
```bash
# Basic backtest
python apex/main.py backtest --strategy breakout --days 30

# With custom parameters
python apex/main.py backtest \\
    --strategy trend_following \\
    --symbol ETH/USDT \\
    --days 60 \\
    --capital 50000

# ML strategy (requires more data)
python apex/main.py backtest --strategy ml --days 90
```

### Paper Trading
```bash
python apex/main.py paper --strategy multi_timeframe --symbol BTC/USDT
```

### Live Trading (Use with caution!)
```bash
python apex/main.py live --strategy ensemble --confirm
```

## Testing

Run the test suite:

```bash
python apex/tests.py
```

Run specific test class:

```bash
python -m unittest apex.tests.TestRiskManager
```

## Best Practices

1. **Always backtest first** - Test strategies on historical data before live trading
2. **Start with paper trading** - Validate in real-time without risk
3. **Use proper risk management** - Never risk more than you can afford to lose
4. **Monitor regularly** - Set up alerts and dashboards
5. **Keep logs** - Review trades and performance regularly
6. **Test in testnet** - Use exchange testnets for initial live testing

## Safety Warnings

- **Never** trade with money you cannot afford to lose
- **Always** use testnet/paper trading first
- **Verify** all API keys have appropriate permissions
- **Monitor** positions and set stop losses
- **Review** code before running live trading
- **Backup** configuration and API keys securely

## Support

For issues or questions:
1. Check the logs in `apex/logs/`
2. Review the test suite output
3. Verify configuration in `config.json`
4. Ensure all dependencies are installed
