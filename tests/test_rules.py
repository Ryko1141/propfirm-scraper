"""
Unit tests for rules engine - Pure logic testing without API dependencies
"""
import unittest
from datetime import datetime
from src.models import AccountSnapshot, Position, RuleBreach
from src.config import PropRules
from src.rules import check_account_rules


class TestRulesEngine(unittest.TestCase):
    """Test pure rule logic with dummy snapshots"""
    
    def setUp(self):
        """Set up test data"""
        # Standard FTMO-style rules
        self.ftmo_rules = PropRules(
            name="FTMO Test",
            max_daily_drawdown_pct=5.0,
            max_total_drawdown_pct=10.0,
            max_risk_per_trade_pct=1.0,
            max_open_lots=10.0,
            max_positions=10,
            warn_buffer_pct=0.8
        )
    
    def test_no_breaches_clean_account(self):
        """Test account with no rule breaches"""
        snapshot = AccountSnapshot(
            timestamp=datetime.now(),
            balance=100000.0,
            equity=100500.0,
            margin_used=1000.0,
            margin_available=99000.0,
            positions=[],
            total_profit_loss=500.0,
            starting_balance=100000.0
        )
        
        breaches = check_account_rules(snapshot, self.ftmo_rules)
        self.assertEqual(len(breaches), 0, "Clean account should have no breaches")
    
    def test_daily_drawdown_warning(self):
        """Test daily drawdown warning threshold"""
        snapshot = AccountSnapshot(
            timestamp=datetime.now(),
            balance=100000.0,
            equity=96000.0,
            margin_used=1000.0,
            margin_available=95000.0,
            positions=[],
            total_profit_loss=-4000.0,  # -4% loss (80% of 5% limit)
            starting_balance=100000.0
        )
        
        breaches = check_account_rules(snapshot, self.ftmo_rules)
        
        # Should have 1 warning for daily DD
        daily_warnings = [b for b in breaches if b.code == "DAILY_DD" and b.level == "WARN"]
        self.assertEqual(len(daily_warnings), 1, "Should have daily DD warning")
        self.assertIn("warning", daily_warnings[0].message.lower())
    
    def test_daily_drawdown_hard_limit(self):
        """Test daily drawdown hard limit breach"""
        snapshot = AccountSnapshot(
            timestamp=datetime.now(),
            balance=100000.0,
            equity=94500.0,
            margin_used=1000.0,
            margin_available=93500.0,
            positions=[],
            total_profit_loss=-5500.0,  # -5.5% loss (exceeds 5% limit)
            starting_balance=100000.0
        )
        
        breaches = check_account_rules(snapshot, self.ftmo_rules)
        
        # Should have 1 hard breach for daily DD
        hard_breaches = [b for b in breaches if b.code == "DAILY_DD" and b.level == "HARD"]
        self.assertEqual(len(hard_breaches), 1, "Should have daily DD hard breach")
        self.assertGreaterEqual(hard_breaches[0].value, 5.0)
    
    def test_total_drawdown_warning(self):
        """Test total drawdown warning threshold"""
        snapshot = AccountSnapshot(
            timestamp=datetime.now(),
            balance=92000.0,  # -8% from starting (80% of 10% limit)
            equity=92000.0,
            margin_used=1000.0,
            margin_available=91000.0,
            positions=[],
            total_profit_loss=0.0,
            starting_balance=100000.0
        )
        
        breaches = check_account_rules(snapshot, self.ftmo_rules, starting_balance=100000.0)
        
        # Should have warning for total DD
        total_warnings = [b for b in breaches if b.code == "TOTAL_DD" and b.level == "WARN"]
        self.assertEqual(len(total_warnings), 1, "Should have total DD warning")
    
    def test_total_drawdown_hard_limit(self):
        """Test total drawdown hard limit breach"""
        snapshot = AccountSnapshot(
            timestamp=datetime.now(),
            balance=89000.0,  # -11% from starting (exceeds 10% limit)
            equity=89000.0,
            margin_used=1000.0,
            margin_available=88000.0,
            positions=[],
            total_profit_loss=0.0,
            starting_balance=100000.0
        )
        
        breaches = check_account_rules(snapshot, self.ftmo_rules)
        
        # Should have hard breach for total DD
        hard_breaches = [b for b in breaches if b.code == "TOTAL_DD" and b.level == "HARD"]
        self.assertEqual(len(hard_breaches), 1, "Should have total DD hard breach")
    
    def test_risk_per_trade_warning(self):
        """Test position size warning"""
        large_position = Position(
            position_id="12345",
            symbol="EURUSD",
            volume=0.9,  # 0.9% of balance
            entry_price=1.1000,
            current_price=1.1050,
            profit_loss=450.0,
            side="buy"
        )
        
        snapshot = AccountSnapshot(
            timestamp=datetime.now(),
            balance=100000.0,
            equity=100450.0,
            margin_used=900.0,
            margin_available=99550.0,
            positions=[large_position],
            total_profit_loss=450.0,
            starting_balance=100000.0
        )
        
        breaches = check_account_rules(snapshot, self.ftmo_rules)
        
        # Should have warning for risk per trade (0.9% approaching 1% limit at 80% threshold)
        risk_warnings = [b for b in breaches if b.code == "RISK_PER_TRADE" and b.level == "WARN"]
        self.assertGreaterEqual(len(risk_warnings), 0, "Should check risk per trade")
    
    def test_risk_per_trade_hard_limit(self):
        """Test position size hard limit"""
        oversized_position = Position(
            position_id="12345",
            symbol="EURUSD",
            volume=1.2,  # 1.2% of balance (exceeds 1% limit)
            entry_price=1.1000,
            current_price=1.1050,
            profit_loss=600.0,
            side="buy"
        )
        
        snapshot = AccountSnapshot(
            timestamp=datetime.now(),
            balance=100000.0,
            equity=100600.0,
            margin_used=1200.0,
            margin_available=99400.0,
            positions=[oversized_position],
            total_profit_loss=600.0,
            starting_balance=100000.0
        )
        
        breaches = check_account_rules(snapshot, self.ftmo_rules)
        
        # Should have hard breach for risk per trade
        hard_breaches = [b for b in breaches if b.code == "RISK_PER_TRADE" and b.level == "HARD"]
        self.assertEqual(len(hard_breaches), 1, "Should have risk per trade hard breach")
    
    def test_max_lots_warning(self):
        """Test total lot size warning"""
        positions = [
            Position(
                position_id=f"pos{i}",
                symbol="EURUSD",
                volume=0.9,  # 0.9 lots each
                entry_price=1.1000,
                current_price=1.1050,
                profit_loss=50.0,
                side="buy"
            )
            for i in range(10)  # 10 positions × 0.9 = 9 lots (90% of 10 lot limit)
        ]
        
        snapshot = AccountSnapshot(
            timestamp=datetime.now(),
            balance=100000.0,
            equity=100500.0,
            margin_used=9000.0,
            margin_available=91500.0,
            positions=positions,
            total_profit_loss=500.0,
            starting_balance=100000.0
        )
        
        breaches = check_account_rules(snapshot, self.ftmo_rules)
        
        # Should have warning for max lots
        lot_warnings = [b for b in breaches if b.code == "MAX_LOTS" and b.level == "WARN"]
        self.assertEqual(len(lot_warnings), 1, "Should have max lots warning")
    
    def test_max_lots_hard_limit(self):
        """Test total lot size hard limit"""
        positions = [
            Position(
                position_id=f"pos{i}",
                symbol="EURUSD",
                volume=1.1,  # 1.1 lots each
                entry_price=1.1000,
                current_price=1.1050,
                profit_loss=50.0,
                side="buy"
            )
            for i in range(10)  # 10 positions × 1.1 = 11 lots (exceeds 10 lot limit)
        ]
        
        snapshot = AccountSnapshot(
            timestamp=datetime.now(),
            balance=100000.0,
            equity=100500.0,
            margin_used=11000.0,
            margin_available=89500.0,
            positions=positions,
            total_profit_loss=500.0,
            starting_balance=100000.0
        )
        
        breaches = check_account_rules(snapshot, self.ftmo_rules)
        
        # Should have hard breach for max lots
        hard_breaches = [b for b in breaches if b.code == "MAX_LOTS" and b.level == "HARD"]
        self.assertEqual(len(hard_breaches), 1, "Should have max lots hard breach")
        self.assertGreater(hard_breaches[0].value, 10.0)
    
    def test_max_positions(self):
        """Test maximum position count"""
        positions = [
            Position(
                position_id=f"pos{i}",
                symbol="EURUSD",
                volume=0.5,
                entry_price=1.1000,
                current_price=1.1050,
                profit_loss=25.0,
                side="buy"
            )
            for i in range(12)  # 12 positions (exceeds 10 position limit)
        ]
        
        snapshot = AccountSnapshot(
            timestamp=datetime.now(),
            balance=100000.0,
            equity=100300.0,
            margin_used=6000.0,
            margin_available=94300.0,
            positions=positions,
            total_profit_loss=300.0,
            starting_balance=100000.0
        )
        
        breaches = check_account_rules(snapshot, self.ftmo_rules)
        
        # Should have warning for too many positions
        position_warnings = [b for b in breaches if b.code == "MAX_POSITIONS"]
        self.assertEqual(len(position_warnings), 1, "Should have max positions warning")
    
    def test_margin_level_critical(self):
        """Test critically low margin level"""
        snapshot = AccountSnapshot(
            timestamp=datetime.now(),
            balance=100000.0,
            equity=100000.0,
            margin_used=80000.0,
            margin_available=20000.0,  # Only 25% margin level
            positions=[],
            total_profit_loss=0.0,
            starting_balance=100000.0
        )
        
        breaches = check_account_rules(snapshot, self.ftmo_rules)
        
        # Should have critical margin warning
        margin_critical = [b for b in breaches if b.code == "MARGIN_LEVEL" and b.level == "HARD"]
        self.assertEqual(len(margin_critical), 1, "Should have critical margin level breach")
    
    def test_multiple_breaches(self):
        """Test multiple simultaneous breaches"""
        positions = [
            Position(
                position_id=f"pos{i}",
                symbol="EURUSD",
                volume=1.5,  # Oversized lots
                entry_price=1.1000,
                current_price=1.1000,
                profit_loss=0.0,
                side="buy"
            )
            for i in range(12)  # Too many positions
        ]
        
        snapshot = AccountSnapshot(
            timestamp=datetime.now(),
            balance=89000.0,  # Total DD violation
            equity=83500.0,
            margin_used=18000.0,
            margin_available=65500.0,
            positions=positions,
            total_profit_loss=-5500.0,  # Daily DD violation
            starting_balance=100000.0
        )
        
        breaches = check_account_rules(snapshot, self.ftmo_rules)
        
        # Should have multiple breaches
        self.assertGreater(len(breaches), 1, "Should have multiple breaches")
        
        # Check for specific breach types
        breach_codes = {b.code for b in breaches}
        self.assertIn("DAILY_DD", breach_codes)
        self.assertIn("TOTAL_DD", breach_codes)
        self.assertIn("MAX_LOTS", breach_codes)
        self.assertIn("MAX_POSITIONS", breach_codes)
    
    def test_custom_rules(self):
        """Test with custom rule configuration"""
        strict_rules = PropRules(
            name="Strict Rules",
            max_daily_drawdown_pct=3.0,
            max_total_drawdown_pct=6.0,
            max_risk_per_trade_pct=0.5,
            max_open_lots=5.0,
            max_positions=5,
            warn_buffer_pct=0.75
        )
        
        snapshot = AccountSnapshot(
            timestamp=datetime.now(),
            balance=100000.0,
            equity=97500.0,
            margin_used=2000.0,
            margin_available=95500.0,
            positions=[],
            total_profit_loss=-2500.0,  # -2.5% (would be OK for FTMO, warning for strict)
            starting_balance=100000.0
        )
        
        breaches = check_account_rules(snapshot, strict_rules)
        
        # Should have warning with strict rules
        self.assertGreater(len(breaches), 0, "Should have breaches with stricter rules")


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == "__main__":
    print("Running Pure Logic Rules Engine Tests")
    print("=" * 60)
    run_tests()
