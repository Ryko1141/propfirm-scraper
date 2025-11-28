"""
MT5 REST API - Allows clients to connect to MT5 with their credentials
"""
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import secrets
import hashlib
import uuid
import logging
import time
from src.mt5_client import MT5Client
from src.models import AccountSnapshot


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] %(message)s'
)
logger = logging.getLogger("mt5_api")

# Initialize FastAPI app
app = FastAPI(
    title="MT5 REST API",
    description="REST API for MetaTrader 5 client authentication and operations",
    version="1.0.0"
)

# Add CORS middleware to allow web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID middleware for tracing
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID for tracing"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Add to logging context
    old_factory = logging.getLogRecordFactory()
    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.request_id = request_id
        return record
    logging.setLogRecordFactory(record_factory)
    
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)
    
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    
    # Restore old factory
    logging.setLogRecordFactory(old_factory)
    
    return response

# Security
security = HTTPBearer()

# In-memory session storage (in production, use Redis or similar)
active_sessions: Dict[str, Dict] = {}


# ==================== Request/Response Models ====================

class MT5LoginRequest(BaseModel):
    """Request model for MT5 login"""
    account_number: int = Field(..., description="MT5 account number", example=12345678)
    password: str = Field(..., description="MT5 account password")
    server: str = Field(..., description="MT5 broker server", example="MetaQuotes-Demo")
    path: Optional[str] = Field(None, description="Optional path to MT5 terminal")


class MT5LoginResponse(BaseModel):
    """Response model for successful MT5 login"""
    session_token: str = Field(..., description="Session token for authenticated requests")
    account_number: int = Field(..., description="Logged in account number")
    server: str = Field(..., description="Connected server")
    expires_in: int = Field(..., description="Token expiry time in seconds")


class AccountInfoResponse(BaseModel):
    """Response model for account information"""
    login: int
    balance: float
    equity: float
    profit: float
    margin: float
    margin_free: float
    margin_level: float
    leverage: int
    currency: str
    server: str
    company: str


class PositionResponse(BaseModel):
    """Response model for a position"""
    ticket: int
    time: int
    type: int
    magic: int
    identifier: int
    reason: int
    volume: float
    price_open: float
    price_current: float
    sl: float
    tp: float
    profit: float
    swap: float
    symbol: str
    comment: str


class ErrorResponse(BaseModel):
    """Error response model"""
    detail: str
    error_code: Optional[str] = None


# ==================== Session Management ====================

def generate_session_token() -> str:
    """Generate a secure session token"""
    return secrets.token_urlsafe(32)


def create_session(account_number: int, password: str, server: str, 
                   path: Optional[str], client: MT5Client) -> str:
    """Create a new session and return token"""
    token = generate_session_token()
    
    # Hash password for storage (don't store plain text)
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    active_sessions[token] = {
        "account_number": account_number,
        "password_hash": password_hash,
        "server": server,
        "path": path,
        "client": client,
        "created_at": datetime.now(),
        "expires_at": datetime.now() + timedelta(hours=24)
    }
    
    return token


def get_session(token: str) -> Optional[Dict]:
    """Get session by token"""
    session = active_sessions.get(token)
    
    if not session:
        return None
    
    # Check if session expired
    if datetime.now() > session["expires_at"]:
        del active_sessions[token]
        return None
    
    return session


def invalidate_session(token: str):
    """Invalidate a session"""
    if token in active_sessions:
        # Disconnect client
        client = active_sessions[token].get("client")
        if client:
            client.disconnect()
        del active_sessions[token]


async def get_current_session(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Dependency to get current authenticated session"""
    token = credentials.credentials
    session = get_session(token)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token"
        )
    
    return session


# ==================== API Endpoints ====================

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "MT5 REST API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "login": "/api/v1/login",
            "logout": "/api/v1/logout",
            "account": "/api/v1/account",
            "positions": "/api/v1/positions",
            "orders": "/api/v1/orders",
            "snapshot": "/api/v1/snapshot"
        }
    }


@app.get("/healthz")
async def healthz():
    """Health check endpoint (does not touch MT5)"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime": "operational"
    }


@app.post("/api/v1/login", response_model=MT5LoginResponse, responses={401: {"model": ErrorResponse}})
async def login(request: Request, login_data: MT5LoginRequest):
    """
    Authenticate with MT5 and create a session
    
    This endpoint allows clients to log in to their MT5 account by providing:
    - Account number
    - Password
    - Server name
    - Optional terminal path
    
    Returns a session token for subsequent authenticated requests.
    """
    request_id = getattr(request.state, 'request_id', 'unknown')
    logger.info(f"Login attempt for account {login_data.account_number} on {login_data.server}")
    
    try:
        # Create MT5 client
        client = MT5Client(
            account_number=login_data.account_number,
            password=login_data.password,
            server=login_data.server,
            path=login_data.path
        )
        
        # Attempt connection with timeout
        if not client.connect():
            logger.warning(f"Failed to connect account {login_data.account_number}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to connect to MT5. Check credentials and server.",
                headers={"X-Request-ID": request_id}
            )
        
        # Create session
        token = create_session(
            login_data.account_number,
            login_data.password,
            login_data.server,
            login_data.path,
            client
        )
        
        logger.info(f"Login successful for account {login_data.account_number}")
        
        return MT5LoginResponse(
            session_token=token,
            account_number=login_data.account_number,
            server=login_data.server,
            expires_in=86400  # 24 hours
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error for account {login_data.account_number}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"MT5 service temporarily unavailable: {str(e)}",
            headers={"X-Request-ID": request_id}
        )


@app.post("/api/v1/logout")
async def logout(session: Dict = Depends(get_current_session),
                credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Logout and invalidate session
    
    Disconnects from MT5 and removes the session token.
    """
    token = credentials.credentials
    invalidate_session(token)
    return {"message": "Successfully logged out"}


@app.get("/api/v1/account", response_model=AccountInfoResponse)
async def get_account_info(session: Dict = Depends(get_current_session)):
    """
    Get current account information
    
    Returns comprehensive account data including:
    - Balance, equity, profit
    - Margin information
    - Account settings (leverage, currency)
    - Server and company details
    """
    try:
        client: MT5Client = session["client"]
        
        # Ensure connection
        if not client.is_connected:
            if not client.connect():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Failed to reconnect to MT5"
                )
        
        account_info = client.get_account_info()
        
        if not account_info:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve account information"
            )
        
        return AccountInfoResponse(**account_info)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching account info: {str(e)}"
        )


@app.get("/api/v1/positions", response_model=List[PositionResponse])
async def get_positions(session: Dict = Depends(get_current_session)):
    """
    Get all open positions
    
    Returns a list of all currently open positions with:
    - Position details (symbol, volume, type)
    - Price information (entry, current)
    - Profit/loss data
    - Stop loss and take profit levels
    """
    try:
        client: MT5Client = session["client"]
        
        if not client.is_connected:
            if not client.connect():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Failed to reconnect to MT5"
                )
        
        positions = client.get_positions()
        return [PositionResponse(**pos) for pos in positions]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching positions: {str(e)}"
        )


@app.get("/api/v1/orders")
async def get_orders(session: Dict = Depends(get_current_session)):
    """
    Get all pending orders
    
    Returns a list of all pending orders waiting to be executed.
    """
    try:
        client: MT5Client = session["client"]
        
        if not client.is_connected:
            if not client.connect():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Failed to reconnect to MT5"
                )
        
        orders = client.get_orders()
        return {"orders": orders}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching orders: {str(e)}"
        )


@app.get("/api/v1/snapshot")
async def get_account_snapshot(session: Dict = Depends(get_current_session)):
    """
    Get complete account snapshot
    
    Returns a comprehensive snapshot including:
    - Account balances and equity
    - All open positions
    - Total profit/loss (realized and unrealized)
    - Day start anchors for drawdown tracking
    """
    try:
        client: MT5Client = session["client"]
        
        if not client.is_connected:
            if not client.connect():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Failed to reconnect to MT5"
                )
        
        snapshot = client.get_account_snapshot()
        
        # Convert to dict for JSON serialization
        return {
            "timestamp": snapshot.timestamp.isoformat(),
            "balance": snapshot.balance,
            "equity": snapshot.equity,
            "margin_used": snapshot.margin_used,
            "margin_available": snapshot.margin_available,
            "total_profit_loss": snapshot.total_profit_loss,
            "day_start_balance": snapshot.day_start_balance,
            "day_start_equity": snapshot.day_start_equity,
            "positions": [
                {
                    "position_id": pos.position_id,
                    "symbol": pos.symbol,
                    "volume": pos.volume,
                    "entry_price": pos.entry_price,
                    "current_price": pos.current_price,
                    "profit_loss": pos.profit_loss,
                    "side": pos.side
                }
                for pos in snapshot.positions
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating snapshot: {str(e)}"
        )


@app.get("/api/v1/balance")
async def get_balance(session: Dict = Depends(get_current_session)):
    """Get current account balance"""
    try:
        client: MT5Client = session["client"]
        
        if not client.is_connected:
            if not client.connect():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Failed to reconnect to MT5"
                )
        
        balance = client.get_balance()
        return {"balance": balance}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching balance: {str(e)}"
        )


@app.get("/api/v1/equity")
async def get_equity(session: Dict = Depends(get_current_session)):
    """Get current account equity"""
    try:
        client: MT5Client = session["client"]
        
        if not client.is_connected:
            if not client.connect():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Failed to reconnect to MT5"
                )
        
        equity = client.get_equity()
        return {"equity": equity}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching equity: {str(e)}"
        )


@app.get("/api/v1/history")
async def get_history(
    from_days_ago: int = 7,
    session: Dict = Depends(get_current_session)
):
    """
    Get trading history
    
    Args:
        from_days_ago: Number of days of history to fetch (default: 7)
    
    Returns closed deals/positions from the specified period.
    """
    try:
        client: MT5Client = session["client"]
        
        if not client.is_connected:
            if not client.connect():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Failed to reconnect to MT5"
                )
        
        from_date = datetime.now() - timedelta(days=from_days_ago)
        deals = client.get_deals_history(from_date=from_date)
        
        return {
            "from_date": from_date.isoformat(),
            "to_date": datetime.now().isoformat(),
            "deals_count": len(deals),
            "deals": deals
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching history: {str(e)}"
        )


@app.get("/api/v1/symbol/{symbol}")
async def get_symbol_info(symbol: str, session: Dict = Depends(get_current_session)):
    """
    Get information about a specific trading symbol
    
    Args:
        symbol: Symbol name (e.g., EURUSD, GBPUSD, XAUUSD)
    """
    try:
        client: MT5Client = session["client"]
        
        if not client.is_connected:
            if not client.connect():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Failed to reconnect to MT5"
                )
        
        symbol_info = client.get_symbol_info(symbol)
        
        if not symbol_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Symbol '{symbol}' not found"
            )
        
        return symbol_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching symbol info: {str(e)}"
        )


@app.get("/api/v1/server-time")
async def get_server_time(session: Dict = Depends(get_current_session)):
    """Get broker server time"""
    try:
        client: MT5Client = session["client"]
        
        if not client.is_connected:
            if not client.connect():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Failed to reconnect to MT5"
                )
        
        server_time = client.get_server_time()
        
        return {
            "server_time": server_time.isoformat(),
            "timezone_offset": client._server_timezone_offset
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching server time: {str(e)}"
        )


# ==================== Health & Status ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(active_sessions)
    }


# ==================== Startup/Shutdown Events ====================

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    # Disconnect all active sessions
    for token in list(active_sessions.keys()):
        invalidate_session(token)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
