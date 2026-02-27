"""
Apex Execution Module

Handles order execution across multiple exchanges with:
- Smart order routing
- Advanced order types (iceberg, trailing stop, bracket)
- Execution algorithms (TWAP, VWAP, POV)
- Multi-exchange management
- Arbitrage detection
"""

from .manager import ExchangeManager
from .routing import SmartOrderRouter, RoutingPriority
from .orders.manager import OrderManager
from .orders.advanced import (
    AdvancedOrderManager,
    IcebergOrder,
    TrailingStopOrder,
    BracketOrder,
    AdvancedOrderType
)
from .orders.algorithms import (
    ExecutionEngine,
    TWAPExecutor,
    VWAPExecutor,
    POVExecutor,
    AlgoType,
    AlgoStatus,
    MarketVolumeProfile
)

__all__ = [
    # Exchange management
    'ExchangeManager',
    'SmartOrderRouter',
    'RoutingPriority',
    
    # Order management
    'OrderManager',
    'AdvancedOrderManager',
    
    # Advanced orders
    'IcebergOrder',
    'TrailingStopOrder',
    'BracketOrder',
    'AdvancedOrderType',
    
    # Execution algorithms
    'ExecutionEngine',
    'TWAPExecutor',
    'VWAPExecutor',
    'POVExecutor',
    'AlgoType',
    'AlgoStatus',
    'MarketVolumeProfile',
]
