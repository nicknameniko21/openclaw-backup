"""
Coinbase Exchange Connector
Handles all Coinbase Advanced Trade API interactions.
"""

import os
import logging
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd

from .base import (
    BaseExchange, Order, OrderType, OrderSide, OrderStatus,
    Balance, Ticker, ExchangeFees
)

# Try to import ccxt
try:
    import ccxt
    CCXT_AVAILABLE = True
except ImportError:
    CCXT_AVAILABLE = False


class CoinbaseConnector(BaseExchange):
    """
    Coinbase exchange connector.
    Implements the standardized BaseExchange interface.
    """
    
    def __init__(self, api_key: str = None, secret: str = None,
                 passphrase: str = None, sandbox: bool = True):
        super().__init__("Coinbase", api_key, secret, sandbox=sandbox)
        self.passphrase = passphrase or os.getenv('COINBASE_PASSPHRASE')
        self.exchange = None
        
    def connect(self) -> bool:
        """Connect to Coinbase API"""
        if not CCXT_AVAILABLE:
            logging.warning("CCXT not available, using mock mode")
            return self._connect_mock()
        
        try:
            api_key = self.api_key or os.getenv('COINBASE_API_KEY')
            secret = self.secret or os.getenv('COINBASE_SECRET')
            
            config = {
                'apiKey': api_key,
                'secret': secret,
                'enableRateLimit': True,
            }
            
            if self.passphrase:
                config['password'] = self.passphrase
            
            if self.sandbox:
                config['sandbox'] = True
            
            self.exchange = ccxt.coinbase(config)
            self.exchange.load_markets()
            self._connected = True
            logging.info(f"Connected to Coinbase {'sandbox' if self.sandbox else 'live'}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to connect to Coinbase: {e}")
            return self._connect_mock()
    
    def _connect_mock(self) -> bool:
        """Fallback to mock mode"""
        from .base import MockExchange
        self._mock = MockExchange("Coinbase")
        self._mock.connect()
        self._connected = True
        self._using_mock = True
        logging.info("Coinbase using mock mode")
        return True
    
    def disconnect(self) -> bool:
        """Disconnect from Coinbase"""
        self.exchange = None
        self._connected = False
        return True
    
    def is_connected(self) -> bool:
        """Check connection status"""
        return self._connected
    
    def get_balance(self, asset: str = None) -> Dict[str, Balance]:
        """Get account balance"""
        if hasattr(self, '_using_mock') and self._using_mock:
            return self._mock.get_balance(asset)
        
        try:
            balance_data = self.exchange.fetch_balance()
            balances = {}
            
            for asset_code, data in balance_data.items():
                if isinstance(data, dict) and 'free' in data:
                    balances[asset_code] = Balance(
                        asset=asset_code,
                        free=data.get('free', 0),
                        used=data.get('used', 0),
                        total=data.get('total', 0)
                    )
            
            if asset:
                return {asset: balances.get(asset, Balance(asset, 0, 0, 0))}
            return balances
            
        except Exception as e:
            logging.error(f"Error fetching balance: {e}")
            return {}
    
    def get_ticker(self, symbol: str) -> Ticker:
        """Get current price ticker"""
        if hasattr(self, '_using_mock') and self._using_mock:
            return self._mock.get_ticker(symbol)
        
        try:
            ticker_data = self.exchange.fetch_ticker(symbol)
            return Ticker(
                symbol=symbol,
                bid=ticker_data.get('bid', 0),
                ask=ticker_data.get('ask', 0),
                last=ticker_data.get('last', 0),
                volume=ticker_data.get('quoteVolume', 0),
                timestamp=datetime.fromtimestamp(ticker_data['timestamp'] / 1000),
                exchange=self.name
            )
        except Exception as e:
            logging.error(f"Error fetching ticker: {e}")
            raise
    
    def get_ohlcv(self, symbol: str, timeframe: str = '1h',
                  limit: int = 100) -> pd.DataFrame:
        """Get OHLCV data"""
        if hasattr(self, '_using_mock') and self._using_mock:
            return self._mock.get_ohlcv(symbol, timeframe, limit)
        
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            logging.error(f"Error fetching OHLCV: {e}")
            raise
    
    def place_order(self, order: Order) -> Order:
        """Place an order"""
        if hasattr(self, '_using_mock') and self._using_mock:
            return self._mock.place_order(order)
        
        try:
            type_map = {
                OrderType.MARKET: 'market',
                OrderType.LIMIT: 'limit',
            }
            order_type = type_map.get(order.order_type, 'market')
            side = 'buy' if order.side == OrderSide.BUY else 'sell'
            
            result = self.exchange.create_order(
                order.symbol,
                order_type,
                side,
                order.amount,
                order.price
            )
            
            order.order_id = result['id']
            order.status = OrderStatus.OPEN
            order.exchange = self.name
            return order
            
        except Exception as e:
            logging.error(f"Error placing order: {e}")
            order.status = OrderStatus.REJECTED
            return order
    
    def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an order"""
        if hasattr(self, '_using_mock') and self._using_mock:
            return self._mock.cancel_order(order_id, symbol)
        
        try:
            self.exchange.cancel_order(order_id, symbol)
            return True
        except Exception as e:
            logging.error(f"Error canceling order: {e}")
            return False
    
    def get_order(self, order_id: str, symbol: str) -> Order:
        """Get order status"""
        if hasattr(self, '_using_mock') and self._using_mock:
            return self._mock.get_order(order_id, symbol)
        
        try:
            result = self.exchange.fetch_order(order_id, symbol)
            status_map = {
                'open': OrderStatus.OPEN,
                'closed': OrderStatus.CLOSED,
                'canceled': OrderStatus.CANCELED
            }
            
            return Order(
                symbol=symbol,
                side=OrderSide.BUY if result['side'] == 'buy' else OrderSide.SELL,
                order_type=OrderType.MARKET,
                amount=result['amount'],
                price=result['price'],
                order_id=result['id'],
                status=status_map.get(result['status'], OrderStatus.PENDING),
                filled_amount=result['filled'],
                timestamp=datetime.fromtimestamp(result['timestamp'] / 1000),
                exchange=self.name
            )
        except Exception as e:
            logging.error(f"Error fetching order: {e}")
            return None
    
    def get_open_orders(self, symbol: str = None) -> List[Order]:
        """Get open orders"""
        if hasattr(self, '_using_mock') and self._using_mock:
            return self._mock.get_open_orders(symbol)
        
        try:
            orders = self.exchange.fetch_open_orders(symbol)
            return [self._convert_ccxt_order(o) for o in orders]
        except Exception as e:
            logging.error(f"Error fetching open orders: {e}")
            return []
    
    def _convert_ccxt_order(self, data: dict) -> Order:
        """Convert ccxt order to Order object"""
        status_map = {
            'open': OrderStatus.OPEN,
            'closed': OrderStatus.CLOSED,
            'canceled': OrderStatus.CANCELED
        }
        
        return Order(
            symbol=data['symbol'],
            side=OrderSide.BUY if data['side'] == 'buy' else OrderSide.SELL,
            order_type=OrderType.MARKET,
            amount=data['amount'],
            price=data['price'],
            order_id=data['id'],
            status=status_map.get(data['status'], OrderStatus.PENDING),
            filled_amount=data['filled'],
            timestamp=datetime.fromtimestamp(data['timestamp'] / 1000),
            exchange=self.name
        )
    
    def get_fees(self) -> ExchangeFees:
        """Get trading fees"""
        if hasattr(self, '_using_mock') and self._using_mock:
            return self._mock.get_fees()
        
        # Coinbase default fees (simplified)
        return ExchangeFees(
            maker=0.006,  # 0.6%
            taker=0.008,  # 0.8%
            withdrawal={'BTC': 0.0001, 'ETH': 0.001}
        )
    
    def get_symbols(self) -> List[str]:
        """Get available trading pairs"""
        if hasattr(self, '_using_mock') and self._using_mock:
            return self._mock.get_symbols()
        
        try:
            markets = self.exchange.load_markets()
            return list(markets.keys())
        except Exception as e:
            logging.error(f"Error fetching symbols: {e}")
            return []
