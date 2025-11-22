"""
Data models for trading account monitoring
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class Position:
    """Represents an open trading position"""
    position_id: str
    symbol: str
    volume: float
    entry_price: float
    current_price: float
    profit_loss: float
    side: str  # "buy" or "sell"
    
    @property
    def profit_loss_percent(self) -> float:
        """Calculate P&L as percentage"""
        if self.side == "buy":
            return ((self.current_price - self.entry_price) / self.entry_price) * 100
        else:
            return ((self.entry_price - self.current_price) / self.entry_price) * 100


@dataclass
class AccountSnapshot:
    """Snapshot of account state at a point in time"""
    timestamp: datetime
    balance: float
    equity: float
    margin_used: float
    margin_available: float
    positions: List[Position]
    total_profit_loss: float
    
    @property
    def daily_loss_percent(self) -> float:
        """Calculate daily loss as percentage of balance"""
        return (self.total_profit_loss / self.balance) * 100 if self.balance > 0 else 0


@dataclass
class RuleViolation:
    """Represents a violated risk rule"""
    rule_name: str
    severity: str  # "warning", "critical"
    message: str
    timestamp: datetime
    value: Optional[float] = None
    threshold: Optional[float] = None
