"""
Configuration management for prop risk monitor
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration"""
    
    # Trading platform selection
    PLATFORM = os.getenv("PLATFORM", "ctrader").lower()  # "ctrader" or "mt5"
    
    # cTrader API credentials
    CTRADER_CLIENT_ID = os.getenv("CTRADER_CLIENT_ID")
    CTRADER_CLIENT_SECRET = os.getenv("CTRADER_CLIENT_SECRET")
    CTRADER_ACCESS_TOKEN = os.getenv("CTRADER_ACCESS_TOKEN")
    
    # MetaTrader 5 credentials
    MT5_PASSWORD = os.getenv("MT5_PASSWORD")
    MT5_SERVER = os.getenv("MT5_SERVER")
    MT5_PATH = os.getenv("MT5_PATH")  # Optional: path to MT5 terminal
    
    # Account settings (used by both platforms)
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
        # Common required fields
        required = ["ACCOUNT_ID"]
        
        # Platform-specific required fields
        if cls.PLATFORM == "ctrader":
            required.extend([
                "CTRADER_CLIENT_ID",
                "CTRADER_CLIENT_SECRET",
                "CTRADER_ACCESS_TOKEN"
            ])
        elif cls.PLATFORM == "mt5":
            required.extend([
                "MT5_PASSWORD",
                "MT5_SERVER"
            ])
        else:
            raise ValueError(f"Invalid PLATFORM: {cls.PLATFORM}. Must be 'ctrader' or 'mt5'")
        
        missing = [key for key in required if not getattr(cls, key)]
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
