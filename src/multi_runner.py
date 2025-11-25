"""
Multi-account runner for monitoring multiple trading accounts simultaneously
"""
import asyncio
import sys
from pathlib import Path
from rich.console import Console
from src.config import AccountManager
from src.runner import RiskMonitor

console = Console()


class MultiAccountMonitor:
    """Monitor multiple trading accounts simultaneously"""
    
    def __init__(self, config_file: str = "accounts.json"):
        """
        Initialize multi-account monitor
        
        Args:
            config_file: Path to accounts configuration JSON file
        """
        self.config_file = config_file
        self.account_manager = AccountManager(config_file)
        self.monitors = []
        self.running = False
    
    async def monitor_account(self, monitor: RiskMonitor):
        """Run a single account monitor in async loop"""
        while self.running:
            try:
                monitor.check_once()
            except Exception as e:
                console.print(f"[red]Error monitoring {monitor.account_config.label}: {e}[/red]")
            
            await asyncio.sleep(monitor.account_config.check_interval)
    
    async def start_async(self):
        """Start monitoring all enabled accounts asynchronously"""
        self.running = True
        
        enabled_accounts = self.account_manager.get_enabled_accounts()
        
        if not enabled_accounts:
            console.print("[red]No enabled accounts found in configuration![/red]")
            return
        
        console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
        console.print(f"[bold cyan]Starting Multi-Account Risk Monitor[/bold cyan]")
        console.print(f"[bold cyan]{'='*60}[/bold cyan]")
        console.print(f"Monitoring [bold]{len(enabled_accounts)}[/bold] account(s):\n")
        
        # Create monitors for each enabled account
        for account in enabled_accounts:
            try:
                monitor = RiskMonitor(account_config=account)
                self.monitors.append(monitor)
                
                console.print(f"[green]✓[/green] [bold]{account.label}[/bold]")
                console.print(f"  Firm: {account.firm} ([cyan]{account.rules.name}[/cyan])")
                console.print(f"  Platform: {account.platform.upper()}")
                console.print(f"  Starting Balance: ${account.starting_balance:,.2f}")
                console.print(f"  Check Interval: {account.check_interval}s")
                console.print()
                
            except Exception as e:
                console.print(f"[red]✗ Failed to initialize {account.label}: {e}[/red]\n")
        
        if not self.monitors:
            console.print("[red]No monitors initialized successfully![/red]")
            return
        
        console.print(f"[bold cyan]{'='*60}[/bold cyan]\n")
        
        # Run all monitors concurrently
        tasks = [self.monitor_account(monitor) for monitor in self.monitors]
        await asyncio.gather(*tasks)
    
    def start(self):
        """Start the multi-account monitor"""
        try:
            asyncio.run(self.start_async())
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopping all monitors...[/yellow]")
            self.stop()
    
    def stop(self):
        """Stop all monitors"""
        self.running = False
        
        for monitor in self.monitors:
            try:
                monitor.stop()
            except:
                pass
        
        console.print("[yellow]All monitors stopped.[/yellow]")


def main():
    """Entry point for multi-account monitoring"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Multi-Account Prop Risk Monitor")
    parser.add_argument(
        '--config',
        default='accounts.json',
        help='Path to accounts configuration file (default: accounts.json)'
    )
    
    args = parser.parse_args()
    
    if not Path(args.config).exists():
        console.print(f"[red]Error: Configuration file '{args.config}' not found![/red]")
        console.print("\nPlease create an accounts.json file based on accounts.json.example")
        console.print("Example:")
        console.print("  cp accounts.json.example accounts.json")
        console.print("  # Edit accounts.json with your account details")
        sys.exit(1)
    
    monitor = MultiAccountMonitor(config_file=args.config)
    
    try:
        monitor.start()
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down...[/yellow]")
        monitor.stop()


if __name__ == "__main__":
    main()
