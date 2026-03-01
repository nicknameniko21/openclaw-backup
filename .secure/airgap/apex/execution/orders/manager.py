"""
Order Management System
Handles order lifecycle and tracking.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import logging


class OrderStatus(Enum):
    PENDING = "pending"
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELED = "canceled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    STOP_LIMIT = "stop_limit"


@dataclass
class Order:
    """Order data structure"""
    id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    amount: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_amount: float = 0.0
    remaining_amount: float = 0.0
    avg_fill_price: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    exchange_id: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        if self.remaining_amount == 0 and self.amount > 0:
            self.remaining_amount = self.amount
    
    def to_dict(self) -> Dict:
        """Convert order to dictionary"""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'side': self.side.value,
            'type': self.order_type.value,
            'amount': self.amount,
            'price': self.price,
            'stop_price': self.stop_price,
            'status': self.status.value,
            'filled_amount': self.filled_amount,
            'remaining_amount': self.remaining_amount,
            'avg_fill_price': self.avg_fill_price,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'exchange_id': self.exchange_id,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Order':
        """Create order from dictionary"""
        return cls(
            id=data['id'],
            symbol=data['symbol'],
            side=OrderSide(data['side']),
            order_type=OrderType(data['type']),
            amount=data['amount'],
            price=data.get('price'),
            stop_price=data.get('stop_price'),
            status=OrderStatus(data['status']),
            filled_amount=data.get('filled_amount', 0.0),
            remaining_amount=data.get('remaining_amount', 0.0),
            avg_fill_price=data.get('avg_fill_price', 0.0),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            exchange_id=data.get('exchange_id'),
            metadata=data.get('metadata', {})
        )


class OrderManager:
    """
    Manages order lifecycle from creation to completion.
    
    Features:
    - Order creation and validation
    - Status tracking and updates
    - Order history
    - Integration with exchange connectors
    """
    
    def __init__(self, storage_path: str = None):
        self.logger = logging.getLogger(__name__)
        self.orders: Dict[str, Order] = {}
        self.order_history: List[Order] = []
        self.storage_path = storage_path
        
        if storage_path:
            self._load_orders()
    
    def create_order(self, symbol: str, side: OrderSide, order_type: OrderType,
                    amount: float, price: float = None, 
                    stop_price: float = None,
                    metadata: Dict = None) -> Order:
        """
        Create a new order.
        
        Args:
            symbol: Trading pair symbol
            side: Buy or sell
            order_type: Market, limit, etc.
            amount: Order amount
            price: Limit price (for limit orders)
            stop_price: Stop price (for stop orders)
            metadata: Additional order metadata
            
        Returns:
            Created Order object
        """
        order_id = f"ord_{datetime.now().timestamp()}"
        
        order = Order(
            id=order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            amount=amount,
            price=price,
            stop_price=stop_price,
            metadata=metadata or {}
        )
        
        self.orders[order_id] = order
        self.logger.info(f"Order created: {order_id} ({side.value} {amount} {symbol})")
        
        return order
    
    def update_order_status(self, order_id: str, status: OrderStatus,
                           filled_amount: float = None,
                           avg_fill_price: float = None,
                           exchange_id: str = None) -> bool:
        """
        Update order status and fill information.
        
        Args:
            order_id: Order ID
            status: New status
            filled_amount: Amount filled
            avg_fill_price: Average fill price
            exchange_id: Exchange order ID
            
        Returns:
            True if order was found and updated
        """
        if order_id not in self.orders:
            self.logger.warning(f"Order not found: {order_id}")
            return False
        
        order = self.orders[order_id]
        order.status = status
        order.updated_at = datetime.now()
        
        if filled_amount is not None:
            order.filled_amount = filled_amount
            order.remaining_amount = order.amount - filled_amount
        
        if avg_fill_price is not None:
            order.avg_fill_price = avg_fill_price
        
        if exchange_id is not None:
            order.exchange_id = exchange_id
        
        # Move to history if terminal state
        if status in [OrderStatus.FILLED, OrderStatus.CANCELED, 
                     OrderStatus.REJECTED, OrderStatus.EXPIRED]:
            self.order_history.append(order)
            self.logger.info(f"Order {order_id} completed with status: {status.value}")
        
        self._save_orders()
        return True
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            True if order was found and canceled
        """
        if order_id not in self.orders:
            return False
        
        order = self.orders[order_id]
        
        if order.status in [OrderStatus.FILLED, OrderStatus.CANCELED]:
            self.logger.warning(f"Cannot cancel order {order_id}: already {order.status.value}")
            return False
        
        self.update_order_status(order_id, OrderStatus.CANCELED)
        return True
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID"""
        return self.orders.get(order_id)
    
    def get_open_orders(self, symbol: str = None) -> List[Order]:
        """
        Get all open orders.
        
        Args:
            symbol: Filter by symbol (optional)
            
        Returns:
            List of open orders
        """
        open_statuses = [OrderStatus.PENDING, OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED]
        orders = [o for o in self.orders.values() if o.status in open_statuses]
        
        if symbol:
            orders = [o for o in orders if o.symbol == symbol]
        
        return orders
    
    def get_order_history(self, symbol: str = None, limit: int = None) -> List[Order]:
        """
        Get order history.
        
        Args:
            symbol: Filter by symbol
            limit: Maximum number of orders to return
            
        Returns:
            List of historical orders
        """
        orders = self.order_history
        
        if symbol:
            orders = [o for o in orders if o.symbol == symbol]
        
        orders = sorted(orders, key=lambda o: o.created_at, reverse=True)
        
        if limit:
            orders = orders[:limit]
        
        return orders
    
    def get_statistics(self) -> Dict:
        """Get order statistics"""
        all_orders = list(self.orders.values()) + self.order_history
        
        filled_orders = [o for o in all_orders if o.status == OrderStatus.FILLED]
        buy_orders = [o for o in filled_orders if o.side == OrderSide.BUY]
        sell_orders = [o for o in filled_orders if o.side == OrderSide.SELL]
        
        return {
            'total_orders': len(all_orders),
            'open_orders': len(self.get_open_orders()),
            'filled_orders': len(filled_orders),
            'canceled_orders': len([o for o in all_orders if o.status == OrderStatus.CANCELED]),
            'buy_orders': len(buy_orders),
            'sell_orders': len(sell_orders),
            'total_volume': sum(o.filled_amount for o in filled_orders)
        }
    
    def _save_orders(self):
        """Save orders to file"""
        if not self.storage_path:
            return
        
        try:
            data = {
                'active': [o.to_dict() for o in self.orders.values()],
                'history': [o.to_dict() for o in self.order_history]
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving orders: {e}")
    
    def _load_orders(self):
        """Load orders from file"""
        import os
        if not os.path.exists(self.storage_path):
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            for order_data in data.get('active', []):
                order = Order.from_dict(order_data)
                self.orders[order.id] = order
            
            for order_data in data.get('history', []):
                order = Order.from_dict(order_data)
                self.order_history.append(order)
            
            self.logger.info(f"Loaded {len(self.orders)} active orders, "
                           f"{len(self.order_history)} historical orders")
                           
        except Exception as e:
            self.logger.error(f"Error loading orders: {e}")
