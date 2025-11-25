"""
Example: Demonstrating "Whichever Is Higher" Max Daily Drawdown Rule

This example shows how the daily drawdown calculation always uses
the WORST CASE between equity-based and balance-based losses.

Key behavior:
- Day start anchor = max(day_start_balance, day_start_equity)
- Daily loss by equity = anchor - current_equity
- Daily loss by balance = anchor - current_balance
- Daily loss used = max(loss_by_equity, loss_by_balance)

This ensures you can't "hide" risk in floating drawdown.
"""
from datetime import datetime
from src.models import AccountSnapshot, Position
from src.config import FTMO_RULES
from src.rules import check_account_rules
from src.notifier import notify_console
from rich.console import Console
from rich.table import Table

console = Console()


def create_snapshot_with_day_start(
    balance: float,
    equity: float,
    day_start_balance: float,
    day_start_equity: float,
    positions: list = None
) -> AccountSnapshot:
    """Helper to create snapshots with day start tracking"""
    return AccountSnapshot(
        timestamp=datetime.now(),
        balance=balance,
        equity=equity,
        margin_used=1000.0,
        margin_available=equity - 1000.0,
        positions=positions or [],
        total_profit_loss=balance - day_start_balance,
        starting_balance=100000.0,
        day_start_balance=day_start_balance,
        day_start_equity=day_start_equity
    )


def example_1_floating_loss_dominates():
    """
    Example 1: Large floating loss (equity drops more than balance)
    
    Scenario: Trader has $3k floating loss in open positions
    - Balance: $100k (unchanged - no closed trades)
    - Equity: $97k (balance - floating loss)
    - Equity-based loss dominates: 3% loss
    """
    console.print("\n[bold cyan]" + "=" * 80 + "[/bold cyan]")
    console.print("[bold]Example 1: Floating Loss Dominates (Equity-Based)[/bold]")
    console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]")
    
    snapshot = create_snapshot_with_day_start(
        balance=100000.0,       # No realized losses yet
        equity=97000.0,         # $3k floating loss
        day_start_balance=100000.0,
        day_start_equity=100000.0
    )
    
    # Show calculations
    anchor = snapshot.day_start_anchor
    loss_by_equity = anchor - snapshot.equity
    loss_by_balance = anchor - snapshot.balance
    loss_used = max(loss_by_equity, loss_by_balance)
    
    console.print(f"\nDay Start Anchor: [cyan]${anchor:,.2f}[/cyan] (max of balance/equity)")
    console.print(f"Current Balance:  [yellow]${snapshot.balance:,.2f}[/yellow]")
    console.print(f"Current Equity:   [red]${snapshot.equity:,.2f}[/red] (has $3k floating loss)")
    console.print()
    console.print(f"Loss by Equity:   [red]${loss_by_equity:,.2f}[/red] ({snapshot.daily_drawdown_pct:.2f}%)")
    console.print(f"Loss by Balance:  [green]${loss_by_balance:,.2f}[/green] (0%)")
    console.print(f"[bold]Loss Used:[/bold] [red bold]${loss_used:,.2f}[/red bold] ({-(100 * loss_used / anchor):.2f}%) ← WORST CASE")
    
    breaches = check_account_rules(snapshot, FTMO_RULES)
    if breaches:
        console.print()
        notify_console("EXAMPLE-1", breaches)


def example_2_realized_loss_dominates():
    """
    Example 2: Large realized loss (balance drops more than equity)
    
    Scenario: Trader closed losing trades at loss, but has profitable floating positions
    - Balance: $95k (realized $5k loss)
    - Equity: $97k (balance + $2k floating profit)
    - Balance-based loss dominates: 5% loss
    """
    console.print("\n[bold cyan]" + "=" * 80 + "[/bold cyan]")
    console.print("[bold]Example 2: Realized Loss Dominates (Balance-Based)[/bold]")
    console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]")
    
    snapshot = create_snapshot_with_day_start(
        balance=95000.0,        # $5k realized loss
        equity=97000.0,         # $2k floating profit helps, but...
        day_start_balance=100000.0,
        day_start_equity=100000.0
    )
    
    # Show calculations
    anchor = snapshot.day_start_anchor
    loss_by_equity = anchor - snapshot.equity
    loss_by_balance = anchor - snapshot.balance
    loss_used = max(loss_by_equity, loss_by_balance)
    
    console.print(f"\nDay Start Anchor: [cyan]${anchor:,.2f}[/cyan] (max of balance/equity)")
    console.print(f"Current Balance:  [red]${snapshot.balance:,.2f}[/red] (realized $5k loss)")
    console.print(f"Current Equity:   [yellow]${snapshot.equity:,.2f}[/yellow] (balance + $2k floating profit)")
    console.print()
    console.print(f"Loss by Equity:   [yellow]${loss_by_equity:,.2f}[/yellow] ({-(100 * loss_by_equity / anchor):.2f}%)")
    console.print(f"Loss by Balance:  [red]${loss_by_balance:,.2f}[/red] ({snapshot.daily_drawdown_pct:.2f}%)")
    console.print(f"[bold]Loss Used:[/bold] [red bold]${loss_used:,.2f}[/red bold] ({-(100 * loss_used / anchor):.2f}%) ← WORST CASE")
    
    breaches = check_account_rules(snapshot, FTMO_RULES)
    if breaches:
        console.print()
        notify_console("EXAMPLE-2", breaches)


def example_3_both_losses_combined():
    """
    Example 3: Both realized and floating losses
    
    Scenario: Trader has both realized and floating losses
    - Balance: $96k (realized $4k loss)
    - Equity: $94k (balance - $2k floating loss)
    - Equity-based loss dominates: 6% total loss
    """
    console.print("\n[bold cyan]" + "=" * 80 + "[/bold cyan]")
    console.print("[bold]Example 3: Combined Losses (Both Realized and Floating)[/bold]")
    console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]")
    
    snapshot = create_snapshot_with_day_start(
        balance=96000.0,        # $4k realized loss
        equity=94000.0,         # $2k additional floating loss
        day_start_balance=100000.0,
        day_start_equity=100000.0
    )
    
    # Show calculations
    anchor = snapshot.day_start_anchor
    loss_by_equity = anchor - snapshot.equity
    loss_by_balance = anchor - snapshot.balance
    loss_used = max(loss_by_equity, loss_by_balance)
    
    console.print(f"\nDay Start Anchor: [cyan]${anchor:,.2f}[/cyan] (max of balance/equity)")
    console.print(f"Current Balance:  [red]${snapshot.balance:,.2f}[/red] ($4k realized loss)")
    console.print(f"Current Equity:   [red bold]${snapshot.equity:,.2f}[/red bold] ($6k total loss)")
    console.print()
    console.print(f"Loss by Equity:   [red bold]${loss_by_equity:,.2f}[/red bold] ({snapshot.daily_drawdown_pct:.2f}%)")
    console.print(f"Loss by Balance:  [red]${loss_by_balance:,.2f}[/red] ({-(100 * loss_by_balance / anchor):.2f}%)")
    console.print(f"[bold]Loss Used:[/bold] [red bold]${loss_used:,.2f}[/red bold] ({-(100 * loss_used / anchor):.2f}%) ← WORST CASE")
    
    breaches = check_account_rules(snapshot, FTMO_RULES)
    if breaches:
        console.print()
        notify_console("EXAMPLE-3", breaches)


def example_4_day_start_with_profit():
    """
    Example 4: Day starts with equity > balance (floating profit from yesterday)
    
    Scenario: Day starts with $2k floating profit from open positions
    - Day start: Balance $98k, Equity $100k → Anchor = $100k (higher)
    - Current: Balance $98k, Equity $95k
    - Loss is calculated from the $100k anchor
    """
    console.print("\n[bold cyan]" + "=" * 80 + "[/bold cyan]")
    console.print("[bold]Example 4: Day Start With Higher Equity (Floating Profit)[/bold]")
    console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]")
    
    snapshot = create_snapshot_with_day_start(
        balance=98000.0,
        equity=95000.0,         # Lost $5k from yesterday's $100k equity
        day_start_balance=98000.0,
        day_start_equity=100000.0  # Started day with $2k floating profit
    )
    
    # Show calculations
    anchor = snapshot.day_start_anchor
    loss_by_equity = anchor - snapshot.equity
    loss_by_balance = anchor - snapshot.balance
    loss_used = max(loss_by_equity, loss_by_balance)
    
    console.print(f"\nDay Start Balance: [yellow]$98,000.00[/yellow]")
    console.print(f"Day Start Equity:  [cyan]$100,000.00[/cyan] (had $2k floating profit)")
    console.print(f"Day Start Anchor:  [cyan bold]$100,000.00[/cyan bold] ← Used higher value")
    console.print()
    console.print(f"Current Balance:   [yellow]${snapshot.balance:,.2f}[/yellow]")
    console.print(f"Current Equity:    [red]${snapshot.equity:,.2f}[/red]")
    console.print()
    console.print(f"Loss by Equity:    [red]${loss_by_equity:,.2f}[/red] ({snapshot.daily_drawdown_pct:.2f}%)")
    console.print(f"Loss by Balance:   [yellow]${loss_by_balance:,.2f}[/yellow] ({-(100 * loss_by_balance / anchor):.2f}%)")
    console.print(f"[bold]Loss Used:[/bold] [red bold]${loss_used:,.2f}[/red bold] ({-(100 * loss_used / anchor):.2f}%) ← WORST CASE")
    
    breaches = check_account_rules(snapshot, FTMO_RULES)
    if breaches:
        console.print()
        notify_console("EXAMPLE-4", breaches)


def example_5_comparison_table():
    """Example 5: Comparison table showing different scenarios"""
    console.print("\n[bold cyan]" + "=" * 80 + "[/bold cyan]")
    console.print("[bold]Example 5: Comparison Table - All Scenarios[/bold]")
    console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]")
    
    scenarios = [
        {
            "name": "Pure Floating Loss",
            "balance": 100000, "equity": 95000,
            "day_bal": 100000, "day_eq": 100000
        },
        {
            "name": "Pure Realized Loss",
            "balance": 95000, "equity": 95000,
            "day_bal": 100000, "day_eq": 100000
        },
        {
            "name": "Mixed: More Floating",
            "balance": 98000, "equity": 94000,
            "day_bal": 100000, "day_eq": 100000
        },
        {
            "name": "Mixed: More Realized",
            "balance": 94000, "equity": 96000,
            "day_bal": 100000, "day_eq": 100000
        },
        {
            "name": "Recovery (Floating Profit)",
            "balance": 95000, "equity": 98000,
            "day_bal": 100000, "day_eq": 100000
        }
    ]
    
    table = Table(title="\nDaily Drawdown Calculation Comparison", show_header=True, header_style="bold cyan")
    table.add_column("Scenario", style="dim", width=20)
    table.add_column("Balance", justify="right")
    table.add_column("Equity", justify="right")
    table.add_column("Loss by\nEquity", justify="right")
    table.add_column("Loss by\nBalance", justify="right")
    table.add_column("Used\n(Worst)", justify="right", style="bold red")
    table.add_column("DD %", justify="right", style="bold")
    
    for scenario in scenarios:
        snapshot = create_snapshot_with_day_start(
            scenario["balance"], scenario["equity"],
            scenario["day_bal"], scenario["day_eq"]
        )
        
        anchor = snapshot.day_start_anchor
        loss_eq = anchor - snapshot.equity
        loss_bal = anchor - snapshot.balance
        loss_used = max(loss_eq, loss_bal)
        dd_pct = snapshot.daily_drawdown_pct
        
        table.add_row(
            scenario["name"],
            f"${snapshot.balance:,.0f}",
            f"${snapshot.equity:,.0f}",
            f"${loss_eq:,.0f}",
            f"${loss_bal:,.0f}",
            f"${loss_used:,.0f}",
            f"{dd_pct:.2f}%"
        )
    
    console.print(table)
    console.print("\n[dim]Note: Day start anchor = $100,000 for all scenarios[/dim]")


def main():
    """Run all examples"""
    console.print("\n[bold cyan]╔" + "═" * 78 + "╗[/bold cyan]")
    console.print("[bold cyan]║" + " " * 15 + "MAX DAILY DRAWDOWN - WHICHEVER IS HIGHER RULE" + " " * 17 + "║[/bold cyan]")
    console.print("[bold cyan]╚" + "═" * 78 + "╝[/bold cyan]")
    
    console.print("\n[dim]This rule ensures you can't hide risk in floating drawdown.[/dim]")
    console.print("[dim]Always uses the WORST CASE between equity and balance-based losses.[/dim]")
    
    example_1_floating_loss_dominates()
    example_2_realized_loss_dominates()
    example_3_both_losses_combined()
    example_4_day_start_with_profit()
    example_5_comparison_table()
    
    console.print("\n[bold cyan]" + "=" * 80 + "[/bold cyan]")
    console.print("[bold green]All examples completed![/bold green]")
    console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]")
    console.print()
    console.print("[bold]Key Takeaways:[/bold]")
    console.print("  1. Day start anchor = max(day_start_balance, day_start_equity)")
    console.print("  2. Daily loss = max(anchor - equity, anchor - balance)")
    console.print("  3. This catches BOTH floating and realized losses")
    console.print("  4. You cannot hide risk by keeping positions open")
    console.print()


if __name__ == "__main__":
    main()
