"""
Position Tracking System
Tracks open positions and calculates P&L.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import logging


class PositionSide(Enum):
    LONG = "long"
    SHORT = "short"


@dataclass
class Position:
    """Trading position data structure"""
    id: str
    symbol: str
    side: PositionSide
    entry_price: float
    quantity: float
    timestamp: datetime = field(default_factory=datetime.now)
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    metadata: Dict = field(default_factory=dict)
    
    def update_unrealized_pnl(self, current_price: float):
        """Update unrealized P&L based on current price"""
        if self.side == PositionSide.LONG:
            self.unrealized_pnl = (current_price - self.entry_price) * self.quantity
        else:
            self.unrealized_pnl = (self.entry_price - current_price) * self.quantity
    
    def calculate_value(self, current_price: float) -> float:
        """Calculate position value at current price"""
        return self.quantity * current_price
    
    def should_exit(self, current_price: float) -> Optional[str]:
        """
        Check if position should be exited based on stop loss or take profit.
        
        Returns:
            'stop_loss', 'take_profit', or None
        """
        if self.side == PositionSide.LONG:
            if self.stop_loss and current_price <= self.stop_loss:
                return 'stop_loss'
            if self.take_profit and current_price >= self.take_profit:
                return 'take_profit'
        else:  # SHORT
            if self.stop_loss and current_price >= self.stop_loss:
                return 'stop_loss'
            if self.take_profit and current_price <= self.take_profit:
                return 'take_profit'
        
        return None
    
    def to_dict(self) -> Dict:
        """Convert position to dictionary"""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'side': self.side.value,
            'entry_price': self.entry_price,
            'quantity': self.quantity,
            'timestamp': self.timestamp.isoformat(),
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'unrealized_pnl': self.unrealized_pnl,
            'realized_pnl': self.realized_pnl,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Position':
        """Create position from dictionary"""
        return cls(
            id=data['id'],
            symbol=data['symbol'],
            side=PositionSide(data['side']),
            entry_price=data['entry_price'],
            quantity=data['quantity'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            stop_loss=data.get('stop_loss'),
            take_profit=data.get('take_profit'),
            unrealized_pnl=data.get('unrealized_pnl', 0.0),
            realized_pnl=data.get('realized_pnl', 0.0),
            metadata=data.get('metadata', {})
        )


class PositionTracker:
    """
    Tracks all trading positions and calculates portfolio P&L.
    
    Features:
    - Position creation and management
    - Real-time P&L calculation
    - Stop loss / take profit monitoring
    - Position history
    """
    
    def __init__(self, storage_path: str = None):
        self.logger = logging.getLogger(__name__)
        self.positions: Dict[str, Position] = {}
        self.closed_positions: List[Position] = []
        self.storage_path = storage_path
        
        if storage_path:
            self._load_positions()
    
    def open_position(self, symbol: str, side: PositionSide,
                     entry_price: float, quantity: float,
                     stop_loss: float = None, take_profit: float = None,
                     metadata: Dict = None) -> Position:
        """
        Open a new position.
        
        Args:
            symbol: Trading pair symbol
            side: Long or short
            entry_price: Entry price
            quantity: Position size
            stop_loss: Stop loss price
            take_profit: Take profit price
            metadata: Additional position metadata
            
        Returns:
            Created Position object
        """
        position_id = f"pos_{datetime.now().timestamp()}"
        
        position = Position(
            id=position_id,
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit,
            metadata=metadata or {}
        )
        
        self.positions[position_id] = position
        self.logger.info(f"Position opened: {position_id} ({side.value} {quantity} {symbol} @ {entry_price})")
        
        self._save_positions()
        return position
    
    def close_position(self, position_id: str, exit_price: float,
                      exit_reason: str = 'manual') -> Optional[Position]:
        """
        Close a position.
        
        Args:
            position_id: Position ID to close
            exit_price: Exit price
            exit_reason: Reason for closing
            
        Returns:
            Closed Position or None if not found
        """
        if position_id not in self.positions:
            self.logger.warning(f"Position not found: {position_id}")
            return None
        
        position = self.positions.pop(position_id)
        
        # Calculate realized P&L
        position.update_unrealized_pnl(exit_price)
        position.realized_pnl = position.unrealized_pnl
        position.unrealized_pnl = 0.0
        
        position.metadata['exit_price'] = exit_price
        position.metadata['exit_reason'] = exit_reason
        position.metadata['exit_time'] = datetime.now().isoformat()
        
        self.closed_positions.append(position)
        
        self.logger.info(f"Position closed: {position_id} (P&L: {position.realized_pnl:.2f}, Reason: {exit_reason})")
        
        self._save_positions()
        return position
    
    def update_positions(self, prices: Dict[str, float]):
        """
        Update all positions with current prices.
        
        Args:
            prices: Dictionary of symbol -> current price
        """
        for position in self.positions.values():
            if position.symbol in prices:
                position.update_unrealized_pnl(prices[position.symbol])
    
    def check_exit_conditions(self, prices: Dict[str, float]) -> List[tuple]:
        """
        Check all positions for exit conditions.
        
        Args:
            prices: Dictionary of symbol -> current price
            
        Returns:
            List of (position_id, exit_reason) tuples
        """
        exits = []
        
        for position in self.positions.values():
            if position.symbol in prices:
                exit_reason = position.should_exit(prices[position.symbol])
                if exit_reason:
                    exits.append((position.id, exit_reason))
        
        return exits
    
    def get_position(self, position_id: str) -> Optional[Position]:
        """Get position by ID"""
        return self.positions.get(position_id)
    
    def get_positions_by_symbol(self, symbol: str) -> List[Position]:
        """Get all positions for a symbol"""
        return [p for p in self.positions.values() if p.symbol == symbol]
    
    def get_open_positions(self) -> List[Position]:
        """Get all open positions"""
        return list(self.positions.values())
    
    def get_closed_positions(self, limit: int = None) -> List[Position]:
        """Get closed positions"""
        positions = sorted(self.closed_positions, 
                         key=lambda p: p.timestamp, 
                         reverse=True)
        if limit:
            positions = positions[:limit]
        return positions
    
    def get_portfolio_value(self, prices: Dict[str, float]) -> float:
        """
        Calculate total portfolio value.
        
        Args:
            prices: Dictionary of symbol -> current price
            
        Returns:
            Total portfolio value
        """
        total = 0.0
        for position in self.positions.values():
            if position.symbol in prices:
                total += position.calculate_value(prices[position.symbol])
        return total
    
    def get_total_pnl(self) -> Dict:
        """Get total P&L statistics"""
        unrealized = sum(p.unrealized_pnl for p in self.positions.values())
        realized = sum(p.realized_pnl for p in self.closed_positions)
        
        return {
            'unrealized_pnl': unrealized,
            'realized_pnl': realized,
            'total_pnl': unrealized + realized,
            'open_positions': len(self.positions),
            'closed_positions': len(self.closed_positions)
        }
    
    def get_statistics(self) -> Dict:
        """Get position statistics"""
        pnl = self.get_total_pnl()
        
        long_positions = len([p for p in self.positions.values() if p.side == PositionSide.LONG])
        short_positions = len([p for p in self.positions.values() if p.side == PositionSide.SHORT])
        
        winning_trades = len([p for p in self.closed_positions if p.realized_pnl > 0])
        losing_trades = len([p for p in self.closed_positions if p.realized_pnl <= 0])
        
        return {
            **pnl,
            'long_positions': long_positions,
            'short_positions': short_positions,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': winning_trades / len(self.closed_positions) if self.closed_positions else 0.0
        }
    
    def _save_positions(self):
        """Save positions to file"""
        if not self.storage_path:
            return
        
        try:
            data = {
                'open': [p.to_dict() for p in self.positions.values()],
                'closed': [p.to_dict() for p in self.closed_positions]
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving positions: {e}")
    
    def _load_positions(self):
        """Load positions from file"""
        import os
        if not os.path.exists(self.storage_path):
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            for pos_data in data.get('open', []):
                position = Position.from_dict(pos_data)
                self.positions[position.id] = position
            
            for pos_data in data.get('closed', []):
                position = Position.from_dict(pos_data)
                self.closed_positions.append(position)
            
            self.logger.info(f"Loaded {len(self.positions)} open positions, "
                           f"{len(self.closed_positions)} closed positions")
                           
        except Exception as e:
            self.logger.error(f"Error loading positions: {e}")
