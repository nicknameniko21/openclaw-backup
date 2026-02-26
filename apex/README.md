# Apex Trading System
## Automated Cryptocurrency Trading Framework

---

## Quick Start

```bash
# Install dependencies
pip install -r apex/requirements.txt

# Check system status
python apex/main.py status

# Run backtest with ML strategy (requires more data)
python apex/main.py backtest --strategy ml --days 90

# Run backtest with trend following
python apex/main.py backtest --strategy trend_following --days 30

# Run backtest with ensemble (consensus) strategy
python apex/main.py backtest --strategy ensemble --days 60

# Run paper trading with multi-timeframe analysis
python apex/main.py paper --strategy multi_timeframe --symbol ETH/USDT
```

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    APEX TRADING SYSTEM                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   TRADING    │    │   ANALYSIS   │    │  EXECUTION   │  │
│  │              │    │              │    │              │  │
│  │ - Strategies │◄──►│ - Indicators │◄──►│ - Orders     │  │
│  │ - Signals    │    │ - Patterns   │    │ - Positions  │  │
│  │ - Risk Mgmt  │    │ - ML Models  │    │ - Exchanges  │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│          │                   │                   │          │
│          └───────────────────┼───────────────────┘          │
│                              ▼                              │
│                    ┌──────────────────┐                     │
│                    │      LOGS        │                     │
│                    │                  │                     │
│                    │ - Trades         │                     │
│                    │ - Performance    │                     │
│                    │ - Errors         │                     │
│                    └──────────────────┘                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
apex/
├── main.py                  # Unified CLI entry point
├── backtest.py              # Backtesting engine
├── requirements.txt         # Python dependencies
├── config.json              # Configuration file
├── trading/                 # Trading strategies and signals
│   ├── strategies/
│   │   ├── base.py          # Base strategy class
│   │   ├── breakout.py      # Breakout strategy
│   │   └── mean_reversion.py
│   └── risk/
│       └── manager.py       # Risk management
├── analysis/                # Technical analysis
│   └── indicators/
│       └── technical.py     # Technical indicators
├── execution/               # Order execution
│   ├── exchanges/
│   │   └── binance.py       # Binance connector
│   ├── orders/
│   │   └── manager.py
│   └── positions/
│       └── tracker.py
└── logs/                    # Trading logs
```

---

## Commands

### Status
```bash
python apex/main.py status
```
Shows system configuration, enabled strategies, and file status.

### Backtest
```bash
python apex/main.py backtest --strategy breakout --symbol BTC/USDT --days 30 --capital 10000
```

**Options:**
- `--strategy`: breakout, mean_reversion
- `--symbol`: Trading pair (default: BTC/USDT)
- `--timeframe`: 1m, 5m, 15m, 1h, 4h, 1d (default: 1h)
- `--days`: Number of days to backtest (default: 30)
- `--capital`: Initial capital (default: 10000)
- `--output`: Results file path (default: apex/logs/backtest_results.json)

### Paper Trading
```bash
python apex/main.py paper --strategy breakout --symbol BTC/USDT --timeframe 1h
```
Runs strategy in real-time with mock data (no real money).

### Live Trading ⚠️
```bash
python apex/main.py live --strategy breakout --risk conservative --confirm
```
**Requires:**
- `--confirm` flag
- Type 'LIVE' when prompted
- Valid API keys in environment variables

---

## Configuration

Edit `apex/config.json`:

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
      "symbols": ["BTC/USDT"],
      "lookback": 20,
      "volume_confirm": true,
      "min_breakout_percent": 0.01
    },
    "mean_reversion": {
      "enabled": false,
      "timeframe": "15m",
      "rsi_period": 14,
      "oversold": 30,
      "overbought": 70
    }
  },
  "exchanges": {
    "binance": {
      "enabled": true,
      "testnet": true
    }
  }
}
```

### API Keys

```bash
# Add to ~/.bashrc or ~/.zshrc
export BINANCE_API_KEY="your_key"
export BINANCE_SECRET="your_secret"
```

---

## Available Strategies

### 1. Breakout Strategy
- **Type:** Trend following
- **Logic:** Enters when price breaks above resistance or below support
- **Best for:** Trending markets
- **Config:** `lookback`, `volume_confirm`, `min_breakout_percent`

### 2. Mean Reversion Strategy
- **Type:** Counter-trend
- **Logic:** Enters when RSI indicates oversold/overbought conditions
- **Best for:** Ranging markets
- **Config:** `rsi_period`, `oversold`, `overbought`

### 3. Trend Following Strategy
- **Type:** Trend following
- **Logic:** Uses EMA50/EMA200 crossover with ADX confirmation
- **Best for:** Strong trending markets
- **Config:** `fast_ema_period`, `slow_ema_period`, `adx_threshold`

### 4. Multi-Timeframe Strategy
- **Type:** Confluence analysis
- **Logic:** Analyzes multiple timeframes for signal alignment
- **Best for:** High-confidence entries
- **Config:** `timeframes`, `ema_period`, `rsi_period`

### 5. Ensemble Strategy
- **Type:** Consensus-based
- **Logic:** Combines multiple strategies, requires minimum consensus
- **Best for:** Reducing false signals
- **Config:** `min_consensus`, sub-strategy settings

### 6. ML Strategy (Machine Learning)
- **Type:** AI-powered prediction
- **Logic:** Uses Random Forest to predict price movements based on 50+ features
- **Best for:** Adapting to changing market conditions
- **Config:** `prediction_threshold`, `min_confidence`, `n_estimators`, `use_regime_filter`
- **Features:** Price returns, moving averages, volatility, RSI, MACD, Bollinger Bands, volume patterns, candlestick patterns
- **Auto-trains:** Yes, on first run with sufficient data (default: 500 samples)

---

## Technical Indicators

All strategies have access to:

| Indicator | Function | Description |
|-----------|----------|-------------|
| SMA | `calculate_sma()` | Simple Moving Average |
| EMA | `calculate_ema()` | Exponential Moving Average |
| RSI | `calculate_rsi()` | Relative Strength Index |
| MACD | `calculate_macd()` | Moving Average Convergence Divergence |
| Bollinger Bands | `calculate_bollinger_bands()` | Volatility bands |
| ATR | `calculate_atr()` | Average True Range |
| Stochastic | `calculate_stochastic()` | Stochastic oscillator |
| ADX | `calculate_adx()` | Average Directional Index |
| OBV | `calculate_obv()` | On-Balance Volume |
| VWAP | `calculate_vwap()` | Volume Weighted Average Price |

---

## Risk Management

### Position Sizing
- Conservative: 5% max per position
- Moderate: 10% max per position
- Aggressive: 20% max per position

### Stop Loss / Take Profit
- Configurable percentages per strategy
- Automatic calculation based on entry price

### Daily Loss Limits
- Trading stops when daily loss limit reached
- Prevents emotional revenge trading

---

## Backtest Results

Example output:

```
============================================================
BACKTEST RESULTS: BreakoutStrategy
============================================================
Symbol: BTC/USDT
Timeframe: 1h
Period: 2025-01-27 to 2025-02-26
------------------------------------------------------------
Initial Capital: $10,000.00
Final Capital:   $10,847.32
Total P&L:       $847.32 (8.47%)
------------------------------------------------------------
Total Trades:    23
Winning Trades:  14
Losing Trades:   9
Win Rate:        60.87%
------------------------------------------------------------
Avg Profit:      $142.50
Avg Loss:        -$87.33
Profit Factor:   1.82
------------------------------------------------------------
Max Drawdown:    $234.56 (2.35%)
Sharpe Ratio:    1.45
============================================================
```

---

## Development Roadmap

### Phase 1: Foundation ✅ COMPLETE
- [x] Directory structure
- [x] Base strategy class
- [x] Breakout strategy
- [x] Mean reversion strategy
- [x] Technical indicators library
- [x] Binance connector
- [x] Risk management system
- [x] Backtesting engine
- [x] Unified CLI interface

### Phase 2: Advanced Strategies ✅ COMPLETE
- [x] Trend following strategy
- [x] Multi-timeframe analysis
- [x] Strategy combination/ensemble
- [ ] Arbitrage detection

### Phase 3: Machine Learning ✅ COMPLETE
- [x] Price prediction models (Random Forest, Gradient Boosting)
- [x] Classification models (up/down/neutral prediction)
- [x] Anomaly detection (price spikes, volume spikes, regime changes)
- [x] Feature engineering (50+ technical features)
- [x] ML Strategy integration
- [x] Market regime detection

### Phase 4: Execution Enhancements
- [ ] Multiple exchange support
- [ ] Smart order routing
- [ ] Latency optimization
- [ ] Order book analysis

### Phase 5: Automation & Monitoring
- [ ] Cron scheduling
- [ ] Telegram/Discord alerts
- [ ] Performance dashboard
- [ ] Real-time monitoring

---

## Safety First

⚠️ **WARNING:** Trading cryptocurrencies involves significant risk. Never trade with money you cannot afford to lose.

### Before Live Trading:
1. ✅ Test thoroughly with backtests
2. ✅ Run paper trading for at least 1 month
3. ✅ Start with small amounts
4. ✅ Set strict stop losses
5. ✅ Have an exit strategy
6. ✅ Never risk more than 2% per trade

### Golden Rules:
- **Start small** - Test with minimal capital first
- **Use stop losses** - Always protect your downside
- **Diversify** - Don't put all capital in one trade
- **Stay disciplined** - Follow your strategy, not emotions
- **Monitor continuously** - Markets move fast

---

## Troubleshooting

### Import Errors
```bash
# Make sure you're in the workspace root
cd /root/.openclaw/workspace
python apex/main.py status
```

### Missing Dependencies
```bash
pip install -r apex/requirements.txt
```

### Mock Mode
If `ccxt` is not installed, the Binance connector runs in mock mode with simulated data.

---

## For Developers

### Creating a New Strategy

1. Create file in `apex/trading/strategies/`
2. Inherit from `BaseStrategy`
3. Implement `calculate_indicators()` and `generate_signals()`

```python
from .base import BaseStrategy, Signal, SignalType

class MyStrategy(BaseStrategy):
    def calculate_indicators(self, data):
        # Add your indicators
        data['my_indicator'] = ...
        return data
    
    def generate_signals(self, data):
        # Generate signals
        if condition:
            return [Signal(...)]
        return []
```

---

## Machine Learning Features

### Feature Engineering (`apex/analysis/ml/features.py`)
The system automatically creates 50+ features from price data:

**Price Features:**
- Returns (1d, 3d, 5d, 10d, 20d)
- Log returns
- Price momentum

**Moving Average Features:**
- SMA/EMA ratios (5, 10, 20, 50, 200 periods)
- Golden cross detection
- Price distance from MAs

**Volatility Features:**
- Rolling volatility (5d, 10d, 20d)
- True Range / ATR
- Volatility regime detection

**Technical Indicators:**
- RSI with oversold/overbought signals
- MACD with crossover detection
- Bollinger Bands with position and squeeze detection

**Volume Features:**
- Volume ratios and trends
- Volume-price divergence
- On-Balance Volume (OBV)

**Candlestick Patterns:**
- Doji, Hammer, Shooting Star detection
- Bullish/Bearish engulfing patterns
- Body size and shadow analysis

### Prediction Models (`apex/analysis/ml/models.py`)

**Random Forest Model:**
- Classification (predict up/down/neutral)
- Regression (predict future return)
- Feature importance analysis
- Cross-validation scoring

**Gradient Boosting Model:**
- Often more accurate than Random Forest
- Better for capturing complex patterns

**Ensemble Model:**
- Combines multiple models
- Weighted predictions for robustness

### Anomaly Detection (`apex/analysis/ml/anomaly.py`)

**Detects:**
- Price spikes (z-score based)
- Volume spikes
- Volatility regime changes
- Unusual candlestick patterns

**Market Regime Detection:**
- Strong uptrend/downtrend
- Weak trends
- Ranging markets
- High volatility periods

### ML Strategy Configuration

```json
{
  "strategies": {
    "ml": {
      "enabled": true,
      "min_confidence": 0.55,
      "prediction_threshold": 0.6,
      "n_estimators": 100,
      "max_depth": 10,
      "use_regime_filter": true,
      "use_anomaly_filter": true,
      "prediction_horizon": 5,
      "return_threshold": 0.01,
      "training_data_size": 500
    }
  }
}
```

---

*Created: February 26, 2026*
*For: Rhuam - The Shirtless Men Army*
*Status: Phase 3 Complete - ML Capabilities Added*
