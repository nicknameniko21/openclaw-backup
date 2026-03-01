# Order Execution

This directory contains order execution and exchange connectivity.

## Exchange Connectors

### Binance (`exchanges/binance.py`)

Features:
- OHLCV data fetching
- Order placement/cancellation
- Balance tracking
- Testnet support

Usage:

```python
from execution.exchanges.binance import BinanceConnector

# Initialize (uses environment variables for API keys)
exchange = BinanceConnector(testnet=True)

# Fetch data
data = exchange.fetch_ohlcv('BTC/USDT', timeframe='1h', limit=100)

# Check balance
balances = exchange.fetch_balance()

# Place order
order = exchange.create_order(
    symbol='BTC/USDT',
    side='buy',
    type_='market',
    amount=0.01
)
```

## Order Management (`orders/manager.py`)

Features:
- Order lifecycle tracking
- Status updates
- Order history
- Persistence

## Position Tracking (`positions/tracker.py`)

Features:
- Position management
- P&L calculation
- Stop loss / take profit monitoring
- Portfolio tracking

## Safety

⚠️ **Always use testnet first!**

1. Start with `testnet=True`
2. Test all functionality
3. Only then switch to live trading
4. Never risk more than you can afford to lose
