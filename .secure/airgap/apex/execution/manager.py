"""
Exchange Manager
Unified interface for managing multiple exchanges.
"""

import os
import logging
from typing import Dict, List, Optional

from .exchanges.base import BaseExchange, Order, OrderSide, OrderType
from .exchanges.binance import BinanceConnector
from .exchanges.coinbase import CoinbaseConnector
from .exchanges.kraken import KrakenConnector
from .routing import SmartOrderRouter, RoutingPriority


class ExchangeManager:
    """
    Manages multiple exchange connections and provides unified interface.
    
    Features:
    - Multi-exchange support (Binance, Coinbase, Kraken)
    - Smart order routing
    - Unified balance tracking
    - Cross-exchange arbitrage detection
    """
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.exchanges: Dict[str, BaseExchange] = {}
        self.router = SmartOrderRouter()
        self._initialized = False
        
    def initialize(self, auto_connect: bool = True) -> bool:
        """Initialize all configured exchanges"""
        try:
            # Load from config or environment
            exchanges_config = self.config.get('exchanges', {})
            
            # Binance
            if exchanges_config.get('binance', {}).get('enabled', True):
                binance = BinanceConnector(
                    testnet=exchanges_config.get('binance', {}).get('testnet', True)
                )
                if auto_connect:
                    self.add_exchange(binance)
                else:
                    self.exchanges['Binance'] = binance
            
            # Coinbase
            if exchanges_config.get('coinbase', {}).get('enabled', False):
                coinbase = CoinbaseConnector(
                    sandbox=exchanges_config.get('coinbase', {}).get('sandbox', True)
                )
                if auto_connect:
                    self.add_exchange(coinbase)
                else:
                    self.exchanges['Coinbase'] = coinbase
            
            # Kraken
            if exchanges_config.get('kraken', {}).get('enabled', False):
                kraken = KrakenConnector()
                if auto_connect:
                    self.add_exchange(kraken)
                else:
                    self.exchanges['Kraken'] = kraken
            
            self._initialized = True
            logging.info(f"ExchangeManager initialized with {len(self.exchanges)} exchanges")
            return True
            
        except Exception as e:
            logging.error(f"Failed to initialize ExchangeManager: {e}")
            return False
    
    def add_exchange(self, exchange: BaseExchange) -> bool:
        """Add and connect an exchange"""
        if self.router.add_exchange(exchange):
            self.exchanges[exchange.name] = exchange
            return True
        return False
    
    def get_exchange(self, name: str) -> Optional[BaseExchange]:
        """Get a specific exchange"""
        return self.exchanges.get(name)
    
    def get_all_balances(self) -> Dict[str, Dict]:
        """Get balances from all exchanges"""
        all_balances = {}
        
        for name, exchange in self.exchanges.items():
            try:
                balances = exchange.get_balance()
                all_balances[name] = {
                    asset: {
                        'free': bal.free,
                        'used': bal.used,
                        'total': bal.total
                    }
                    for asset, bal in balances.items()
                }
            except Exception as e:
                logging.error(f"Failed to get balances from {name}: {e}")
                all_balances[name] = {'error': str(e)}
        
        return all_balances
    
    def get_total_balance(self, asset: str) -> Dict[str, float]:
        """Get total balance of an asset across all exchanges"""
        total_free = 0.0
        total_used = 0.0
        
        for name, exchange in self.exchanges.items():
            try:
                balance = exchange.get_balance(asset)
                if asset in balance:
                    total_free += balance[asset].free
                    total_used += balance[asset].used
            except Exception as e:
                logging.error(f"Failed to get {asset} balance from {name}: {e}")
        
        return {
            'free': total_free,
            'used': total_used,
            'total': total_free + total_used
        }
    
    def get_best_price(self, symbol: str, side: OrderSide) -> Dict:
        """Get the best price across all exchanges"""
        best_price = None
        best_exchange = None
        all_prices = {}
        
        for name, exchange in self.exchanges.items():
            try:
                ticker = exchange.get_ticker(symbol)
                price = ticker.ask if side == OrderSide.BUY else ticker.bid
                all_prices[name] = price
                
                if best_price is None:
                    best_price = price
                    best_exchange = name
                elif side == OrderSide.BUY and price < best_price:
                    best_price = price
                    best_exchange = name
                elif side == OrderSide.SELL and price > best_price:
                    best_price = price
                    best_exchange = name
                    
            except Exception as e:
                logging.error(f"Failed to get price from {name}: {e}")
        
        return {
            'best_price': best_price,
            'best_exchange': best_exchange,
            'all_prices': all_prices
        }
    
    def place_order(self, order: Order, use_smart_routing: bool = True,
                    priority: RoutingPriority = None) -> Order:
        """
        Place an order on the best exchange or using smart routing.
        
        Args:
            order: Order to place
            use_smart_routing: If True, use SmartOrderRouter
            priority: Routing priority (if smart routing)
        """
        if use_smart_routing and len(self.exchanges) > 1:
            executed, decision = self.router.route_order(order, priority)
            logging.info(f"Order routed to {decision.selected_exchange}: {decision.reason}")
            return executed
        else:
            # Use specified exchange or first available
            if order.exchange and order.exchange in self.exchanges:
                exchange = self.exchanges[order.exchange]
            else:
                exchange = list(self.exchanges.values())[0]
                order.exchange = exchange.name
            
            return exchange.place_order(order)
    
    def cancel_order(self, order_id: str, symbol: str, 
                     exchange_name: str = None) -> bool:
        """Cancel an order on a specific exchange"""
        if exchange_name and exchange_name in self.exchanges:
            return self.exchanges[exchange_name].cancel_order(order_id, symbol)
        
        # Try all exchanges
        for name, exchange in self.exchanges.items():
            try:
                if exchange.cancel_order(order_id, symbol):
                    return True
            except:
                continue
        
        return False
    
    def get_order_status(self, order_id: str, symbol: str,
                         exchange_name: str = None) -> Optional[Order]:
        """Get order status from an exchange"""
        if exchange_name and exchange_name in self.exchanges:
            return self.exchanges[exchange_name].get_order(order_id, symbol)
        
        # Try all exchanges
        for name, exchange in self.exchanges.items():
            try:
                order = exchange.get_order(order_id, symbol)
                if order:
                    return order
            except:
                continue
        
        return None
    
    def get_arbitrage_opportunities(self, symbol: str,
                                     min_profit_percent: float = 0.1) -> List[Dict]:
        """Find arbitrage opportunities across exchanges"""
        return self.router.get_arbitrage_opportunities(symbol, min_profit_percent)
    
    def get_status(self) -> Dict:
        """Get status of all exchanges and router"""
        return {
            'initialized': self._initialized,
            'exchange_count': len(self.exchanges),
            'exchanges': self.router.get_exchange_status(),
            'routing_enabled': len(self.exchanges) > 1
        }
    
    def disconnect_all(self):
        """Disconnect from all exchanges"""
        for name, exchange in self.exchanges.items():
            try:
                exchange.disconnect()
                logging.info(f"Disconnected from {name}")
            except Exception as e:
                logging.error(f"Error disconnecting from {name}: {e}")
        
        self.exchanges.clear()
        self._initialized = False
