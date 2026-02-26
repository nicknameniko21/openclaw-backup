"""
Risk Management System
Controls position sizing, stop losses, and portfolio risk.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging


class RiskLevel(Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


@dataclass
class RiskConfig:
    """Risk management configuration"""
    max_position_size: float = 0.1  # Max 10% of portfolio per position
    max_daily_loss: float = 0.05    # Max 5% daily loss
    max_total_risk: float = 0.2     # Max 20% total portfolio risk
    stop_loss_percent: float = 0.02  # 2% stop loss
    take_profit_percent: float = 0.05  # 5% take profit
    risk_level: RiskLevel = RiskLevel.MODERATE
    
    # Risk level presets
    @classmethod
    def conservative(cls):
        return cls(
            max_position_size=0.05,
            max_daily_loss=0.03,
            max_total_risk=0.1,
            stop_loss_percent=0.015,
            take_profit_percent=0.03,
            risk_level=RiskLevel.CONSERVATIVE
        )
    
    @classmethod
    def aggressive(cls):
        return cls(
            max_position_size=0.2,
            max_daily_loss=0.1,
            max_total_risk=0.3,
            stop_loss_percent=0.03,
            take_profit_percent=0.1,
            risk_level=RiskLevel.AGGRESSIVE
        )


class RiskManager:
    """
    Manages trading risk across all strategies.
    
    Features:
    - Position sizing based on risk parameters
    - Stop loss and take profit calculations
    - Daily loss tracking
    - Portfolio risk monitoring
    """
    
    def __init__(self, config: RiskConfig = None):
        self.config = config or RiskConfig()
        self.daily_pnl = 0.0
        self.total_risk = 0.0
        self.positions_risk: Dict[str, float] = {}
        self.logger = logging.getLogger(__name__)
        
    def calculate_position_size(self, portfolio_value: float, 
                                entry_price: float, 
                                stop_loss_price: float) -> float:
        """
        Calculate position size based on risk parameters.
        
        Args:
            portfolio_value: Total portfolio value
            entry_price: Entry price for the trade
            stop_loss_price: Stop loss price
            
        Returns:
            Position size in units
        """
        # Risk per trade (2% of portfolio)
        risk_amount = portfolio_value * self.config.stop_loss_percent
        
        # Risk per unit
        risk_per_unit = abs(entry_price - stop_loss_price)
        
        if risk_per_unit == 0:
            self.logger.warning("Risk per unit is zero, using max position size")
            return portfolio_value * self.config.max_position_size / entry_price
        
        # Position size based on risk
        position_size = risk_amount / risk_per_unit
        
        # Cap at max position size
        max_position_value = portfolio_value * self.config.max_position_size
        max_position_size = max_position_value / entry_price
        
        final_size = min(position_size, max_position_size)
        
        self.logger.info(f"Position size: {final_size:.4f} units "
                        f"(Risk: ${risk_amount:.2f})")
        
        return final_size
    
    def calculate_stop_loss(self, entry_price: float, 
                           side: str = 'long') -> float:
        """
        Calculate stop loss price.
        
        Args:
            entry_price: Entry price
            side: 'long' or 'short'
            
        Returns:
            Stop loss price
        """
        if side == 'long':
            return entry_price * (1 - self.config.stop_loss_percent)
        else:
            return entry_price * (1 + self.config.stop_loss_percent)
    
    def calculate_take_profit(self, entry_price: float, 
                             side: str = 'long') -> float:
        """
        Calculate take profit price.
        
        Args:
            entry_price: Entry price
            side: 'long' or 'short'
            
        Returns:
            Take profit price
        """
        if side == 'long':
            return entry_price * (1 + self.config.take_profit_percent)
        else:
            return entry_price * (1 - self.config.take_profit_percent)
    
    def check_daily_loss_limit(self, current_pnl: float) -> bool:
        """
        Check if daily loss limit has been reached.
        
        Args:
            current_pnl: Current day's P&L
            
        Returns:
            True if trading should stop
        """
        self.daily_pnl = current_pnl
        daily_loss_percent = abs(min(0, self.daily_pnl))
        
        if daily_loss_percent >= self.config.max_daily_loss:
            self.logger.error(f"Daily loss limit reached: {daily_loss_percent:.2%}")
            return True
        
        return False
    
    def can_open_position(self, portfolio_value: float, 
                         symbol: str) -> bool:
        """
        Check if a new position can be opened.
        
        Args:
            portfolio_value: Total portfolio value
            symbol: Trading symbol
            
        Returns:
            True if position can be opened
        """
        # Check daily loss limit
        if self.daily_pnl < 0 and abs(self.daily_pnl) >= self.config.max_daily_loss:
            self.logger.warning("Cannot open position: daily loss limit reached")
            return False
        
        # Check total risk
        if self.total_risk >= self.config.max_total_risk:
            self.logger.warning("Cannot open position: max total risk reached")
            return False
        
        # Check if already have position in symbol
        if symbol in self.positions_risk:
            self.logger.warning(f"Already have position in {symbol}")
            return False
        
        return True
    
    def add_position_risk(self, symbol: str, risk_amount: float, 
                         portfolio_value: float):
        """Track risk for a new position"""
        risk_percent = risk_amount / portfolio_value
        self.positions_risk[symbol] = risk_percent
        self.total_risk += risk_percent
        
    def remove_position_risk(self, symbol: str):
        """Remove risk tracking for a closed position"""
        if symbol in self.positions_risk:
            self.total_risk -= self.positions_risk[symbol]
            del self.positions_risk[symbol]
    
    def get_risk_report(self) -> Dict:
        """Generate risk report"""
        return {
            'daily_pnl': self.daily_pnl,
            'total_risk': self.total_risk,
            'max_total_risk': self.config.max_total_risk,
            'positions_risk': self.positions_risk,
            'risk_level': self.config.risk_level.value,
            'can_trade': self.can_open_position(100000, 'TEST')  # Test with dummy value
        }
