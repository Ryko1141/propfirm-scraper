"""
cTrader API client for fetching account and trading data
"""
from typing import Dict, List, Optional
import requests
from src.config import Config


class CTraderClient:
    """Client for interacting with cTrader API"""
    
    BASE_URL = "https://api.ctrader.com/api/v2"
    
    def __init__(self):
        self.client_id = Config.CTRADER_CLIENT_ID
        self.client_secret = Config.CTRADER_CLIENT_SECRET
        self.access_token = Config.CTRADER_ACCESS_TOKEN
        self.account_id = Config.ACCOUNT_ID
        
    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers for API requests"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def get_account_info(self) -> Dict:
        """Fetch account information"""
        url = f"{self.BASE_URL}/accounts/{self.account_id}"
        response = requests.get(url, headers=self._get_headers())
        response.raise_for_status()
        return response.json()
    
    def get_positions(self) -> List[Dict]:
        """Fetch open positions"""
        url = f"{self.BASE_URL}/accounts/{self.account_id}/positions"
        response = requests.get(url, headers=self._get_headers())
        response.raise_for_status()
        return response.json().get("positions", [])
    
    def get_orders(self) -> List[Dict]:
        """Fetch pending orders"""
        url = f"{self.BASE_URL}/accounts/{self.account_id}/orders"
        response = requests.get(url, headers=self._get_headers())
        response.raise_for_status()
        return response.json().get("orders", [])
    
    def get_balance(self) -> float:
        """Get current account balance"""
        account_info = self.get_account_info()
        return float(account_info.get("balance", 0))
    
    def get_equity(self) -> float:
        """Get current account equity"""
        account_info = self.get_account_info()
        return float(account_info.get("equity", 0))
