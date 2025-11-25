"""
Notification system for sending alerts

Simple, readable console output using rich.
Extensible design for future notification channels.
"""
from typing import List
from rich.console import Console
from rich.panel import Panel
from src.models import RuleBreach

console = Console()


def notify_console(account_label: str, breaches: List[RuleBreach]):
    """
    Display rule breaches in the console with rich formatting.
    
    Args:
        account_label: Account identifier (e.g., "FTMO-12345")
        breaches: List of RuleBreach objects to display
    """
    if not breaches:
        return
    
    lines = [f"[bold]{account_label}[/bold]:"]
    for b in breaches:
        prefix = "[red]HARD[/red]" if b.level == "HARD" else "[yellow]WARN[/yellow]"
        lines.append(f"{prefix} {b.code} – {b.message}")
    
    console.print(Panel("\n".join(lines)))


# Future notification channels (extensible design):

# def notify_email(account_label: str, breaches: List[RuleBreach], 
#                  to_email: str, smtp_config: dict):
#     """Send email notification for breaches"""
#     pass

# def notify_telegram(account_label: str, breaches: List[RuleBreach],
#                     bot_token: str, chat_id: str):
#     """Send Telegram notification for breaches"""
#     pass

# def notify_discord_webhook(account_label: str, breaches: List[RuleBreach],
#                           webhook_url: str):
#     """Send Discord webhook notification for breaches"""
#     pass

# def notify_slack_webhook(account_label: str, breaches: List[RuleBreach],
#                         webhook_url: str):
#     """Send Slack webhook notification for breaches"""
#     pass
