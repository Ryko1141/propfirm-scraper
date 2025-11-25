"""
MetaTrader 5 API client for fetching account and trading data
"""
from typing import Dict, List, Optional
from datetime import datetime, time, timedelta
import MetaTrader5 as mt5
from src.config import Config
from src.models import AccountSnapshot, Position


class MT5Client:
    """Client for interacting with MetaTrader 5 API"""
    
    def __init__(self, account_number: int = None, password: str = None, 
                 server: str = None, path: str = None):
        """
        Initialize MT5 client
        
        Args:
            account_number: MT5 account number (defaults to config)
            password: MT5 account password (defaults to config)
            server: MT5 broker server (defaults to config)
            path: Path to MT5 terminal (optional, auto-detected if not provided)
        """
        self.account_number = account_number or int(Config.ACCOUNT_ID)
        self.password = password or Config.MT5_PASSWORD
        self.server = server or Config.MT5_SERVER
        self.path = path
        
        self.is_connected = False
        self._last_snapshot = None
        
        # Day start tracking for "whichever is higher" rule
        self._day_start_balance: Optional[float] = None
        self._day_start_equity: Optional[float] = None
        self._current_date: Optional[datetime] = None
        self._server_timezone_offset: Optional[int] = None  # Offset in hours from UTC
    
    def connect(self) -> bool:
        """
        Connect and login to MT5 terminal
        
        Returns:
            True if connection successful, False otherwise
        """
        # Initialize MT5 connection
        if self.path:
            if not mt5.initialize(path=self.path):
                print(f"MT5 initialize() failed, error code: {mt5.last_error()}")
                return False
        else:
            if not mt5.initialize():
                print(f"MT5 initialize() failed, error code: {mt5.last_error()}")
                return False
        
        # Login to account
        if not mt5.login(self.account_number, password=self.password, server=self.server):
            print(f"MT5 login failed, error code: {mt5.last_error()}")
            mt5.shutdown()
            return False
        
        self.is_connected = True
        
        # Calculate server timezone offset on first connection
        if self._server_timezone_offset is None:
            self._calculate_server_timezone_offset()
        
        print(f"Connected to MT5 account {self.account_number} on {self.server}")
        return True
    
    def disconnect(self):
        """Disconnect from MT5 terminal"""
        if self.is_connected:
            mt5.shutdown()
            self.is_connected = False
            print("Disconnected from MT5")
    
    def _ensure_connected(self) -> bool:
        """Ensure MT5 is connected, attempt reconnection if needed"""
        if not self.is_connected:
            return self.connect()
        return True
    
    def _calculate_server_timezone_offset(self):
        """
        Calculate the broker server's timezone offset from UTC.
        MT5 doesn't provide server time directly in API, but we can infer it
        from the last tick timestamp or use terminal_info.
        """
        if not self.is_connected:
            return
        
        # Get a recent tick to determine server time
        # Most MT5 brokers use UTC+2 or UTC+3 (EET/EEST)
        # We'll use symbol_info_tick to get server time
        try:
            # Try to get a tick from a common symbol
            symbols = mt5.symbols_get()
            if symbols and len(symbols) > 0:
                tick = mt5.symbol_info_tick(symbols[0].name)
                if tick:
                    # tick.time is server time as Unix timestamp
                    server_time = datetime.fromtimestamp(tick.time)
                    utc_time = datetime.utcnow()
                    # Calculate offset in hours
                    offset_seconds = (server_time - utc_time).total_seconds()
                    self._server_timezone_offset = round(offset_seconds / 3600)
                    print(f"Detected MT5 server timezone offset: UTC{self._server_timezone_offset:+d}")
                    return
        except Exception as e:
            print(f"Could not determine server timezone offset: {e}")
        
        # Default to UTC+2 (common for MT5 brokers)
        self._server_timezone_offset = 2
        print(f"Using default MT5 server timezone offset: UTC+2")
    
    def get_server_time(self) -> datetime:
        """
        Get the current broker server time.
        
        Returns:
            datetime: Current broker server time
        """
        if not self._ensure_connected():
            return datetime.now()
        
        # Get latest tick from any available symbol
        symbols = mt5.symbols_get()
        if symbols and len(symbols) > 0:
            tick = mt5.symbol_info_tick(symbols[0].name)
            if tick:
                return datetime.fromtimestamp(tick.time)
        
        # Fallback: use UTC with offset
        if self._server_timezone_offset is not None:
            return datetime.utcnow() + timedelta(hours=self._server_timezone_offset)
        
        return datetime.now()
    
    # ==================== Account Data Methods ====================
    
    def get_account_info(self) -> Optional[Dict]:
        """
        Fetch account information
        Returns balance, equity, margin, profit, etc.
        """
        if not self._ensure_connected():
            return None
        
        account_info = mt5.account_info()
        if account_info is None:
            print(f"Failed to get account info, error: {mt5.last_error()}")
            return None
        
        return {
            "login": account_info.login,
            "balance": account_info.balance,
            "equity": account_info.equity,
            "profit": account_info.profit,
            "margin": account_info.margin,
            "margin_free": account_info.margin_free,
            "margin_level": account_info.margin_level,
            "margin_so_mode": account_info.margin_so_mode,
            "margin_so_call": account_info.margin_so_call,
            "margin_so_so": account_info.margin_so_so,
            "leverage": account_info.leverage,
            "currency": account_info.currency,
            "server": account_info.server,
            "company": account_info.company
        }
    
    def get_balance(self) -> float:
        """Get current account balance"""
        account_info = self.get_account_info()
        return float(account_info.get("balance", 0)) if account_info else 0.0
    
    def get_equity(self) -> float:
        """Get current account equity (balance + unrealised P&L)"""
        account_info = self.get_account_info()
        return float(account_info.get("equity", 0)) if account_info else 0.0
    
    def get_margin_free(self) -> float:
        """Get free margin available"""
        account_info = self.get_account_info()
        return float(account_info.get("margin_free", 0)) if account_info else 0.0
    
    def get_margin_used(self) -> float:
        """Get margin currently used"""
        account_info = self.get_account_info()
        return float(account_info.get("margin", 0)) if account_info else 0.0
    
    def get_unrealised_pnl(self) -> float:
        """Get unrealised profit/loss from open positions"""
        account_info = self.get_account_info()
        return float(account_info.get("profit", 0)) if account_info else 0.0
    
    # ==================== Position & Order Methods ====================
    
    def get_positions(self) -> List[Dict]:
        """Fetch all open positions"""
        if not self._ensure_connected():
            return []
        
        positions = mt5.positions_get()
        if positions is None:
            print(f"Failed to get positions, error: {mt5.last_error()}")
            return []
        
        positions_list = []
        for pos in positions:
            positions_list.append({
                "ticket": pos.ticket,
                "time": pos.time,
                "type": pos.type,
                "magic": pos.magic,
                "identifier": pos.identifier,
                "reason": pos.reason,
                "volume": pos.volume,
                "price_open": pos.price_open,
                "price_current": pos.price_current,
                "sl": pos.sl,
                "tp": pos.tp,
                "profit": pos.profit,
                "swap": pos.swap,
                "commission": pos.commission,
                "symbol": pos.symbol,
                "comment": pos.comment
            })
        
        return positions_list
    
    def get_orders(self) -> List[Dict]:
        """Fetch pending orders"""
        if not self._ensure_connected():
            return []
        
        orders = mt5.orders_get()
        if orders is None:
            print(f"Failed to get orders, error: {mt5.last_error()}")
            return []
        
        orders_list = []
        for order in orders:
            orders_list.append({
                "ticket": order.ticket,
                "time_setup": order.time_setup,
                "type": order.type,
                "state": order.state,
                "magic": order.magic,
                "volume_initial": order.volume_initial,
                "volume_current": order.volume_current,
                "price_open": order.price_open,
                "sl": order.sl,
                "tp": order.tp,
                "price_current": order.price_current,
                "symbol": order.symbol,
                "comment": order.comment
            })
        
        return orders_list
    
    def get_deals_history(self, from_date: datetime = None, to_date: datetime = None) -> List[Dict]:
        """
        Fetch historical deals (closed positions)
        
        Args:
            from_date: Start date for history
            to_date: End date for history
        """
        if not self._ensure_connected():
            return []
        
        if from_date is None:
            # Default: last 24 hours
            from_date = datetime.now() - timedelta(days=1)
        if to_date is None:
            to_date = datetime.now()
        
        deals = mt5.history_deals_get(from_date, to_date)
        if deals is None:
            print(f"Failed to get deals history, error: {mt5.last_error()}")
            return []
        
        deals_list = []
        for deal in deals:
            deals_list.append({
                "ticket": deal.ticket,
                "order": deal.order,
                "time": deal.time,
                "type": deal.type,
                "entry": deal.entry,
                "magic": deal.magic,
                "position_id": deal.position_id,
                "volume": deal.volume,
                "price": deal.price,
                "commission": deal.commission,
                "swap": deal.swap,
                "profit": deal.profit,
                "symbol": deal.symbol,
                "comment": deal.comment
            })
        
        return deals_list
    
    def get_today_pl(self) -> float:
        """
        Calculate today's realised P&L from closed positions
        Returns sum of P&L for deals closed since broker server midnight
        """
        # Get broker server time
        if not self._ensure_connected():
            return 0.0
        
        # Calculate today's start (broker server midnight)
        now = self.get_server_time()
        today_start = datetime.combine(now.date(), time.min)
        
        deals = self.get_deals_history(from_date=today_start, to_date=now)
        
        total_pl = 0.0
        for deal in deals:
            # Only count exit deals (DEAL_ENTRY_OUT = 1)
            if deal.get("entry") == 1:
                profit = float(deal.get("profit", 0))
                commission = float(deal.get("commission", 0))
                swap = float(deal.get("swap", 0))
                total_pl += profit + commission + swap
        
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
    
    def get_open_positions(self) -> List[Position]:
        """Get list of open positions as Position objects"""
        positions_data = self.get_positions()
        positions = []
        
        for pos_data in positions_data:
            # Determine side (0 = buy, 1 = sell in MT5)
            pos_type = pos_data.get("type", 0)
            side = "buy" if pos_type == 0 else "sell"
            
            position = Position(
                position_id=str(pos_data.get("ticket", "")),
                symbol=pos_data.get("symbol", ""),
                volume=float(pos_data.get("volume", 0)),
                entry_price=float(pos_data.get("price_open", 0)),
                current_price=float(pos_data.get("price_current", 0)),
                profit_loss=float(pos_data.get("profit", 0)),
                side=side
            )
            positions.append(position)
        
        return positions
    
    def get_account_snapshot(self) -> AccountSnapshot:
        """
        Create a complete account snapshot with all relevant data.
        Implements "whichever is higher" rule for daily drawdown tracking.
        This is the main method to use for monitoring.
        """
        if not self._ensure_connected():
            raise ConnectionError("Failed to connect to MT5")
        
        account_info = self.get_account_info()
        if not account_info:
            raise ValueError("Failed to get account info")
        
        positions_data = self.get_positions()
        
        # Parse account data
        balance = float(account_info.get("balance", 0))
        equity = float(account_info.get("equity", 0))
        margin_used = float(account_info.get("margin", 0))
        margin_free = float(account_info.get("margin_free", 0))
        unrealised_pnl = float(account_info.get("profit", 0))
        
        # Update day start anchor if new day detected
        self._update_day_start_anchor(balance, equity)
        
        # Parse positions
        positions = []
        for pos_data in positions_data:
            pos_type = pos_data.get("type", 0)
            side = "buy" if pos_type == 0 else "sell"
            
            position = Position(
                position_id=str(pos_data.get("ticket", "")),
                symbol=pos_data.get("symbol", ""),
                volume=float(pos_data.get("volume", 0)),
                entry_price=float(pos_data.get("price_open", 0)),
                current_price=float(pos_data.get("price_current", 0)),
                profit_loss=float(pos_data.get("profit", 0)),
                side=side
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
    
    # ==================== Symbol & Market Data Methods ====================
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """Get information about a trading symbol"""
        if not self._ensure_connected():
            return None
        
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            print(f"Failed to get symbol info for {symbol}")
            return None
        
        return {
            "name": symbol_info.name,
            "bid": symbol_info.bid,
            "ask": symbol_info.ask,
            "point": symbol_info.point,
            "digits": symbol_info.digits,
            "spread": symbol_info.spread,
            "volume_min": symbol_info.volume_min,
            "volume_max": symbol_info.volume_max,
            "volume_step": symbol_info.volume_step,
            "trade_contract_size": symbol_info.trade_contract_size,
            "currency_base": symbol_info.currency_base,
            "currency_profit": symbol_info.currency_profit,
            "currency_margin": symbol_info.currency_margin
        }
    
    def get_terminal_info(self) -> Optional[Dict]:
        """Get MT5 terminal information"""
        if not self._ensure_connected():
            return None
        
        terminal_info = mt5.terminal_info()
        if terminal_info is None:
            return None
        
        return {
            "connected": terminal_info.connected,
            "trade_allowed": terminal_info.trade_allowed,
            "email_enabled": terminal_info.email_enabled,
            "ftp_enabled": terminal_info.ftp_enabled,
            "notifications_enabled": terminal_info.notifications_enabled,
            "mqid": terminal_info.mqid,
            "build": terminal_info.build,
            "maxbars": terminal_info.maxbars,
            "codepage": terminal_info.codepage,
            "cpu_cores": terminal_info.cpu_cores,
            "memory_physical": terminal_info.memory_physical,
            "memory_total": terminal_info.memory_total,
            "memory_available": terminal_info.memory_available,
            "memory_used": terminal_info.memory_used
        }
    
    def __del__(self):
        """Cleanup: disconnect when object is destroyed"""
        self.disconnect()
