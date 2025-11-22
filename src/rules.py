"""
Risk monitoring rules and validators
"""
from typing import List
from datetime import datetime
from src.models import AccountSnapshot, RuleViolation
from src.config import Config


class RiskRuleEngine:
    """Engine for evaluating risk rules against account state"""
    
    def __init__(self):
        self.max_daily_loss_percent = Config.MAX_DAILY_LOSS_PERCENT
        self.max_position_size_percent = Config.MAX_POSITION_SIZE_PERCENT
    
    def evaluate(self, snapshot: AccountSnapshot) -> List[RuleViolation]:
        """Evaluate all rules against account snapshot"""
        violations = []
        
        # Check daily loss limit
        daily_loss_violation = self._check_daily_loss(snapshot)
        if daily_loss_violation:
            violations.append(daily_loss_violation)
        
        # Check position size limits
        position_violations = self._check_position_sizes(snapshot)
        violations.extend(position_violations)
        
        # Check margin levels
        margin_violation = self._check_margin_level(snapshot)
        if margin_violation:
            violations.append(margin_violation)
        
        return violations
    
    def _check_daily_loss(self, snapshot: AccountSnapshot) -> RuleViolation:
        """Check if daily loss exceeds maximum threshold"""
        daily_loss_pct = snapshot.daily_loss_percent
        
        if daily_loss_pct < -self.max_daily_loss_percent:
            return RuleViolation(
                rule_name="Daily Loss Limit",
                severity="critical",
                message=f"Daily loss of {daily_loss_pct:.2f}% exceeds limit of {self.max_daily_loss_percent}%",
                timestamp=datetime.now(),
                value=daily_loss_pct,
                threshold=self.max_daily_loss_percent
            )
        return None
    
    def _check_position_sizes(self, snapshot: AccountSnapshot) -> List[RuleViolation]:
        """Check if any position exceeds maximum size threshold"""
        violations = []
        
        for position in snapshot.positions:
            position_value = abs(position.volume * position.current_price)
            position_pct = (position_value / snapshot.equity) * 100
            
            if position_pct > self.max_position_size_percent:
                violations.append(RuleViolation(
                    rule_name="Position Size Limit",
                    severity="warning",
                    message=f"Position {position.symbol} size of {position_pct:.2f}% exceeds limit of {self.max_position_size_percent}%",
                    timestamp=datetime.now(),
                    value=position_pct,
                    threshold=self.max_position_size_percent
                ))
        
        return violations
    
    def _check_margin_level(self, snapshot: AccountSnapshot) -> RuleViolation:
        """Check if margin level is critically low"""
        margin_level = (snapshot.margin_available / snapshot.margin_used * 100) if snapshot.margin_used > 0 else 100
        
        if margin_level < 50:  # Critical threshold
            return RuleViolation(
                rule_name="Low Margin Level",
                severity="critical",
                message=f"Margin level critically low at {margin_level:.2f}%",
                timestamp=datetime.now(),
                value=margin_level,
                threshold=50.0
            )
        elif margin_level < 100:  # Warning threshold
            return RuleViolation(
                rule_name="Low Margin Level",
                severity="warning",
                message=f"Margin level low at {margin_level:.2f}%",
                timestamp=datetime.now(),
                value=margin_level,
                threshold=100.0
            )
        
        return None
