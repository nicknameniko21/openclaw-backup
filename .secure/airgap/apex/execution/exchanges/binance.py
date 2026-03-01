"""
Binance Exchange Connector
Handles all Binance API interactions using the standardized interface.
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

# Try to import ccxt, handle if not installed
try:
    import ccxt
    CCXT_AVAILABLE = True
except ImportError:
    CCXT_AVAILABLE = False
    logging.warning("ccxt not installed. Binance connector will use mock mode.")


class BinanceConnector(BaseExchange):
    """
    Binance exchange connector using CCXT library.
    Implements the standardized BaseExchange interface.
    """
    
    def __init__(self, api_key: str = None, secret: str = None, 
                 testnet: bool = True):
        super().__init__("Binance", api_key, secret, testnet)
        self.exchange = None
        
    def connect(self) -> bool:
        """Connect to Binance API"""
        if not CCXT_AVAILABLE:
            logging.warning("CCXT not available, using mock mode")
            return self._connect_mock()
        
        try:
            api_key = self.api_key or os.getenv('BINANCE_API_KEY')
            secret = self.secret or os.getenv('BINANCE_SECRET')
            
            config = {
                'apiKey': api_key,
                'secret': secret,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',
                }
            }
            
            if self.testnet:
                config['sandbox'] = True
                # Use testnet URLs
                config['urls'] = {
                    'api': {
                        'public': 'https://testnet.binance.vision/api',
                        'private': 'https://testnet.binance.vision/api',
                    }
                }
            
            self.exchange = ccxt.binance(config)
            
            # Test connection
            self.exchange.load_markets()
            self._connected = True
            logging.info(f"Connected to Binance {'testnet' if self.testnet else 'live'}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to connect to Binance: {e}")
            return self._connect_mock()
    
    def _connect_mock(self) -> bool:
        """Fallback to mock mode"""
        from .base import MockExchange
        self._mock = MockExchange("Binance")
        self._mock.connect()
        self._connected = True
        self._using_mock = True
        logging.info("Binance using mock mode")
        return True
    
    def disconnect(self) -> bool:
        """Disconnect from Binance"""
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
            # Convert timeframe to ccxt format
            tf_map = {
                '1m': '1m', '5m': '5m', '15m': '15m',
                '1h': '1h', '4h': '4h', '1d': '1d'
            }
            ccxt_tf = tf_map.get(timeframe, '1h')
            
            ohlcv = self.exchange.fetch_ohlcv(symbol, ccxt_tf, limit=limit)
            
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
            # Convert order type
            type_map = {
                OrderType.MARKET: 'market',
                OrderType.LIMIT: 'limit',
                OrderType.STOP_LOSS: 'stop_loss',
                OrderType.STOP_LIMIT: 'stop_limit'
            }
            order_type = type_map.get(order.order_type, 'market')
            side = 'buy' if order.side == OrderSide.BUY else 'sell'
            
            params = {}
            if order.stop_price:
                params['stopPrice'] = order.stop_price
            
            result = self.exchange.create_order(
                order.symbol,
                order_type,
                side,
                order.amount,
                order.price,
                params
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
                order_type=OrderType.MARKET,  # Simplified
                amount=result['amount'],
                price=result['price'],
                order_id=result['id'],
                status=status_map.get(result['status'], OrderStatus.PENDING),
                filled_amount=result['filled'],
                average_price=result.get('average', 0),
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
        """Convert ccxt order format to Order object"""
        status_map = {
            'open': OrderStatus.OPEN,
            'closed': OrderStatus.CLOSED,
            'canceled': OrderStatus.CANCELED
        }
        
        return Order(
            symbol=data['symbol'],
            side=OrderSide.BUY if data['side'] == 'buy' else OrderSide.SELL,
            order_type=OrderType.MARKET,  # Simplified
            amount=data['amount'],
            price=data['price'],
            order_id=data['id'],
            status=status_map.get(data['status'], OrderStatus.PENDING),
            filled_amount=data['filled'],
            average_price=data.get('average', 0),
            timestamp=datetime.fromtimestamp(data['timestamp'] / 1000),
            exchange=self.name
        )
    
    def get_fees(self) -> ExchangeFees:
        """Get trading fees"""
        if hasattr(self, '_using_mock') and self._using_mock:
            return self._mock.get_fees()
        
        try:
            # Default Binance fees (VIP 0)
            return ExchangeFees(
                maker=0.001,  # 0.1%
                taker=0.001,  # 0.1%
                withdrawal={
                    'BTC': 0.0005,
                    'ETH': 0.005,
                    'USDT': 1.0
                }
            )
        except Exception as e:
            logging.error(f"Error fetching fees: {e}")
            return ExchangeFees(maker=0.001, taker=0.001, withdrawal={})
    
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
