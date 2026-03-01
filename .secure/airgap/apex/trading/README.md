# Trading Strategies

This directory contains trading strategy implementations.

## Available Strategies

### 1. Breakout Strategy (`breakout.py`)
- **Type:** Trend following
- **Logic:** Enters when price breaks above resistance or below support
- **Indicators:** Support/Resistance levels, Volume
- **Best for:** Trending markets

### 2. Mean Reversion Strategy (`mean_reversion.py`)
- **Type:** Counter-trend
- **Logic:** Enters when price deviates significantly from mean
- **Indicators:** RSI, Bollinger Bands
- **Best for:** Ranging markets

## Creating a New Strategy

1. Create a new file in `strategies/`
2. Inherit from `BaseStrategy`
3. Implement `calculate_indicators()` and `generate_signals()`

Example:

```python
from .base import BaseStrategy, Signal, SignalType

class MyStrategy(BaseStrategy):
    def __init__(self, config: dict):
        super().__init__(config)
        # Your config parameters
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        # Add your indicators
        data['my_indicator'] = ...
        return data
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        # Generate signals based on indicators
        if condition:
            return [Signal(...)]
        return []
```

## Risk Management

See `risk/manager.py` for risk management controls:
- Position sizing
- Stop loss / take profit
- Daily loss limits
- Portfolio risk monitoring
