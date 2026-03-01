"""
Advanced Order Types
Implements sophisticated order types for professional trading.
"""

from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import time
import threading

from .manager import Order, OrderSide, OrderType, OrderStatus


class AdvancedOrderType(Enum):
    """Extended order types beyond basic market/limit"""
    ICEBERG = "iceberg"              # Hidden large orders shown in chunks
    TRAILING_STOP = "trailing_stop"  # Stop that follows price
    BRACKET = "bracket"              # Entry + stop loss + take profit
    OCO = "oco"                      # One-cancels-other
    PEGGED = "pegged"                # Price pegged to market
    RESERVE = "reserve"              # Reserve order with display quantity


@dataclass
class IcebergOrder:
    """
    Iceberg Order - Large order hidden behind smaller visible chunks.
    
    Shows only a portion of the total order at a time to minimize
    market impact and hide true order size from other traders.
    
    Example: 1000 BTC order with 100 BTC display size shows as
    100 BTC, then refreshes to 100 BTC after each fill until complete.
    """
    total_amount: float
    display_size: float
    symbol: str
    side: OrderSide
    price: Optional[float] = None  # None for market iceberg
    variance_pct: float = 0.1      # Randomize display size ±10%
    
    # Internal state
    remaining: float = field(default=0.0, repr=False)
    current_display: float = field(default=0.0, repr=False)
    chunks_executed: int = field(default=0, repr=False)
    orders: List[Order] = field(default_factory=list, repr=False)
    
    def __post_init__(self):
        self.remaining = self.total_amount
        self._calculate_display_size()
    
    def _calculate_display_size(self):
        """Calculate next display size with variance"""
        import random
        variance = self.display_size * self.variance_pct
        self.current_display = min(
            self.display_size + random.uniform(-variance, variance),
            self.remaining
        )
    
    def get_next_chunk(self) -> Optional[Order]:
        """Get the next visible chunk as an order"""
        if self.remaining <= 0:
            return None
        
        chunk_size = min(self.current_display, self.remaining)
        
        order_type = OrderType.LIMIT if self.price else OrderType.MARKET
        
        order = Order(
            id=f"iceberg_{self.symbol}_{int(time.time() * 1000)}",
            symbol=self.symbol,
            side=self.side,
            order_type=order_type,
            amount=chunk_size,
            price=self.price,
            metadata={
                'iceberg_parent': True,
                'iceberg_chunk': self.chunks_executed + 1,
                'iceberg_total_chunks': int(self.total_amount / self.display_size) + 1
            }
        )
        
        self.orders.append(order)
        return order
    
    def on_chunk_filled(self, filled_amount: float) -> Optional[Order]:
        """Called when a chunk fills - returns next chunk if any"""
        self.remaining -= filled_amount
        self.chunks_executed += 1
        
        if self.remaining > 0:
            self._calculate_display_size()
            return self.get_next_chunk()
        
        return None
    
    def is_complete(self) -> bool:
        """Check if entire iceberg order is filled"""
        return self.remaining <= 0
    
    def get_progress(self) -> Dict:
        """Get execution progress"""
        filled = self.total_amount - self.remaining
        return {
            'total': self.total_amount,
            'remaining': self.remaining,
            'filled': filled,
            'percent_complete': (filled / self.total_amount) * 100,
            'chunks_executed': self.chunks_executed
        }


@dataclass
class TrailingStopOrder:
    """
    Trailing Stop Order - Stop price follows favorable price movement.
    
    For BUY stops: Stop price trails below market by offset,
    moves up when market rises, stays put when market falls.
    
    For SELL stops: Stop price trails above market by offset,
    moves down when market falls, stays put when market rises.
    
    Example: SELL trailing stop at $100 with $5 trail
    - Market rises to $105 → stop moves to $100
    - Market falls to $102 → stop stays at $100
    - Market hits $100 → order triggers
    """
    symbol: str
    side: OrderSide  # BUY = stop-entry, SELL = stop-loss
    amount: float
    trail_amount: Optional[float] = None      # Fixed dollar/pip amount
    trail_percent: Optional[float] = None     # Percentage trail
    
    # Internal state
    stop_price: float = field(default=0.0, repr=False)
    highest_price: float = field(default=0.0, repr=False)  # For SELL stops
    lowest_price: float = field(default=float('inf'), repr=False)  # For BUY stops
    activated: bool = field(default=False, repr=False)
    
    def __post_init__(self):
        if self.trail_amount is None and self.trail_percent is None:
            raise ValueError("Must specify either trail_amount or trail_percent")
        if self.trail_amount is not None and self.trail_percent is not None:
            raise ValueError("Cannot specify both trail_amount and trail_percent")
    
    def update_price(self, current_price: float) -> Optional[Order]:
        """
        Update trailing stop with new market price.
        Returns Order if stop is triggered, None otherwise.
        """
        if not self.activated:
            # Initialize on first price
            self._initialize(current_price)
            return None
        
        # Update trailing extremes
        if self.side == OrderSide.SELL:
            # For sell stops, trail below highest price
            if current_price > self.highest_price:
                self.highest_price = current_price
                self._update_stop_price()
            
            # Check if triggered
            if current_price <= self.stop_price:
                return self._create_market_order()
                
        else:  # BUY stop
            # For buy stops, trail above lowest price
            if current_price < self.lowest_price:
                self.lowest_price = current_price
                self._update_stop_price()
            
            # Check if triggered
            if current_price >= self.stop_price:
                return self._create_market_order()
        
        return None
    
    def _initialize(self, price: float):
        """Initialize trailing stop"""
        self.highest_price = price
        self.lowest_price = price
        self._update_stop_price()
        self.activated = True
        logging.info(f"Trailing stop activated at {price}, stop: {self.stop_price}")
    
    def _update_stop_price(self):
        """Calculate new stop price based on trail"""
        if self.side == OrderSide.SELL:
            if self.trail_amount:
                self.stop_price = self.highest_price - self.trail_amount
            else:
                self.stop_price = self.highest_price * (1 - self.trail_percent / 100)
        else:
            if self.trail_amount:
                self.stop_price = self.lowest_price + self.trail_amount
            else:
                self.stop_price = self.lowest_price * (1 + self.trail_percent / 100)
    
    def _create_market_order(self) -> Order:
        """Create market order when stop triggers"""
        return Order(
            id=f"trailing_stop_{self.symbol}_{int(time.time() * 1000)}",
            symbol=self.symbol,
            side=self.side,
            order_type=OrderType.MARKET,
            amount=self.amount,
            metadata={
                'trailing_stop_triggered': True,
                'stop_price': self.stop_price,
                'highest_price': self.highest_price if self.side == OrderSide.SELL else None,
                'lowest_price': self.lowest_price if self.side == OrderSide.BUY else None
            }
        )
    
    def get_status(self) -> Dict:
        """Get current trailing stop status"""
        return {
            'activated': self.activated,
            'current_stop_price': self.stop_price,
            'highest_price': self.highest_price if self.side == OrderSide.SELL else None,
            'lowest_price': self.lowest_price if self.side == OrderSide.BUY else None,
            'trail_amount': self.trail_amount,
            'trail_percent': self.trail_percent
        }


@dataclass
class BracketOrder:
    """
    Bracket Order - Entry order with attached stop loss and take profit.
    
    Automatically creates three linked orders:
    1. Entry order (market or limit)
    2. Stop loss order (cancels when take profit fills)
    3. Take profit order (cancels when stop loss fills)
    
    Example: Buy BTC at $50,000
    - Stop loss at $48,000 (risk $2,000)
    - Take profit at $55,000 (reward $5,000)
    - Risk/Reward ratio: 1:2.5
    """
    symbol: str
    side: OrderSide
    amount: float
    entry_price: Optional[float] = None  # None for market entry
    stop_loss_price: float = 0.0
    take_profit_price: float = 0.0
    
    # Internal state
    entry_order: Optional[Order] = field(default=None, repr=False)
    stop_order: Optional[Order] = field(default=None, repr=False)
    profit_order: Optional[Order] = field(default=None, repr=False)
    status: str = field(default="pending", repr=False)  # pending, entry_filled, completed, canceled
    
    def __post_init__(self):
        # Validate prices
        if self.side == OrderSide.BUY:
            if self.stop_loss_price >= self.entry_price or self.entry_price is None:
                pass  # Market entry is ok
            elif self.stop_loss_price >= self.entry_price:
                raise ValueError("Stop loss must be below entry for BUY")
            if self.take_profit_price <= self.entry_price:
                raise ValueError("Take profit must be above entry for BUY")
        else:
            if self.stop_loss_price <= self.entry_price:
                raise ValueError("Stop loss must be above entry for SELL")
            if self.take_profit_price >= self.entry_price:
                raise ValueError("Take profit must be below entry for SELL")
    
    def create_orders(self) -> List[Order]:
        """Create all three bracket orders"""
        # Entry order
        entry_type = OrderType.LIMIT if self.entry_price else OrderType.MARKET
        self.entry_order = Order(
            id=f"bracket_entry_{self.symbol}_{int(time.time() * 1000)}",
            symbol=self.symbol,
            side=self.side,
            order_type=entry_type,
            amount=self.amount,
            price=self.entry_price,
            metadata={'bracket_entry': True}
        )
        
        # Stop loss (opposite side)
        stop_side = OrderSide.SELL if self.side == OrderSide.BUY else OrderSide.BUY
        self.stop_order = Order(
            id=f"bracket_stop_{self.symbol}_{int(time.time() * 1000)}",
            symbol=self.symbol,
            side=stop_side,
            order_type=OrderType.STOP_LOSS,
            amount=self.amount,
            stop_price=self.stop_loss_price,
            metadata={'bracket_stop': True, 'bracket_parent': self.entry_order.id}
        )
        
        # Take profit (opposite side)
        self.profit_order = Order(
            id=f"bracket_profit_{self.symbol}_{int(time.time() * 1000)}",
            symbol=self.symbol,
            side=stop_side,
            order_type=OrderType.TAKE_PROFIT,
            amount=self.amount,
            price=self.take_profit_price,
            metadata={'bracket_profit': True, 'bracket_parent': self.entry_order.id}
        )
        
        return [self.entry_order, self.stop_order, self.profit_order]
    
    def on_entry_filled(self) -> List[Order]:
        """Called when entry fills - returns stop and profit orders to place"""
        self.status = "entry_filled"
        return [self.stop_order, self.profit_order]
    
    def on_exit_filled(self, order: Order) -> Optional[Order]:
        """
        Called when stop or profit fills.
        Returns the other order to cancel, or None if already handled.
        """
        self.status = "completed"
        
        if order.id == self.stop_order.id:
            return self.profit_order  # Cancel profit order
        elif order.id == self.profit_order.id:
            return self.stop_order  # Cancel stop order
        
        return None
    
    def get_risk_reward_ratio(self) -> float:
        """Calculate risk/reward ratio"""
        entry = self.entry_price or 0  # Use 0 for market orders (unknown)
        if entry == 0:
            return 0.0
        
        risk = abs(entry - self.stop_loss_price)
        reward = abs(self.take_profit_price - entry)
        
        return reward / risk if risk > 0 else 0.0
    
    def get_status_dict(self) -> Dict:
        """Get full bracket status"""
        return {
            'status': self.status,
            'entry': self.entry_order.to_dict() if self.entry_order else None,
            'stop_loss': self.stop_order.to_dict() if self.stop_order else None,
            'take_profit': self.profit_order.to_dict() if self.profit_order else None,
            'risk_reward_ratio': self.get_risk_reward_ratio()
        }


class AdvancedOrderManager:
    """
    Manages advanced order types and their lifecycle.
    
    Handles the complexity of multi-part orders like icebergs,
    trailing stops, and bracket orders.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.iceberg_orders: Dict[str, IcebergOrder] = {}
        self.trailing_stops: Dict[str, TrailingStopOrder] = {}
        self.bracket_orders: Dict[str, BracketOrder] = {}
        self._lock = threading.Lock()
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None
    
    def start(self):
        """Start the advanced order monitor"""
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
        self.logger.info("Advanced order manager started")
    
    def stop(self):
        """Stop the advanced order monitor"""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        self.logger.info("Advanced order manager stopped")
    
    def _monitor_loop(self):
        """Background monitoring for trailing stops"""
        while self._running:
            # Trailing stops need price updates - in real implementation
            # this would connect to market data feed
            time.sleep(1)
    
    def create_iceberg(self, symbol: str, side: OrderSide,
                       total_amount: float, display_size: float,
                       price: Optional[float] = None) -> IcebergOrder:
        """Create a new iceberg order"""
        iceberg = IcebergOrder(
            total_amount=total_amount,
            display_size=display_size,
            symbol=symbol,
            side=side,
            price=price
        )
        
        with self._lock:
            self.iceberg_orders[iceberg.orders[0].id if iceberg.orders else str(id(iceberg))] = iceberg
        
        self.logger.info(f"Created iceberg order: {total_amount} {symbol} "
                        f"(display: {display_size})")
        return iceberg
    
    def create_trailing_stop(self, symbol: str, side: OrderSide,
                            amount: float, trail_amount: float = None,
                            trail_percent: float = None) -> TrailingStopOrder:
        """Create a new trailing stop order"""
        trailing = TrailingStopOrder(
            symbol=symbol,
            side=side,
            amount=amount,
            trail_amount=trail_amount,
            trail_percent=trail_percent
        )
        
        with self._lock:
            self.trailing_stops[f"ts_{symbol}_{int(time.time() * 1000)}"] = trailing
        
        self.logger.info(f"Created trailing stop: {side.value} {amount} {symbol}")
        return trailing
    
    def create_bracket(self, symbol: str, side: OrderSide,
                      amount: float, stop_loss: float,
                      take_profit: float,
                      entry_price: Optional[float] = None) -> BracketOrder:
        """Create a new bracket order"""
        bracket = BracketOrder(
            symbol=symbol,
            side=side,
            amount=amount,
            entry_price=entry_price,
            stop_loss_price=stop_loss,
            take_profit_price=take_profit
        )
        
        with self._lock:
            self.bracket_orders[bracket.entry_order.id] = bracket
        
        ratio = bracket.get_risk_reward_ratio()
        self.logger.info(f"Created bracket order: {side.value} {amount} {symbol} "
                        f"(R:R = 1:{ratio:.2f})")
        return bracket
    
    def update_trailing_stop(self, order_id: str, current_price: float) -> Optional[Order]:
        """Update a trailing stop with new price"""
        with self._lock:
            trailing = self.trailing_stops.get(order_id)
        
        if trailing:
            return trailing.update_price(current_price)
        return None
    
    def get_all_status(self) -> Dict:
        """Get status of all advanced orders"""
        return {
            'iceberg_orders': len(self.iceberg_orders),
            'trailing_stops': len(self.trailing_stops),
            'bracket_orders': len(self.bracket_orders),
            'iceberg_details': {k: v.get_progress() for k, v in self.iceberg_orders.items()},
            'trailing_details': {k: v.get_status() for k, v in self.trailing_stops.items()}
        }
