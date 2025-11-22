"""
Configuration management for prop risk monitor
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration"""
    
    # cTrader API credentials
    CTRADER_CLIENT_ID = os.getenv("CTRADER_CLIENT_ID")
    CTRADER_CLIENT_SECRET = os.getenv("CTRADER_CLIENT_SECRET")
    CTRADER_ACCESS_TOKEN = os.getenv("CTRADER_ACCESS_TOKEN")
    
    # Account settings
    ACCOUNT_ID = os.getenv("ACCOUNT_ID")
    
    # Notification settings
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    
    # Monitoring rules
    MAX_DAILY_LOSS_PERCENT = float(os.getenv("MAX_DAILY_LOSS_PERCENT", "5.0"))
    MAX_POSITION_SIZE_PERCENT = float(os.getenv("MAX_POSITION_SIZE_PERCENT", "10.0"))
    
    @classmethod
    def validate(cls):
        """Validate that all required configuration is present"""
        required = [
            "CTRADER_CLIENT_ID",
            "CTRADER_CLIENT_SECRET",
            "ACCOUNT_ID"
        ]
        missing = [key for key in required if not getattr(cls, key)]
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
