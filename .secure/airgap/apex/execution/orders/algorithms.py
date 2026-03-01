"""
Execution Algorithms
Implements institutional-grade order execution algorithms.

TWAP - Time Weighted Average Price
VWAP - Volume Weighted Average Price
POV - Percentage of Volume
Implementation Shortfall - Balance urgency vs market impact
"""

from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import time
import threading
from collections import deque
import pandas as pd
import numpy as np

from .manager import Order, OrderSide, OrderType, OrderStatus


class AlgoType(Enum):
    """Execution algorithm types"""
    TWAP = "twap"           # Time Weighted Average Price
    VWAP = "vwap"           # Volume Weighted Average Price
    POV = "pov"             # Percentage of Volume
    IS = "is"               # Implementation Shortfall


class AlgoStatus(Enum):
    """Algorithm execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


@dataclass
class AlgoPerformance:
    """Performance metrics for execution algorithm"""
    target_price: float = 0.0
    avg_executed_price: float = 0.0
    slippage_bps: float = 0.0           # Slippage in basis points
    market_impact_bps: float = 0.0      # Estimated market impact
    completion_percent: float = 0.0
    orders_placed: int = 0
    orders_filled: int = 0
    volume_executed: float = 0.0
    volume_remaining: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def calculate_slippage(self) -> float:
        """Calculate slippage in basis points"""
        if self.target_price == 0:
            return 0.0
        return ((self.avg_executed_price - self.target_price) / self.target_price) * 10000


@dataclass
class MarketVolumeProfile:
    """Historical volume profile for VWAP calculation"""
    intervals: int = 48                 # 30-min intervals in trading day
    volume_distribution: List[float] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.volume_distribution:
            # Default: U-shaped pattern (higher volume at open/close)
            self.volume_distribution = self._generate_default_profile()
    
    def _generate_default_profile(self) -> List[float]:
        """Generate typical U-shaped intraday volume profile"""
        intervals = self.intervals
        profile = []
        
        for i in range(intervals):
            # U-shape: higher at start and end of day
            x = i / (intervals - 1)  # 0 to 1
            # Parabola opening upward, minimum at midday
            volume = 0.5 + 2 * (x - 0.5) ** 2
            profile.append(volume)
        
        # Normalize to sum to 1
        total = sum(profile)
        return [v / total for v in profile]
    
    def get_interval_volume(self, interval: int, total_volume: float) -> float:
        """Get expected volume for a specific interval"""
        if 0 <= interval < len(self.volume_distribution):
            return total_volume * self.volume_distribution[interval]
        return total_volume / len(self.volume_distribution)


class TWAPExecutor:
    """
    Time Weighted Average Price Execution
    
    Splits large order into equal chunks executed at regular intervals.
    Goal: Achieve average price close to the time-weighted average market price.
    
    Best for: Low urgency, minimizing market impact, predictable execution
    
    Example: Execute 10,000 shares over 4 hours with 15-min intervals
    = 16 orders of 625 shares each
    """
    
    def __init__(self, symbol: str, side: OrderSide, total_amount: float,
                 duration_minutes: int, interval_seconds: int = 60,
                 price_limit: Optional[float] = None):
        """
        Initialize TWAP executor.
        
        Args:
            symbol: Trading pair
            side: Buy or sell
            total_amount: Total quantity to execute
            duration_minutes: Total execution time
            interval_seconds: Time between child orders
            price_limit: Optional price limit (None for no limit)
        """
        self.symbol = symbol
        self.side = side
        self.total_amount = total_amount
        self.duration_minutes = duration_minutes
        self.interval_seconds = interval_seconds
        self.price_limit = price_limit
        
        # Calculate slices
        total_seconds = duration_minutes * 60
        self.num_slices = max(1, total_seconds // interval_seconds)
        self.slice_size = total_amount / self.num_slices
        
        # State
        self.status = AlgoStatus.PENDING
        self.slices_completed = 0
        self.slices: List[Order] = []
        self.performance = AlgoPerformance(
            volume_remaining=total_amount
        )
        
        self.logger = logging.getLogger(f"TWAP.{symbol}")
    
    def generate_slices(self) -> List[Order]:
        """Generate all TWAP child orders"""
        orders = []
        
        for i in range(self.num_slices):
            # Adjust last slice for rounding
            amount = self.slice_size
            if i == self.num_slices - 1:
                amount = self.total_amount - (self.slice_size * (self.num_slices - 1))
            
            order_type = OrderType.LIMIT if self.price_limit else OrderType.MARKET
            
            order = Order(
                id=f"twap_{self.symbol}_{i}_{int(time.time() * 1000)}",
                symbol=self.symbol,
                side=self.side,
                order_type=order_type,
                amount=round(amount, 8),
                price=self.price_limit,
                metadata={
                    'twap_slice': i + 1,
                    'twap_total_slices': self.num_slices,
                    'twap_parent': True
                }
            )
            orders.append(order)
        
        self.slices = orders
        self.performance.orders_placed = len(orders)
        return orders
    
    def on_slice_filled(self, order: Order, filled_amount: float, 
                       avg_price: float) -> Optional[Order]:
        """
        Called when a slice fills.
        Returns next slice if ready, None otherwise.
        """
        self.slices_completed += 1
        self.performance.volume_executed += filled_amount
        self.performance.volume_remaining -= filled_amount
        
        # Update average price (volume-weighted)
        total_vol = self.performance.volume_executed
        if total_vol > 0:
            prev_vol = total_vol - filled_amount
            self.performance.avg_executed_price = (
                (self.performance.avg_executed_price * prev_vol + avg_price * filled_amount) 
                / total_vol
            )
        
        self.performance.completion_percent = (
            self.performance.volume_executed / self.total_amount * 100
        )
        
        if self.slices_completed >= self.num_slices:
            self.status = AlgoStatus.COMPLETED
            self.performance.end_time = datetime.now()
            return None
        
        return self.slices[self.slices_completed] if self.slices_completed < len(self.slices) else None
    
    def get_status(self) -> Dict:
        """Get current TWAP status"""
        return {
            'status': self.status.value,
            'progress': f"{self.slices_completed}/{self.num_slices}",
            'percent_complete': self.performance.completion_percent,
            'volume_executed': self.performance.volume_executed,
            'avg_price': self.performance.avg_executed_price,
            'slippage_bps': self.performance.calculate_slippage()
        }


class VWAPExecutor:
    """
    Volume Weighted Average Price Execution
    
    Splits order based on historical volume profile of the security.
    Executes more when volume is typically higher (open/close),
    less during quiet periods (midday).
    
    Goal: Achieve average price close to the market's volume-weighted average.
    
    Best for: Large orders where blending in with natural flow matters
    
    Example: If historical volume is 30% in first hour, 20% midday, 50% close,
    VWAP front-loads and back-loads the order accordingly.
    """
    
    def __init__(self, symbol: str, side: OrderSide, total_amount: float,
                 duration_minutes: int, volume_profile: MarketVolumeProfile = None,
                 price_limit: Optional[float] = None,
                 participation_rate: float = 0.1):  # 10% of expected volume
        """
        Initialize VWAP executor.
        
        Args:
            symbol: Trading pair
            side: Buy or sell
            total_amount: Total quantity to execute
            duration_minutes: Total execution time
            volume_profile: Historical volume distribution
            price_limit: Optional price limit
            participation_rate: Target % of volume (0.1 = 10%)
        """
        self.symbol = symbol
        self.side = side
        self.total_amount = total_amount
        self.duration_minutes = duration_minutes
        self.volume_profile = volume_profile or MarketVolumeProfile()
        self.price_limit = price_limit
        self.participation_rate = participation_rate
        
        # Calculate intervals (30-min buckets)
        self.interval_minutes = 30
        self.num_intervals = max(1, duration_minutes // self.interval_minutes)
        
        # Adjust intervals to match volume profile
        self.volume_profile.intervals = self.num_intervals
        if len(self.volume_profile.volume_distribution) != self.num_intervals:
            self.volume_profile.volume_distribution = (
                self.volume_profile._generate_default_profile()
            )
        
        # State
        self.status = AlgoStatus.PENDING
        self.current_interval = 0
        self.slices: List[Order] = []
        self.performance = AlgoPerformance(
            volume_remaining=total_amount
        )
        
        self.logger = logging.getLogger(f"VWAP.{symbol}")
    
    def generate_slices(self) -> List[Order]:
        """Generate VWAP slices based on volume profile"""
        orders = []
        remaining = self.total_amount
        
        for i in range(self.num_intervals):
            # Get target volume for this interval
            interval_pct = self.volume_profile.volume_distribution[i]
            target_amount = self.total_amount * interval_pct
            
            # Adjust for participation rate
            slice_amount = target_amount * self.participation_rate
            
            # Ensure we don't exceed remaining
            slice_amount = min(slice_amount, remaining)
            
            if slice_amount > 0:
                order_type = OrderType.LIMIT if self.price_limit else OrderType.MARKET
                
                order = Order(
                    id=f"vwap_{self.symbol}_{i}_{int(time.time() * 1000)}",
                    symbol=self.symbol,
                    side=self.side,
                    order_type=order_type,
                    amount=round(slice_amount, 8),
                    price=self.price_limit,
                    metadata={
                        'vwap_slice': i + 1,
                        'vwap_total_slices': self.num_intervals,
                        'vwap_interval_pct': interval_pct,
                        'vwap_parent': True
                    }
                )
                orders.append(order)
                remaining -= slice_amount
        
        # Add any remainder to last slice
        if remaining > 0 and orders:
            orders[-1].amount += remaining
        
        self.slices = orders
        self.performance.orders_placed = len(orders)
        return orders
    
    def on_slice_filled(self, order: Order, filled_amount: float,
                       avg_price: float) -> Optional[Order]:
        """Called when a VWAP slice fills"""
        self.current_interval += 1
        self.performance.volume_executed += filled_amount
        self.performance.volume_remaining -= filled_amount
        
        # Update VWAP
        total_vol = self.performance.volume_executed
        if total_vol > 0:
            prev_vol = total_vol - filled_amount
            self.performance.avg_executed_price = (
                (self.performance.avg_executed_price * prev_vol + avg_price * filled_amount)
                / total_vol
            )
        
        self.performance.completion_percent = (
            self.performance.volume_executed / self.total_amount * 100
        )
        
        if self.current_interval >= len(self.slices):
            self.status = AlgoStatus.COMPLETED
            self.performance.end_time = datetime.now()
            return None
        
        return self.slices[self.current_interval]
    
    def get_status(self) -> Dict:
        """Get VWAP execution status"""
        return {
            'status': self.status.value,
            'current_interval': self.current_interval,
            'total_intervals': self.num_intervals,
            'percent_complete': self.performance.completion_percent,
            'volume_executed': self.performance.volume_executed,
            'avg_price': self.performance.avg_executed_price,
            'target_vwap': self.performance.target_price,
            'slippage_bps': self.performance.calculate_slippage()
        }


class POVExecutor:
    """
    Percentage of Volume Execution
    
    Executes at a fixed percentage of observed market volume.
    Adapts to real-time market conditions.
    
    Goal: Maintain consistent participation in market flow without
    dominating the order book.
    
    Best for: Very large orders where minimal market impact is critical
    
    Example: Target 5% of volume - if market trades 1000/min, you trade 50/min
    """
    
    def __init__(self, symbol: str, side: OrderSide, total_amount: float,
                 target_pov: float = 0.05,  # 5% of volume
                 min_interval_seconds: int = 60,
                 max_duration_minutes: int = 480):
        """
        Initialize POV executor.
        
        Args:
            symbol: Trading pair
            side: Buy or sell
            total_amount: Total quantity to execute
            target_pov: Target percentage of market volume (0.05 = 5%)
            min_interval_seconds: Minimum time between slices
            max_duration_minutes: Maximum execution time
        """
        self.symbol = symbol
        self.side = side
        self.total_amount = total_amount
        self.target_pov = target_pov
        self.min_interval_seconds = min_interval_seconds
        self.max_duration_minutes = max_duration_minutes
        
        # State
        self.status = AlgoStatus.PENDING
        self.volume_observed = 0.0
        self.volume_executed = 0.0
        self.slices_placed = 0
        self.last_slice_time = 0
        
        # Volume tracking
        self.volume_history: deque = deque(maxlen=100)
        
        self.performance = AlgoPerformance(
            volume_remaining=total_amount
        )
        
        self.logger = logging.getLogger(f"POV.{symbol}")
    
    def calculate_next_slice(self, current_market_volume: float) -> Optional[Order]:
        """
        Calculate next slice based on observed market volume.
        
        Args:
            current_market_volume: Volume traded since last check
            
        Returns:
            Order if slice should be placed, None otherwise
        """
        # Check minimum interval
        current_time = time.time()
        if current_time - self.last_slice_time < self.min_interval_seconds:
            return None
        
        # Calculate target slice size
        target_slice = current_market_volume * self.target_pov
        
        # Don't exceed remaining amount
        remaining = self.total_amount - self.volume_executed
        slice_amount = min(target_slice, remaining)
        
        if slice_amount <= 0:
            return None
        
        # Create order
        order = Order(
            id=f"pov_{self.symbol}_{self.slices_placed}_{int(time.time() * 1000)}",
            symbol=self.symbol,
            side=self.side,
            order_type=OrderType.MARKET,
            amount=round(slice_amount, 8),
            metadata={
                'pov_slice': self.slices_placed + 1,
                'pov_target': self.target_pov,
                'pov_market_vol': current_market_volume,
                'pov_parent': True
            }
        )
        
        self.slices_placed += 1
        self.last_slice_time = current_time
        
        return order
    
    def on_slice_filled(self, filled_amount: float, avg_price: float):
        """Called when POV slice fills"""
        self.volume_executed += filled_amount
        self.performance.volume_executed = self.volume_executed
        self.performance.volume_remaining = self.total_amount - self.volume_executed
        
        # Update average price
        total_vol = self.volume_executed
        if total_vol > 0:
            prev_vol = total_vol - filled_amount
            self.performance.avg_executed_price = (
                (self.performance.avg_executed_price * prev_vol + avg_price * filled_amount)
                / total_vol
            )
        
        self.performance.completion_percent = (
            self.volume_executed / self.total_amount * 100
        )
        
        if self.volume_executed >= self.total_amount:
            self.status = AlgoStatus.COMPLETED
            self.performance.end_time = datetime.now()
    
    def get_status(self) -> Dict:
        """Get POV execution status"""
        return {
            'status': self.status.value,
            'target_pov': self.target_pov * 100,
            'volume_executed': self.volume_executed,
            'volume_observed': self.volume_observed,
            'actual_pov': (self.volume_executed / self.volume_observed * 100) 
                         if self.volume_observed > 0 else 0,
            'percent_complete': self.performance.completion_percent,
            'avg_price': self.performance.avg_executed_price
        }


class ExecutionEngine:
    """
    Central execution engine for managing algorithmic orders.
    
    Coordinates multiple algo executions and provides unified interface.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.active_executions: Dict[str, object] = {}
        self.performance_history: List[AlgoPerformance] = []
        self._lock = threading.Lock()
    
    def start_twap(self, symbol: str, side: OrderSide, amount: float,
                   duration_minutes: int, interval_seconds: int = 60,
                   price_limit: Optional[float] = None) -> str:
        """Start a new TWAP execution"""
        executor = TWAPExecutor(
            symbol=symbol,
            side=side,
            total_amount=amount,
            duration_minutes=duration_minutes,
            interval_seconds=interval_seconds,
            price_limit=price_limit
        )
        
        execution_id = f"twap_{symbol}_{int(time.time() * 1000)}"
        
        with self._lock:
            self.active_executions[execution_id] = executor
        
        executor.status = AlgoStatus.RUNNING
        executor.performance.start_time = datetime.now()
        
        self.logger.info(f"Started TWAP: {side.value} {amount} {symbol} "
                        f"over {duration_minutes}min")
        
        return execution_id
    
    def start_vwap(self, symbol: str, side: OrderSide, amount: float,
                   duration_minutes: int, price_limit: Optional[float] = None,
                   participation_rate: float = 0.1) -> str:
        """Start a new VWAP execution"""
        executor = VWAPExecutor(
            symbol=symbol,
            side=side,
            total_amount=amount,
            duration_minutes=duration_minutes,
            price_limit=price_limit,
            participation_rate=participation_rate
        )
        
        execution_id = f"vwap_{symbol}_{int(time.time() * 1000)}"
        
        with self._lock:
            self.active_executions[execution_id] = executor
        
        executor.status = AlgoStatus.RUNNING
        executor.performance.start_time = datetime.now()
        
        self.logger.info(f"Started VWAP: {side.value} {amount} {symbol}")
        
        return execution_id
    
    def start_pov(self, symbol: str, side: OrderSide, amount: float,
                  target_pov: float = 0.05) -> str:
        """Start a new POV execution"""
        executor = POVExecutor(
            symbol=symbol,
            side=side,
            total_amount=amount,
            target_pov=target_pov
        )
        
        execution_id = f"pov_{symbol}_{int(time.time() * 1000)}"
        
        with self._lock:
            self.active_executions[execution_id] = executor
        
        executor.status = AlgoStatus.RUNNING
        executor.performance.start_time = datetime.now()
        
        self.logger.info(f"Started POV: {side.value} {amount} {symbol} "
                        f"at {target_pov*100}% participation")
        
        return execution_id
    
    def get_execution(self, execution_id: str) -> Optional[object]:
        """Get execution by ID"""
        with self._lock:
            return self.active_executions.get(execution_id)
    
    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel an active execution"""
        with self._lock:
            executor = self.active_executions.get(execution_id)
            if executor:
                executor.status = AlgoStatus.CANCELLED
                executor.performance.end_time = datetime.now()
                self.performance_history.append(executor.performance)
                del self.active_executions[execution_id]
                return True
        return False
    
    def get_all_status(self) -> Dict:
        """Get status of all executions"""
        return {
            'active_count': len(self.active_executions),
            'history_count': len(self.performance_history),
            'executions': {
                k: v.get_status() for k, v in self.active_executions.items()
            }
        }
