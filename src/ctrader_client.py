"""
cTrader API client for fetching account and trading data
"""
from typing import Dict, List, Optional
from datetime import datetime, time
import requests
import asyncio
import websockets
import json
from src.config import Config
from src.models import AccountSnapshot, Position


class CTraderClient:
    """Client for interacting with cTrader Open API"""
    
    # cTrader Open API endpoints
    REST_BASE_URL = "https://openapi.ctrader.com"
    WS_URL = "wss://openapi.ctrader.com"
    
    def __init__(self, client_id: str = None, client_secret: str = None, 
                 access_token: str = None, account_id: str = None):
        """
        Initialize cTrader client
        
        Args:
            client_id: OAuth client ID (defaults to config)
            client_secret: OAuth client secret (defaults to config)
            access_token: OAuth access token (defaults to config)
            account_id: Trading account ID (defaults to config)
        """
        self.client_id = client_id or Config.CTRADER_CLIENT_ID
        self.client_secret = client_secret or Config.CTRADER_CLIENT_SECRET
        self.access_token = access_token or Config.CTRADER_ACCESS_TOKEN
        self.account_id = account_id or Config.ACCOUNT_ID
        
        self.ws_connection = None
        self.is_connected = False
        self._last_snapshot = None
        
    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers for API requests"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    # ==================== REST API Methods (Synchronous) ====================
    
    def get_account_info(self) -> Dict:
        """
        Fetch account information via REST
        Returns balance, equity, margin, unrealised P&L, etc.
        """
        url = f"{self.REST_BASE_URL}/v2/accounts/{self.account_id}"
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching account info: {e}")
            return {}
    
    def get_positions(self) -> List[Dict]:
        """Fetch open positions via REST"""
        url = f"{self.REST_BASE_URL}/v2/accounts/{self.account_id}/positions"
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("position", []) if isinstance(data, dict) else []
        except requests.RequestException as e:
            print(f"Error fetching positions: {e}")
            return []
    
    def get_orders(self) -> List[Dict]:
        """Fetch pending orders via REST"""
        url = f"{self.REST_BASE_URL}/v2/accounts/{self.account_id}/orders"
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("order", []) if isinstance(data, dict) else []
        except requests.RequestException as e:
            print(f"Error fetching orders: {e}")
            return []
    
    def get_deals_history(self, from_timestamp: int = None, to_timestamp: int = None) -> List[Dict]:
        """
        Fetch historical deals (closed positions)
        
        Args:
            from_timestamp: Start timestamp in milliseconds
            to_timestamp: End timestamp in milliseconds
        """
        url = f"{self.REST_BASE_URL}/v2/accounts/{self.account_id}/deals"
        params = {}
        if from_timestamp:
            params["from"] = from_timestamp
        if to_timestamp:
            params["to"] = to_timestamp
            
        try:
            response = requests.get(url, headers=self._get_headers(), params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("deal", []) if isinstance(data, dict) else []
        except requests.RequestException as e:
            print(f"Error fetching deals history: {e}")
            return []
    
    def get_balance(self) -> float:
        """Get current account balance"""
        account_info = self.get_account_info()
        return float(account_info.get("balance", 0)) / 100  # cTrader returns in cents
    
    def get_equity(self) -> float:
        """Get current account equity (balance + unrealised P&L)"""
        account_info = self.get_account_info()
        return float(account_info.get("equity", 0)) / 100  # cTrader returns in cents
    
    def get_margin_free(self) -> float:
        """Get free margin available"""
        account_info = self.get_account_info()
        return float(account_info.get("marginFree", 0)) / 100
    
    def get_margin_used(self) -> float:
        """Get margin currently used"""
        account_info = self.get_account_info()
        return float(account_info.get("margin", 0)) / 100
    
    def get_unrealised_pnl(self) -> float:
        """Get unrealised profit/loss from open positions"""
        account_info = self.get_account_info()
        return float(account_info.get("unrealizedNetProfit", 0)) / 100
    
    def get_today_pl(self) -> float:
        """
        Calculate today's realised P&L from closed positions
        Returns sum of P&L for deals closed since broker server midnight
        """
        # Get broker server time (typically UTC+2 or UTC+3 for cTrader)
        now = datetime.utcnow()
        
        # Approximate broker midnight (you may need to adjust timezone)
        # For now, using UTC midnight
        today_start = datetime.combine(now.date(), time.min)
        from_timestamp = int(today_start.timestamp() * 1000)
        
        deals = self.get_deals_history(from_timestamp=from_timestamp)
        
        total_pl = 0.0
        for deal in deals:
            # closeProfit is in cents
            profit = float(deal.get("closeProfit", 0)) / 100
            total_pl += profit
        
        return total_pl
    
    def get_account_snapshot(self) -> AccountSnapshot:
        """
        Create a complete account snapshot with all relevant data
        This is the main method to use for monitoring
        """
        account_info = self.get_account_info()
        positions_data = self.get_positions()
        
        # Parse account data
        balance = float(account_info.get("balance", 0)) / 100
        equity = float(account_info.get("equity", 0)) / 100
        margin_used = float(account_info.get("margin", 0)) / 100
        margin_free = float(account_info.get("marginFree", 0)) / 100
        unrealised_pnl = float(account_info.get("unrealizedNetProfit", 0)) / 100
        
        # Parse positions
        positions = []
        for pos_data in positions_data:
            position = Position(
                position_id=str(pos_data.get("positionId", "")),
                symbol=pos_data.get("symbol", ""),
                volume=float(pos_data.get("volume", 0)) / 100,  # Volume in lots
                entry_price=float(pos_data.get("entryPrice", 0)),
                current_price=float(pos_data.get("currentPrice", 0)),
                profit_loss=float(pos_data.get("profit", 0)) / 100,
                side="buy" if pos_data.get("tradeSide") == "BUY" else "sell"
            )
            positions.append(position)
        
        # Get today's realised P&L
        realised_pl_today = self.get_today_pl()
        
        # Total P&L = realised + unrealised
        total_pl = realised_pl_today + unrealised_pnl
        
        snapshot = AccountSnapshot(
            timestamp=datetime.now(),
            balance=balance,
            equity=equity,
            margin_used=margin_used,
            margin_available=margin_free,
            positions=positions,
            total_profit_loss=total_pl
        )
        
        self._last_snapshot = snapshot
        return snapshot
    
    def get_open_positions(self) -> List[Position]:
        """Get list of open positions as Position objects"""
        positions_data = self.get_positions()
        positions = []
        
        for pos_data in positions_data:
            position = Position(
                position_id=str(pos_data.get("positionId", "")),
                symbol=pos_data.get("symbol", ""),
                volume=float(pos_data.get("volume", 0)) / 100,
                entry_price=float(pos_data.get("entryPrice", 0)),
                current_price=float(pos_data.get("currentPrice", 0)),
                profit_loss=float(pos_data.get("profit", 0)) / 100,
                side="buy" if pos_data.get("tradeSide") == "BUY" else "sell"
            )
            positions.append(position)
        
        return positions
    
    # ==================== WebSocket API Methods (Async) ====================
    
    async def connect(self):
        """
        Connect to cTrader WebSocket API for real-time streaming
        This is for advanced usage - polling REST is simpler for most cases
        """
        try:
            self.ws_connection = await websockets.connect(
                self.WS_URL,
                extra_headers={"Authorization": f"Bearer {self.access_token}"}
            )
            self.is_connected = True
            print("WebSocket connected to cTrader API")
            
            # Send authentication message
            auth_msg = {
                "clientMsgId": "auth_1",
                "payloadType": 2100,  # ProtoOAApplicationAuthReq
                "payload": {
                    "clientId": self.client_id,
                    "clientSecret": self.client_secret
                }
            }
            await self.ws_connection.send(json.dumps(auth_msg))
            
            # Wait for auth response
            response = await self.ws_connection.recv()
            print(f"Auth response: {response}")
            
        except Exception as e:
            print(f"WebSocket connection error: {e}")
            self.is_connected = False
            raise
    
    async def subscribe_to_account(self):
        """Subscribe to account updates via WebSocket"""
        if not self.is_connected:
            await self.connect()
        
        subscribe_msg = {
            "clientMsgId": "sub_1",
            "payloadType": 2124,  # ProtoOASubscribeSpotsReq
            "payload": {
                "ctidTraderAccountId": int(self.account_id)
            }
        }
        await self.ws_connection.send(json.dumps(subscribe_msg))
    
    async def listen_for_updates(self, callback):
        """
        Listen for real-time account updates
        
        Args:
            callback: Async function to handle updates
        """
        if not self.is_connected:
            await self.connect()
            await self.subscribe_to_account()
        
        try:
            async for message in self.ws_connection:
                data = json.loads(message)
                await callback(data)
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket connection closed")
            self.is_connected = False
        except Exception as e:
            print(f"Error in WebSocket listener: {e}")
            self.is_connected = False
    
    async def disconnect(self):
        """Close WebSocket connection"""
        if self.ws_connection:
            await self.ws_connection.close()
            self.is_connected = False
            print("WebSocket disconnected")
