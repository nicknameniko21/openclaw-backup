# Technical Analysis

This directory contains technical analysis tools and ML models.

## Indicators

### Technical Indicators (`indicators/technical.py`)

Available indicators:
- **SMA/EMA:** Simple and exponential moving averages
- **RSI:** Relative Strength Index
- **MACD:** Moving Average Convergence Divergence
- **Bollinger Bands:** Volatility bands
- **ATR:** Average True Range
- **Stochastic:** Stochastic oscillator
- **ADX:** Average Directional Index
- **OBV:** On-Balance Volume
- **VWAP:** Volume Weighted Average Price

Usage:

```python
from analysis.indicators.technical import calculate_rsi, calculate_macd

# Calculate RSI
rsi = calculate_rsi(data['close'], period=14)

# Calculate MACD
macd, signal, hist = calculate_macd(data['close'])

# Add all indicators at once
from analysis.indicators.technical import TechnicalIndicators
data = TechnicalIndicators.add_all_indicators(data)
```

## Pattern Recognition

Coming soon:
- Candlestick patterns
- Chart patterns
- Harmonic patterns

## Machine Learning Models

Coming soon:
- Price prediction models
- Classification models
- Anomaly detection
