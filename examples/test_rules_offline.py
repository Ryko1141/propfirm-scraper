"""
Example: Testing rules engine offline with dummy data
Demonstrates pure logic testing without API dependencies
"""
from datetime import datetime
from src.models import AccountSnapshot, Position
from src.config import FTMO_RULES, ALPHA_CAPITAL_RULES
from src.rules import check_account_rules
from src.notifier import notify_console
from rich.console import Console

console = Console()


def create_test_snapshot(
    balance: float = 100000.0,
    daily_pnl: float = 0.0,
    positions: list = None,
    starting_balance: float = 100000.0
) -> AccountSnapshot:
    """Helper to create test snapshots"""
    return AccountSnapshot(
        timestamp=datetime.now(),
        balance=balance,
        equity=balance + daily_pnl,
        margin_used=1000.0,
        margin_available=balance + daily_pnl - 1000.0,
        positions=positions or [],
        total_profit_loss=daily_pnl,
        starting_balance=starting_balance
    )


def example_1_clean_account():
    """Example 1: Clean account with no violations"""
    console.print("\n[bold cyan]" + "=" * 60 + "[/bold cyan]")
    console.print("[bold]Example 1: Clean Account[/bold]")
    console.print("[bold cyan]" + "=" * 60 + "[/bold cyan]")
    
    snapshot = create_test_snapshot(
        balance=100000.0,
        daily_pnl=500.0  # Small profit
    )
    
    breaches = check_account_rules(snapshot, FTMO_RULES)
    
    console.print(f"Balance: [cyan]${snapshot.balance:,.2f}[/cyan]")
    console.print(f"Daily P&L: [green]${snapshot.total_profit_loss:,.2f}[/green]")
    console.print(f"Breaches: [green]{len(breaches)}[/green]")
    
    if breaches:
        notify_console("FTMO-Example", breaches)
    else:
        console.print("[green]✅ All rules passed![/green]")


def example_2_daily_dd_warning():
    """Example 2: Daily drawdown approaching limit"""
    console.print("\n[bold cyan]" + "=" * 60 + "[/bold cyan]")
    console.print("[bold]Example 2: Daily Drawdown Warning[/bold]")
    console.print("[bold cyan]" + "=" * 60 + "[/bold cyan]")
    
    snapshot = create_test_snapshot(
        balance=100000.0,
        daily_pnl=-4200.0  # -4.2% loss (warning at 80% of 5% limit)
    )
    
    breaches = check_account_rules(snapshot, FTMO_RULES)
    
    console.print(f"Balance: [cyan]${snapshot.balance:,.2f}[/cyan]")
    console.print(f"Daily P&L: [red]${snapshot.total_profit_loss:,.2f}[/red] ({snapshot.daily_drawdown_pct:.2f}%)")
    console.print(f"Breaches: [yellow]{len(breaches)}[/yellow]")
    
    notify_console("FTMO-Example", breaches)


def example_3_daily_dd_violation():
    """Example 3: Daily drawdown hard limit breached"""
    console.print("\n[bold cyan]" + "=" * 60 + "[/bold cyan]")
    console.print("[bold]Example 3: Daily Drawdown VIOLATION[/bold]")
    console.print("[bold cyan]" + "=" * 60 + "[/bold cyan]")
    
    snapshot = create_test_snapshot(
        balance=100000.0,
        daily_pnl=-5500.0  # -5.5% loss (exceeds 5% limit)
    )
    
    breaches = check_account_rules(snapshot, FTMO_RULES)
    
    console.print(f"Balance: [cyan]${snapshot.balance:,.2f}[/cyan]")
    console.print(f"Daily P&L: [red]${snapshot.total_profit_loss:,.2f}[/red] ({snapshot.daily_drawdown_pct:.2f}%)")
    console.print(f"Breaches: [red]{len(breaches)}[/red]")
    
    notify_console("FTMO-Example", breaches)


def example_4_total_dd_violation():
    """Example 4: Total drawdown breached"""
    console.print("\n[bold cyan]" + "=" * 60 + "[/bold cyan]")
    console.print("[bold]Example 4: Total Drawdown VIOLATION[/bold]")
    console.print("[bold cyan]" + "=" * 60 + "[/bold cyan]")
    
    snapshot = create_test_snapshot(
        balance=89000.0,  # Down $11k from $100k start = 11% DD
        daily_pnl=0.0,
        starting_balance=100000.0
    )
    
    breaches = check_account_rules(snapshot, FTMO_RULES, starting_balance=100000.0)
    
    console.print(f"Starting Balance: [cyan]$100,000.00[/cyan]")
    console.print(f"Current Balance: [red]${snapshot.balance:,.2f}[/red]")
    console.print(f"Total Drawdown: [red]{snapshot.total_drawdown_pct:.2f}%[/red]")
    console.print(f"Breaches: [red]{len(breaches)}[/red]")
    
    notify_console("FTMO-Example", breaches)


def example_5_oversized_position():
    """Example 5: Position too large"""
    console.print("\n[bold cyan]" + "=" * 60 + "[/bold cyan]")
    console.print("[bold]Example 5: Oversized Position[/bold]")
    console.print("[bold cyan]" + "=" * 60 + "[/bold cyan]")
    
    large_position = Position(
        position_id="12345",
        symbol="EURUSD",
        volume=1.5,  # 1.5% of balance (exceeds 1% limit)
        entry_price=1.1000,
        current_price=1.1050,
        profit_loss=750.0,
        side="buy"
    )
    
    snapshot = create_test_snapshot(
        balance=100000.0,
        daily_pnl=750.0,
        positions=[large_position]
    )
    
    breaches = check_account_rules(snapshot, FTMO_RULES)
    
    console.print(f"Position: [cyan]{large_position.symbol}[/cyan]")
    console.print(f"Volume: {large_position.volume} lots")
    console.print(f"Position Risk: [yellow]{(large_position.volume / snapshot.balance * 100):.2f}%[/yellow] of balance")
    console.print(f"Breaches: [red]{len(breaches)}[/red]")
    
    notify_console("FTMO-Example", breaches)


def example_6_too_many_lots():
    """Example 6: Total lot size exceeded"""
    console.print("\n[bold cyan]" + "=" * 60 + "[/bold cyan]")
    console.print("[bold]Example 6: Too Many Lots[/bold]")
    console.print("[bold cyan]" + "=" * 60 + "[/bold cyan]")
    
    # 10 positions with 1.2 lots each = 12 total lots (exceeds 10 lot limit)
    positions = [
        Position(
            position_id=f"pos{i}",
            symbol="EURUSD",
            volume=1.2,
            entry_price=1.1000,
            current_price=1.1050,
            profit_loss=60.0,
            side="buy"
        )
        for i in range(10)
    ]
    
    snapshot = create_test_snapshot(
        balance=100000.0,
        daily_pnl=600.0,
        positions=positions
    )
    
    breaches = check_account_rules(snapshot, FTMO_RULES)
    
    total_lots = sum(p.volume for p in positions)
    console.print(f"Open Positions: [cyan]{len(positions)}[/cyan]")
    console.print(f"Total Lots: [yellow]{total_lots:.2f}[/yellow]")
    console.print(f"Max Allowed: [green]{FTMO_RULES.max_open_lots}[/green]")
    console.print(f"Breaches: [red]{len(breaches)}[/red]")
    
    notify_console("FTMO-Example", breaches)


def example_7_multiple_violations():
    """Example 7: Multiple simultaneous violations"""
    console.print("\n[bold cyan]" + "=" * 60 + "[/bold cyan]")
    console.print("[bold]Example 7: Multiple Violations[/bold]")
    console.print("[bold cyan]" + "=" * 60 + "[/bold cyan]")
    
    # Create disaster scenario
    positions = [
        Position(
            position_id=f"pos{i}",
            symbol="EURUSD",
            volume=1.5,  # Oversized
            entry_price=1.1000,
            current_price=1.0950,
            profit_loss=-750.0,
            side="buy"
        )
        for i in range(12)  # Too many positions
    ]
    
    snapshot = create_test_snapshot(
        balance=88000.0,  # Total DD violation
        daily_pnl=-6000.0,  # Daily DD violation
        positions=positions,
        starting_balance=100000.0
    )
    
    breaches = check_account_rules(snapshot, FTMO_RULES)
    
    console.print(f"Starting Balance: [cyan]$100,000.00[/cyan]")
    console.print(f"Current Balance: [red]${snapshot.balance:,.2f}[/red]")
    console.print(f"Daily P&L: [red]${snapshot.total_profit_loss:,.2f}[/red] ({snapshot.daily_drawdown_pct:.2f}%)")
    console.print(f"Total DD: [red]{snapshot.total_drawdown_pct:.2f}%[/red]")
    console.print(f"Open Positions: [yellow]{len(positions)}[/yellow]")
    console.print(f"Total Lots: [yellow]{sum(p.volume for p in positions):.2f}[/yellow]")
    console.print(f"\nBreaches: [red bold]{len(breaches)}[/red bold]")
    
    notify_console("FTMO-Example", breaches)


def example_8_different_firm_rules():
    """Example 8: Compare different firm rules"""
    console.print("\n[bold cyan]" + "=" * 60 + "[/bold cyan]")
    console.print("[bold]Example 8: Different Firm Rules Comparison[/bold]")
    console.print("[bold cyan]" + "=" * 60 + "[/bold cyan]")
    
    snapshot = create_test_snapshot(
        balance=100000.0,
        daily_pnl=-4500.0  # -4.5% loss
    )
    
    console.print(f"Daily P&L: [red]${snapshot.total_profit_loss:,.2f}[/red] ({snapshot.daily_drawdown_pct:.2f}%)")
    console.print()
    
    # Test with FTMO rules
    ftmo_breaches = check_account_rules(snapshot, FTMO_RULES)
    console.print(f"[bold]FTMO (5% limit):[/bold] [yellow]{len(ftmo_breaches)}[/yellow] breaches")
    if ftmo_breaches:
        notify_console("FTMO", ftmo_breaches)
    
    console.print()
    
    # Test with Alpha Capital rules
    alpha_breaches = check_account_rules(snapshot, ALPHA_CAPITAL_RULES)
    console.print(f"[bold]Alpha Capital (5% limit):[/bold] [yellow]{len(alpha_breaches)}[/yellow] breaches")
    if alpha_breaches:
        notify_console("Alpha Capital", alpha_breaches)


def main():
    """Run all examples"""
    console.print("\n[bold cyan]╔" + "═" * 58 + "╗[/bold cyan]")
    console.print("[bold cyan]║" + " " * 10 + "Pure Logic Rules Engine Examples" + " " * 15 + "║[/bold cyan]")
    console.print("[bold cyan]╚" + "═" * 58 + "╝[/bold cyan]")
    console.print("\n[dim]No API required - Testing with dummy data[/dim]")
    
    example_1_clean_account()
    example_2_daily_dd_warning()
    example_3_daily_dd_violation()
    example_4_total_dd_violation()
    example_5_oversized_position()
    example_6_too_many_lots()
    example_7_multiple_violations()
    example_8_different_firm_rules()
    
    console.print("\n[bold cyan]" + "=" * 60 + "[/bold cyan]")
    console.print("[bold green]All examples completed![/bold green]")
    console.print("[bold cyan]" + "=" * 60 + "[/bold cyan]")
    console.print("\n[dim]Run unit tests with:[/dim] [cyan]python tests/test_rules.py[/cyan]")
    console.print()


if __name__ == "__main__":
    main()
