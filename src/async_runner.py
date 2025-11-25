"""
Async runner for real-time WebSocket streaming
This is an advanced alternative to the polling-based runner
"""
import asyncio
from datetime import datetime
from rich.console import Console
from src.config import Config, AccountConfig, AccountManager
from src.ctrader_client import CTraderClient
from src.rules import check_account_rules
from src.notifier import notify_console

console = Console()


class AsyncRiskMonitor:
    """Real-time monitoring service using WebSocket streaming"""
    
    def __init__(self, account_config: AccountConfig = None):
        """
        Initialize the async risk monitor
        
        Args:
            account_config: AccountConfig object with account and rules (if None, uses env vars)
        """
        # Load account configuration
        if account_config:
            self.account_config = account_config
        else:
            # Create from environment variables for backwards compatibility
            Config.validate()
            import os
            firm_name = os.getenv("FIRM_NAME")
            manager = AccountManager()
            self.account_config = manager.create_account_from_env(firm_name)
        
        # Only works with cTrader
        if self.account_config.platform != "ctrader":
            raise ValueError("Async runner only supports cTrader platform (WebSocket streaming)")
        
        self.client = CTraderClient(account_id=self.account_config.account_id)
        self.running = False
        
        # Print startup info
        console.print(f"[bold cyan]🚀 Async Risk Monitor (WebSocket)[/bold cyan]")
        console.print(f"Account: [bold]{self.account_config.label}[/bold]")
        console.print(f"Firm: {self.account_config.firm}")
        console.print(f"Starting Balance: ${self.account_config.starting_balance:,.2f}")
    
    async def handle_account_update(self, data: dict):
        """
        Handle incoming WebSocket updates from cTrader
        
        Args:
            data: WebSocket message containing account/position updates
        """
        try:
            payload_type = data.get("payloadType")
            
            # Handle different message types
            if payload_type == 2126:  # ProtoOASpotEvent (price update)
                # Price updates - might trigger position P&L changes
                pass
            
            elif payload_type == 2132:  # ProtoOAExecutionEvent (order/position event)
                # Position opened, closed, or modified
                console.print(f"[dim]Execution event received[/dim]")
                await self.check_rules()
            
            elif payload_type == 2142:  # ProtoOAAccountAuthRes
                console.print("[green]✓ Account authenticated via WebSocket[/green]")
            
            else:
                console.print(f"[dim]Received message type {payload_type}[/dim]")
                
        except Exception as e:
            console.print(f"[red]Error handling update: {e}[/red]")
    
    async def check_rules(self):
        """Perform a risk check using current account state"""
        try:
            # Get snapshot using REST (WebSocket doesn't provide full snapshot)
            snapshot = self.client.get_account_snapshot()
            
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
    
    async def periodic_check(self, interval: int = 60):
        """
        Perform periodic checks in addition to event-driven checks
        
        Args:
            interval: Time between checks in seconds
        """
        while self.running:
            await self.check_rules()
            await asyncio.sleep(interval)
    
    async def start(self):
        """Start the async monitoring service"""
        self.running = True
        
        console.print(f"\n[bold]Starting async risk monitor with WebSocket streaming...[/bold]")
        console.print(f"Firm: {self.account_config.firm} ([cyan]{self.account_config.rules.name}[/cyan])")
        console.print(f"Periodic check interval: 60s\n")
        
        try:
            # Connect to WebSocket
            await self.client.connect()
            await self.client.subscribe_to_account()
            
            # Run both event listener and periodic checker concurrently
            await asyncio.gather(
                self.client.listen_for_updates(self.handle_account_update),
                self.periodic_check(interval=60)
            )
            
        except Exception as e:
            console.print(f"[red]Error in monitoring loop: {e}[/red]")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the monitoring service"""
        self.running = False
        await self.client.disconnect()
        console.print("[yellow]Async risk monitor stopped[/yellow]")


def main():
    """Entry point for async application"""
    monitor = AsyncRiskMonitor()
    
    try:
        asyncio.run(monitor.start())
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down...[/yellow]")


if __name__ == "__main__":
    main()
