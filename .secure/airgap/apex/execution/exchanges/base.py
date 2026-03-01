"""
Base Exchange Interface
Abstract base class for all exchange connectors.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import pandas as pd


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    STOP_LIMIT = "stop_limit"


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    PENDING = "pending"
    OPEN = "open"
    CLOSED = "closed"
    CANCELED = "canceled"
    REJECTED = "rejected"


@dataclass
class Order:
    """Standardized order data structure"""
    symbol: str
    side: OrderSide
    order_type: OrderType
    amount: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    order_id: Optional[str] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_amount: float = 0.0
    average_price: float = 0.0
    fee: float = 0.0
    fee_currency: str = ""
    timestamp: datetime = None
    exchange: str = ""
    
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


@dataclass
class Ticker:
    """Price ticker data"""
    symbol: str
    bid: float
    ask: float
    last: float
    volume: float
    timestamp: datetime
    exchange: str


@dataclass
class ExchangeFees:
    """Trading fees"""
    maker: float
    taker: float
    withdrawal: Dict[str, float]


class BaseExchange(ABC):
    """
    Abstract base class for all exchange connectors.
    All exchange implementations must inherit from this class.
    """
    
    def __init__(self, name: str, api_key: str = None, secret: str = None, 
                 testnet: bool = True, sandbox: bool = False):
        self.name = name
        self.api_key = api_key
        self.secret = secret
        self.testnet = testnet
        self.sandbox = sandbox
        self._connected = False
        self._fees: Optional[ExchangeFees] = None
    
    @abstractmethod
    def connect(self) -> bool:
        """Connect to exchange API"""
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """Disconnect from exchange API"""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected to exchange"""
        pass
    
    @abstractmethod
    def get_balance(self, asset: str = None) -> Dict[str, Balance]:
        """Get account balance"""
        pass
    
    @abstractmethod
    def get_ticker(self, symbol: str) -> Ticker:
        """Get current price ticker"""
        pass
    
    @abstractmethod
    def get_ohlcv(self, symbol: str, timeframe: str = '1h', 
                  limit: int = 100) -> pd.DataFrame:
        """Get OHLCV data"""
        pass
    
    @abstractmethod
    def place_order(self, order: Order) -> Order:
        """Place an order"""
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an order"""
        pass
    
    @abstractmethod
    def get_order(self, order_id: str, symbol: str) -> Order:
        """Get order status"""
        pass
    
    @abstractmethod
    def get_open_orders(self, symbol: str = None) -> List[Order]:
        """Get all open orders"""
        pass
    
    @abstractmethod
    def get_fees(self) -> ExchangeFees:
        """Get trading fees"""
        pass
    
    @abstractmethod
    def get_symbols(self) -> List[str]:
        """Get available trading pairs"""
        pass
    
    def get_spread(self, symbol: str) -> float:
        """Calculate bid-ask spread"""
        ticker = self.get_ticker(symbol)
        return (ticker.ask - ticker.bid) / ticker.last * 100
    
    def get_mid_price(self, symbol: str) -> float:
        """Get mid price (average of bid and ask)"""
        ticker = self.get_ticker(symbol)
        return (ticker.bid + ticker.ask) / 2
    
    def estimate_cost(self, symbol: str, amount: float, 
                      side: OrderSide) -> Tuple[float, float]:
        """
        Estimate total cost including fees
        Returns: (cost_without_fees, total_cost_with_fees)
        """
        ticker = self.get_ticker(symbol)
        price = ticker.ask if side == OrderSide.BUY else ticker.bid
        cost = amount * price
        fees = self.get_fees()
        fee_rate = fees.taker  # Assume taker fee for estimation
        total_cost = cost * (1 + fee_rate)
        return cost, total_cost


class MockExchange(BaseExchange):
    """
    Mock exchange for testing without real API calls.
    Simulates realistic price movements and order execution.
    """
    
    def __init__(self, name: str = "MockExchange"):
        super().__init__(name, testnet=True)
        self._prices = {}
        self._balances = {}
        self._orders = {}
        self._order_counter = 0
        self._initialize_mock_data()
    
    def _initialize_mock_data(self):
        """Initialize mock price data"""
        import random
        import numpy as np
        
        base_prices = {
            'BTC/USDT': 65000.0,
            'ETH/USDT': 3500.0,
            'SOL/USDT': 145.0,
            'BNB/USDT': 590.0,
            'XRP/USDT': 0.62,
            'ADA/USDT': 0.58,
            'DOGE/USDT': 0.16,
            'DOT/USDT': 7.8,
        }
        
        for symbol, base_price in base_prices.items():
            # Add some randomness
            variation = random.uniform(-0.02, 0.02)
            price = base_price * (1 + variation)
            self._prices[symbol] = {
                'bid': price * 0.9995,
                'ask': price * 1.0005,
                'last': price,
                'volume': random.uniform(1000000, 10000000)
            }
        
        # Initialize balances
        self._balances = {
            'USDT': Balance('USDT', 10000.0, 0.0, 10000.0),
            'BTC': Balance('BTC', 0.1, 0.0, 0.1),
            'ETH': Balance('ETH', 1.0, 0.0, 1.0),
        }
    
    def connect(self) -> bool:
        self._connected = True
        return True
    
    def disconnect(self) -> bool:
        self._connected = False
        return True
    
    def is_connected(self) -> bool:
        return self._connected
    
    def get_balance(self, asset: str = None) -> Dict[str, Balance]:
        if asset:
            return {asset: self._balances.get(asset, Balance(asset, 0.0, 0.0, 0.0))}
        return self._balances
    
    def get_ticker(self, symbol: str) -> Ticker:
        if symbol not in self._prices:
            # Generate mock price for unknown symbol
            import random
            base_price = random.uniform(1, 1000)
            self._prices[symbol] = {
                'bid': base_price * 0.9995,
                'ask': base_price * 1.0005,
                'last': base_price,
                'volume': random.uniform(100000, 1000000)
            }
        
        p = self._prices[symbol]
        return Ticker(
            symbol=symbol,
            bid=p['bid'],
            ask=p['ask'],
            last=p['last'],
            volume=p['volume'],
            timestamp=datetime.now(),
            exchange=self.name
        )
    
    def get_ohlcv(self, symbol: str, timeframe: str = '1h', 
                  limit: int = 100) -> pd.DataFrame:
        """Generate mock OHLCV data"""
        import numpy as np
        
        ticker = self.get_ticker(symbol)
        base_price = ticker.last
        
        # Generate random walk
        np.random.seed(42)  # For reproducibility
        returns = np.random.normal(0.0001, 0.02, limit)
        prices = base_price * np.exp(np.cumsum(returns))
        
        # Create OHLCV data
        data = []
        for i, price in enumerate(prices):
            volatility = price * 0.005
            open_p = price + np.random.normal(0, volatility)
            high_p = max(open_p, price) + abs(np.random.normal(0, volatility))
            low_p = min(open_p, price) - abs(np.random.normal(0, volatility))
            close_p = price
            volume = np.random.uniform(100, 1000)
            
            data.append({
                'timestamp': datetime.now(),
                'open': open_p,
                'high': high_p,
                'low': low_p,
                'close': close_p,
                'volume': volume
            })
        
        return pd.DataFrame(data)
    
    def place_order(self, order: Order) -> Order:
        self._order_counter += 1
        order.order_id = f"mock_{self.name}_{self._order_counter}"
        order.status = OrderStatus.CLOSED  # Instant fill in mock mode
        order.exchange = self.name
        
        # Simulate fill
        ticker = self.get_ticker(order.symbol)
        if order.order_type == OrderType.MARKET:
            order.average_price = ticker.ask if order.side == OrderSide.BUY else ticker.bid
        else:
            order.average_price = order.price or ticker.last
        
        order.filled_amount = order.amount
        
        # Calculate fee
        fees = self.get_fees()
        order.fee = order.amount * order.average_price * fees.taker
        order.fee_currency = order.symbol.split('/')[1]
        
        self._orders[order.order_id] = order
        return order
    
    def cancel_order(self, order_id: str, symbol: str) -> bool:
        if order_id in self._orders:
            self._orders[order_id].status = OrderStatus.CANCELED
            return True
        return False
    
    def get_order(self, order_id: str, symbol: str) -> Order:
        return self._orders.get(order_id)
    
    def get_open_orders(self, symbol: str = None) -> List[Order]:
        orders = [o for o in self._orders.values() 
                  if o.status == OrderStatus.OPEN]
        if symbol:
            orders = [o for o in orders if o.symbol == symbol]
        return orders
    
    def get_fees(self) -> ExchangeFees:
        return ExchangeFees(
            maker=0.001,  # 0.1%
            taker=0.001,  # 0.1%
            withdrawal={'BTC': 0.0005, 'ETH': 0.005}
        )
    
    def get_symbols(self) -> List[str]:
        return list(self._prices.keys())
