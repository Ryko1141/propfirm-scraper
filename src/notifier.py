"""
Notification system for sending alerts
"""
from typing import List
import requests
from src.models import RuleViolation
from src.config import Config


class Notifier:
    """Handles sending notifications via various channels"""
    
    def __init__(self):
        self.telegram_bot_token = Config.TELEGRAM_BOT_TOKEN
        self.telegram_chat_id = Config.TELEGRAM_CHAT_ID
    
    def send_violations(self, violations: List[RuleViolation]):
        """Send notifications for rule violations"""
        if not violations:
            return
        
        for violation in violations:
            self._send_telegram(violation)
    
    def _send_telegram(self, violation: RuleViolation):
        """Send notification via Telegram"""
        if not self.telegram_bot_token or not self.telegram_chat_id:
            print(f"[{violation.severity.upper()}] {violation.message}")
            return
        
        # Format message
        emoji = "🔴" if violation.severity == "critical" else "⚠️"
        message = f"{emoji} *{violation.rule_name}*\n\n{violation.message}"
        
        if violation.value is not None and violation.threshold is not None:
            message += f"\n\nValue: {violation.value:.2f}\nThreshold: {violation.threshold:.2f}"
        
        message += f"\n\n_Time: {violation.timestamp.strftime('%Y-%m-%d %H:%M:%S')}_"
        
        # Send via Telegram API
        url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
        except Exception as e:
            print(f"Failed to send Telegram notification: {e}")
            print(f"[{violation.severity.upper()}] {violation.message}")
    
    def send_status(self, message: str):
        """Send a general status message"""
        if not self.telegram_bot_token or not self.telegram_chat_id:
            print(f"[STATUS] {message}")
            return
        
        url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": f"ℹ️ {message}"
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
        except Exception as e:
            print(f"Failed to send status message: {e}")
