"""
Main runner for the prop risk monitor
"""
import time
from datetime import datetime
from src.config import Config
from src.ctrader_client import CTraderClient
from src.models import AccountSnapshot, Position
from src.rules import RiskRuleEngine
from src.notifier import Notifier


class RiskMonitor:
    """Main monitoring service"""
    
    def __init__(self, check_interval: int = 60):
        """
        Initialize the risk monitor
        
        Args:
            check_interval: Time between checks in seconds (default: 60)
        """
        Config.validate()
        
        self.client = CTraderClient()
        self.rule_engine = RiskRuleEngine()
        self.notifier = Notifier()
        self.check_interval = check_interval
        self.running = False
    
    def _create_snapshot(self) -> AccountSnapshot:
        """Create an account snapshot from current API data"""
        # Use the enhanced get_account_snapshot method
        return self.client.get_account_snapshot()
    
    def check_once(self):
        """Perform a single monitoring check"""
        try:
            snapshot = self._create_snapshot()
            violations = self.rule_engine.evaluate(snapshot)
            
            if violations:
                self.notifier.send_violations(violations)
            
            print(f"[{snapshot.timestamp}] Check complete - Equity: ${snapshot.equity:.2f}, P&L: ${snapshot.total_profit_loss:.2f}, Violations: {len(violations)}")
            
        except Exception as e:
            print(f"Error during check: {e}")
            self.notifier.send_status(f"Error during monitoring: {str(e)}")
    
    def start(self):
        """Start the monitoring loop"""
        self.running = True
        self.notifier.send_status("Risk monitor started")
        
        print(f"Starting risk monitor with {self.check_interval}s interval...")
        
        while self.running:
            self.check_once()
            time.sleep(self.check_interval)
    
    def stop(self):
        """Stop the monitoring loop"""
        self.running = False
        self.notifier.send_status("Risk monitor stopped")
        print("Risk monitor stopped")


def main():
    """Entry point for the application"""
    monitor = RiskMonitor(check_interval=60)
    
    try:
        monitor.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
        monitor.stop()


if __name__ == "__main__":
    main()
