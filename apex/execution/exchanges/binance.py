"""
Binance Exchange Connector
Handles all Binance API interactions.
"""

import os
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import pandas as pd

# Try to import ccxt, handle if not installed
try:
    import ccxt
    CCXT_AVAILABLE = True
except ImportError:
    CCXT_AVAILABLE = False
    logging.warning("ccxt not installed. Binance connector will use mock mode.")


@dataclass
class Order:
    """Order data structure"""
    symbol: str
    side: str  # 'buy' or 'sell'
    type: str  # 'market', 'limit', etc.
    amount: float
    price: Optional[float] = None
    order_id: Optional[str] = None
    status: str = 'pending'  # 'pending', 'open', 'closed', 'canceled'
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class Balance:
    """Account balance"""
    asset: str
    free: float
    used: float
    total: float


class BinanceConnector:
    """
    Binance exchange connector using CCXT library.
    
    Features:
    - Market data fetching
    - Order placement and management
    - Account balance tracking
    - OHLCV data retrieval
    """
    
    def __init__(self, api_key: str = None, api_secret: str = None, testnet: bool = True):
        self.logger = logging.getLogger(__name__)
        
        # Use environment variables if not provided
        self.api_key = api_key or os.getenv('BINANCE_API_KEY')
        self.api_secret = api_secret or os.getenv('BINANCE_SECRET')
        self.testnet = testnet
        
        self.exchange = None
        self.mock_mode = not CCXT_AVAILABLE
        
        if not self.mock_mode:
            self._initialize_exchange()
        else:
            self.logger.info("Running in mock mode (ccxt not available)")
    
    def _initialize_exchange(self):
        """Initialize CCXT exchange instance"""
        try:
            config = {
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'enableRateLimit': True,
            }
            
            if self.testnet:
                config['options'] = {'defaultType': 'spot'}
                self.exchange = ccxt.binance(config)
                self.exchange.set_sandbox_mode(True)
            else:
                self.exchange = ccxt.binance(config)
            
            self.logger.info(f"Binance connector initialized (testnet={self.testnet})")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Binance: {e}")
            self.mock_mode = True
    
    def fetch_ohlcv(self, symbol: str, timeframe: str = '1h', 
                    limit: int = 100) -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV data from Binance.
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Candle timeframe (e.g., '1h', '1d')
            limit: Number of candles to fetch
            
        Returns:
            DataFrame with OHLCV data or None if error
        """
        if self.mock_mode:
            return self._generate_mock_ohlcv(symbol, limit)
        
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 
                                                'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error fetching OHLCV: {e}")
            return None
    
    def fetch_balance(self) -> List[Balance]:
        """
        Fetch account balance.
        
        Returns:
            List of Balance objects
        """
        if self.mock_mode:
            return self._generate_mock_balance()
        
        try:
            balance = self.exchange.fetch_balance()
            balances = []
            
            for asset, data in balance.items():
                if isinstance(data, dict) and data.get('total', 0) > 0:
                    balances.append(Balance(
                        asset=asset,
                        free=data.get('free', 0),
                        used=data.get('used', 0),
                        total=data.get('total', 0)
                    ))
            
            return balances
            
        except Exception as e:
            self.logger.error(f"Error fetching balance: {e}")
            return []
    
    def create_order(self, symbol: str, side: str, type_: str,
                    amount: float, price: float = None) -> Optional[Order]:
        """
        Create a new order.
        
        Args:
            symbol: Trading pair
            side: 'buy' or 'sell'
            type_: 'market', 'limit', etc.
            amount: Order amount
            price: Order price (for limit orders)
            
        Returns:
            Order object or None if error
        """
        if self.mock_mode:
            return self._generate_mock_order(symbol, side, type_, amount, price)
        
        try:
            order_data = self.exchange.create_order(
                symbol, type_, side, amount, price
            )
            
            order = Order(
                symbol=symbol,
                side=side,
                type=type_,
                amount=amount,
                price=price,
                order_id=order_data.get('id'),
                status=order_data.get('status', 'open')
            )
            
            self.logger.info(f"Order created: {order.order_id}")
            return order
            
        except Exception as e:
            self.logger.error(f"Error creating order: {e}")
            return None
    
    def cancel_order(self, order_id: str, symbol: str) -> bool:
        """
        Cancel an existing order.
        
        Args:
            order_id: Order ID to cancel
            symbol: Trading pair
            
        Returns:
            True if successful
        """
        if self.mock_mode:
            return True
        
        try:
            self.exchange.cancel_order(order_id, symbol)
            self.logger.info(f"Order canceled: {order_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error canceling order: {e}")
            return False
    
    def fetch_ticker(self, symbol: str) -> Optional[Dict]:
        """
        Fetch current ticker data.
        
        Args:
            symbol: Trading pair
            
        Returns:
            Ticker data dictionary
        """
        if self.mock_mode:
            return self._generate_mock_ticker(symbol)
        
        try:
            return self.exchange.fetch_ticker(symbol)
        except Exception as e:
            self.logger.error(f"Error fetching ticker: {e}")
            return None
    
    # Mock methods for testing without API
    def _generate_mock_ohlcv(self, symbol: str, limit: int) -> pd.DataFrame:
        """Generate mock OHLCV data for testing"""
        np.random.seed(42)
        dates = pd.date_range(end=datetime.now(), periods=limit, freq='1h')
        
        # Generate random price data around $50,000 for BTC
        base_price = 50000
        returns = np.random.normal(0.001, 0.02, limit)
        prices = base_price * (1 + returns).cumprod()
        
        df = pd.DataFrame({
            'open': prices * (1 + np.random.normal(0, 0.001, limit)),
            'high': prices * (1 + abs(np.random.normal(0, 0.01, limit))),
            'low': prices * (1 - abs(np.random.normal(0, 0.01, limit))),
            'close': prices,
            'volume': np.random.uniform(100, 1000, limit)
        }, index=dates)
        
        return df
    
    def _generate_mock_balance(self) -> List[Balance]:
        """Generate mock balance for testing"""
        return [
            Balance(asset='USDT', free=10000.0, used=0.0, total=10000.0),
            Balance(asset='BTC', free=0.5, used=0.0, total=0.5),
            Balance(asset='ETH', free=5.0, used=0.0, total=5.0)
        ]
    
    def _generate_mock_order(self, symbol: str, side: str, type_: str,
                            amount: float, price: float = None) -> Order:
        """Generate mock order for testing"""
        return Order(
            symbol=symbol,
            side=side,
            type=type_,
            amount=amount,
            price=price,
            order_id=f"mock_{datetime.now().timestamp()}",
            status='open'
        )
    
    def _generate_mock_ticker(self, symbol: str) -> Dict:
        """Generate mock ticker for testing"""
        return {
            'symbol': symbol,
            'last': 50000.0,
            'bid': 49990.0,
            'ask': 50010.0,
            'high': 51000.0,
            'low': 49000.0,
            'volume': 1000.0
        }
