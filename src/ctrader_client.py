"""
cTrader API client for fetching account and trading data
"""
from typing import Dict, List, Optional
from datetime import datetime, time, timedelta
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
        
        # Day start tracking for "whichever is higher" rule
        self._day_start_balance: Optional[float] = None
        self._day_start_equity: Optional[float] = None
        self._current_date: Optional[datetime] = None
        self._server_time_offset: Optional[float] = None  # Offset in seconds from local time
        
    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers for API requests"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def get_server_time(self) -> datetime:
        """
        Get the current broker server time from cTrader.
        
        cTrader returns timestamps in UTC milliseconds in various API responses.
        We'll use a spot price subscription or recent deal timestamp to determine server time.
        
        Returns:
            datetime: Current broker server time
        """
        try:
            # Get recent deals to extract server timestamp
            # cTrader provides timestamps in milliseconds since Unix epoch
            url = f"{self.REST_BASE_URL}/v2/accounts/{self.account_id}/deals"
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            data = response.json()
            
            deals = data.get("deal", [])
            if deals and len(deals) > 0:
                # Get the most recent deal timestamp (in milliseconds)
                latest_timestamp = max(deal.get("executionTimestamp", 0) for deal in deals)
                if latest_timestamp > 0:
                    server_time = datetime.fromtimestamp(latest_timestamp / 1000)
                    
                    # Calculate offset if not already set
                    if self._server_time_offset is None:
                        local_time = datetime.now()
                        self._server_time_offset = (server_time - local_time).total_seconds()
                        print(f"Detected cTrader server time offset: {self._server_time_offset:.0f} seconds")
                    
                    return server_time
        except Exception as e:
            print(f"Could not fetch server time from deals: {e}")
        
        # Fallback: if we have a cached offset, use it
        if self._server_time_offset is not None:
            return datetime.now() + timedelta(seconds=self._server_time_offset)
        
        # Final fallback: assume UTC (cTrader typically uses UTC)
        return datetime.utcnow()
    
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
        # Get broker server time
        now = self.get_server_time()
        
        # Calculate broker midnight based on server time
        today_start = datetime.combine(now.date(), time.min)
        from_timestamp = int(today_start.timestamp() * 1000)
        
        deals = self.get_deals_history(from_timestamp=from_timestamp)
        
        total_pl = 0.0
        for deal in deals:
            # closeProfit is in cents
            profit = float(deal.get("closeProfit", 0)) / 100
            total_pl += profit
        
        return total_pl
    
    def _update_day_start_anchor(self, balance: float, equity: float):
        """
        Update day start anchor when server date changes.
        
        Implements the "use whichever is higher" rule:
        At first tick after server date changes (00:00 server time):
        - dayStartBalance = current balance
        - dayStartEquity = current equity
        - dayStartAnchor = max(balance, equity)
        
        Args:
            balance: Current account balance
            equity: Current account equity
        """
        now = self.get_server_time()
        current_date = now.date()
        
        # First run or new day detected
        if self._current_date is None or current_date != self._current_date:
            self._day_start_balance = balance
            self._day_start_equity = equity
            self._current_date = current_date
            
            anchor = max(balance, equity)
            print(f"Day start anchor updated: Balance=${balance:,.2f}, "
                  f"Equity=${equity:,.2f}, Anchor=${anchor:,.2f} (using higher)")
    
    def get_account_snapshot(self) -> AccountSnapshot:
        """
        Create a complete account snapshot with all relevant data.
        Implements "whichever is higher" rule for daily drawdown tracking.
        This is the main method to use for monitoring.
        """
        account_info = self.get_account_info()
        positions_data = self.get_positions()
        
        # Parse account data
        balance = float(account_info.get("balance", 0)) / 100
        equity = float(account_info.get("equity", 0)) / 100
        margin_used = float(account_info.get("margin", 0)) / 100
        margin_free = float(account_info.get("marginFree", 0)) / 100
        unrealised_pnl = float(account_info.get("unrealizedNetProfit", 0)) / 100
        
        # Update day start anchor if new day detected
        self._update_day_start_anchor(balance, equity)
        
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
            total_profit_loss=total_pl,
            day_start_balance=self._day_start_balance,
            day_start_equity=self._day_start_equity
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
