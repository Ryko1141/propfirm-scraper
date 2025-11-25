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
    starting_balance: Optional[float] = None  # For total drawdown calculation
    day_start_balance: Optional[float] = None  # Balance at start of trading day
    day_start_equity: Optional[float] = None   # Equity at start of trading day
    
    @property
    def day_start_anchor(self) -> float:
        """
        Get day start anchor - uses whichever is higher (balance or equity).
        This is the reference point for max daily drawdown calculation.
        Falls back to balance if day start values not set.
        """
        if self.day_start_balance is not None and self.day_start_equity is not None:
            return max(self.day_start_balance, self.day_start_equity)
        elif self.day_start_balance is not None:
            return self.day_start_balance
        elif self.day_start_equity is not None:
            return self.day_start_equity
        else:
            # Fallback: use current balance
            return self.balance
    
    @property
    def daily_loss_percent(self) -> float:
        """Calculate daily loss as percentage of balance"""
        return (self.total_profit_loss / self.balance) * 100 if self.balance > 0 else 0
    
    @property
    def daily_drawdown_pct(self) -> float:
        """
        Calculate daily drawdown using "whichever is higher" rule.
        
        Uses the WORST CASE between:
        - Equity-based loss (captures floating losses)
        - Balance-based loss (captures realized losses)
        
        This ensures we can't "hide" risk in floating drawdown.
        Returns negative value for losses (e.g., -3.5% for 3.5% loss).
        """
        anchor = self.day_start_anchor
        
        if anchor <= 0:
            return 0.0
        
        # Calculate loss from anchor using both equity and balance
        daily_loss_by_equity = anchor - self.equity
        daily_loss_by_balance = anchor - self.balance
        
        # Use whichever shows the LARGER loss (worst case)
        daily_loss_money = max(daily_loss_by_equity, daily_loss_by_balance)
        
        # Convert to percentage (negative for losses)
        return -(100.0 * daily_loss_money / anchor)
    
    @property
    def total_drawdown_pct(self) -> float:
        """Calculate total drawdown from starting balance as negative percentage"""
        if not self.starting_balance or self.starting_balance <= 0:
            return 0.0
        # Returns negative value for drawdown (e.g., -8.0% for 8% drawdown)
        return ((self.balance - self.starting_balance) / self.starting_balance) * 100


@dataclass
class RuleBreach:
    """Represents a rule breach (warning or hard limit)"""
    level: str  # "WARN" or "HARD"
    code: str  # e.g. "DAILY_DD", "MAX_LOTS", "TOTAL_DD"
    message: str
    value: Optional[float] = None
    threshold: Optional[float] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        """Set timestamp if not provided"""
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    @property
    def severity(self) -> str:
        """Map level to severity for backwards compatibility"""
        return "critical" if self.level == "HARD" else "warning"


@dataclass
class RuleViolation:
    """Legacy model - kept for backwards compatibility"""
    rule_name: str
    severity: str  # "warning", "critical"
    message: str
    timestamp: datetime
    value: Optional[float] = None
    threshold: Optional[float] = None
    
    @classmethod
    def from_breach(cls, breach: RuleBreach) -> 'RuleViolation':
        """Convert RuleBreach to RuleViolation"""
        return cls(
            rule_name=breach.code,
            severity=breach.severity,
            message=breach.message,
            timestamp=breach.timestamp,
            value=breach.value,
            threshold=breach.threshold
        )
