"""
Main runner for the prop risk monitor
"""
import os
import time
from datetime import datetime
from src.config import Config, AccountConfig, AccountManager
from src.models import AccountSnapshot, Position
from src.rules import check_account_rules
from src.notifier import notify_console
from rich.console import Console

console = Console()


class RiskMonitor:
    """Main monitoring service"""
    
    def __init__(self, account_config: AccountConfig = None, check_interval: int = None):
        """
        Initialize the risk monitor
        
        Args:
            account_config: AccountConfig object with account and rules (if None, uses env vars)
            check_interval: Time between checks in seconds (overrides account_config)
        """
        # Load account configuration
        if account_config:
            self.account_config = account_config
        else:
            # Create from environment variables for backwards compatibility
            Config.validate()
            firm_name = os.getenv("FIRM_NAME")
            manager = AccountManager()
            self.account_config = manager.create_account_from_env(firm_name)
        
        # Override check interval if provided
        if check_interval:
            self.account_config.check_interval = check_interval
        
        # Initialize the appropriate client based on platform
        if self.account_config.platform == "ctrader":
            from src.ctrader_client import CTraderClient
            self.client = CTraderClient(
                account_id=self.account_config.account_id
            )
            console.print(f"[green]✓[/green] Using cTrader platform for {self.account_config.label}")
        elif self.account_config.platform == "mt5":
            from src.mt5_client import MT5Client
            self.client = MT5Client(
                account_number=int(self.account_config.account_id)
            )
            # Connect to MT5 terminal
            if not self.client.connect():
                raise ConnectionError("Failed to connect to MT5")
            console.print(f"[green]✓[/green] Using MetaTrader 5 platform for {self.account_config.label}")
        else:
            raise ValueError(f"Unsupported platform: {self.account_config.platform}")
        
        self.running = False
        
        # Print startup info
        console.print(f"[bold cyan]🚀 Risk Monitor Started[/bold cyan]")
        console.print(f"Account: [bold]{self.account_config.label}[/bold]")
        console.print(f"Firm: {self.account_config.firm}")
        console.print(f"Platform: {self.account_config.platform.upper()}")
        console.print(f"Starting Balance: ${self.account_config.starting_balance:,.2f}")
        console.print(f"Check Interval: {self.account_config.check_interval}s")
    
    def _create_snapshot(self) -> AccountSnapshot:
        """Create an account snapshot from current API data"""
        # Use the enhanced get_account_snapshot method
        return self.client.get_account_snapshot()
    
    def check_once(self):
        """Perform a single monitoring check"""
        try:
            snapshot = self._create_snapshot()
            
            # Use pure function to check rules
            breaches = check_account_rules(
                snapshot, 
                self.account_config.rules,
                self.account_config.starting_balance
            )
            
            # Notify if breaches found
            if breaches:
                notify_console(self.account_config.label, breaches)
            
            # Status update
            timestamp = snapshot.timestamp.strftime('%H:%M:%S')
            status = f"[dim][{timestamp}] Check complete[/dim] - "
            status += f"Equity: [cyan]${snapshot.equity:,.2f}[/cyan], "
            status += f"P&L: [{'green' if snapshot.total_profit_loss >= 0 else 'red'}]${snapshot.total_profit_loss:,.2f}[/], "
            status += f"Breaches: [{'red' if breaches else 'green'}]{len(breaches)}[/]"
            console.print(status)
            
        except Exception as e:
            console.print(f"[red]Error during check: {e}[/red]")
    
    def start(self):
        """Start the monitoring loop"""
        self.running = True
        
        console.print(f"\n[bold]Starting risk monitor for {self.account_config.label}...[/bold]")
        console.print(f"Firm: {self.account_config.firm} ([cyan]{self.account_config.rules.name}[/cyan])")
        console.print(f"Check interval: {self.account_config.check_interval}s\n")
        
        while self.running:
            self.check_once()
            time.sleep(self.account_config.check_interval)
    
    def stop(self):
        """Stop the monitoring loop"""
        self.running = False
        console.print("[yellow]Risk monitor stopped[/yellow]")


def main():
    """Entry point for the application"""
    monitor = RiskMonitor(check_interval=60)
    
    try:
        monitor.start()
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down...[/yellow]")
        monitor.stop()


if __name__ == "__main__":
    main()
