# Prop Risk Monitor

A Python-based trading account monitoring system that tracks risk metrics and sends alerts when predefined rules are violated. **Supports both cTrader and MetaTrader 5 platforms** with REST API polling and WebSocket streaming (cTrader only).

## Features

- **Multi-platform support**: Works with both **cTrader** and **MetaTrader 5**
- **Real-time monitoring** of trading accounts
- **Dual modes** (cTrader): REST polling (simple) or WebSocket streaming (advanced)
- **MT5 native integration**: Direct connection to MetaTrader 5 terminal
- **Comprehensive risk rules**:
  - Daily loss limits (realised + unrealised P&L)
  - Position size limits per trade
  - Margin level monitoring
- **Telegram notifications** for rule violations
- **Today's P&L tracking** - monitors realised + unrealised profit/loss
- **Account snapshots** - balance, equity, margin, positions
- Easy configuration via environment variables

## Project Structure

```
prop-risk-monitor/
  src/
    __init__.py          # Package initialization
    config.py            # Configuration management
    ctrader_client.py    # cTrader Open API client (REST + WebSocket)
    mt5_client.py        # MetaTrader 5 API client
    models.py            # Data models
    rules.py             # Risk rule engine
    notifier.py          # Notification system
    runner.py            # Main application runner (supports both platforms)
    async_runner.py      # Async runner (WebSocket streaming - cTrader only)
  examples/
    test_api.py          # cTrader API testing
    test_mt5.py          # MT5 API testing
  .env                   # Environment variables (not committed)
  requirements.txt       # Python dependencies
  README.md              # This file
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/prop-risk-monitor.git
cd prop-risk-monitor
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Set your `PLATFORM` ("ctrader" or "mt5")
   - Fill in platform-specific credentials
   - (Optional) Add Telegram bot token for notifications

## Configuration

Edit the `.env` file with your settings:

### Common Settings (Both Platforms)
- `PLATFORM`: Choose "ctrader" or "mt5"
- `ACCOUNT_ID`: Your trading account ID/number
- `TELEGRAM_BOT_TOKEN`: (Optional) Telegram bot token for notifications
- `TELEGRAM_CHAT_ID`: (Optional) Telegram chat ID for notifications
- `MAX_DAILY_LOSS_PERCENT`: Maximum allowed daily loss percentage (default: 5.0)
- `MAX_POSITION_SIZE_PERCENT`: Maximum position size as percentage of equity (default: 10.0)

### cTrader Specific Settings
- `CTRADER_CLIENT_ID`: Your cTrader API client ID
- `CTRADER_CLIENT_SECRET`: Your cTrader API client secret
- `CTRADER_ACCESS_TOKEN`: Your cTrader access token

### MetaTrader 5 Specific Settings
- `MT5_PASSWORD`: Your MT5 account password
- `MT5_SERVER`: Your broker's MT5 server name
- `MT5_PATH`: (Optional) Custom path to MT5 terminal executable

## Usage

### Quick Start - Test Your Connection

First, test your API connection based on your platform:

**For cTrader:**
```bash
python examples/test_api.py
```

**For MetaTrader 5:**
```bash
python examples/test_mt5.py
```

This will verify your credentials and show live account data.

### Running the Monitor

#### Option 1: REST Polling (Recommended - Works for Both Platforms)

Run the monitor with REST API polling (checks every 60 seconds):

```bash
python -m src.runner
```

The monitor will:
1. Connect to your trading account (cTrader via REST API or MT5 via terminal)
2. Check account status every 60 seconds
3. Evaluate risk rules
4. Send notifications when violations occur

**Note**: The runner automatically detects your platform from the `.env` file.

#### Option 2: WebSocket Streaming (cTrader Only - Advanced)

For real-time updates using WebSocket:

```bash
python -m src.async_runner
```

This provides:
- Real-time position updates
- Event-driven monitoring
- Lower latency alerts
- Automatic reconnection

Press `Ctrl+C` to stop either monitor.

## API Client Features

### cTrader Client

The `CTraderClient` supports both sync and async operations:

#### Synchronous REST API
```python
from src.ctrader_client import CTraderClient

client = CTraderClient()

# Get account data
balance = client.get_balance()
equity = client.get_equity()
margin_free = client.get_margin_free()
unrealised_pnl = client.get_unrealised_pnl()

# Get positions
positions = client.get_open_positions()

# Get today's realised P&L
today_pl = client.get_today_pl()

# Get complete snapshot
snapshot = client.get_account_snapshot()
```

#### Asynchronous WebSocket API
```python
import asyncio
from src.ctrader_client import CTraderClient

async def main():
    client = CTraderClient()
    
    # Connect to WebSocket
    await client.connect()
    await client.subscribe_to_account()
    
    # Listen for real-time updates
    async def handle_update(data):
        print(f"Update: {data}")
    
    await client.listen_for_updates(handle_update)

asyncio.run(main())
```

### MetaTrader 5 Client

The `MT5Client` provides synchronous access to MT5 terminal:

```python
from src.mt5_client import MT5Client

client = MT5Client()

# Connect to MT5 terminal
if client.connect():
    # Get account data
    balance = client.get_balance()
    equity = client.get_equity()
    margin_free = client.get_margin_free()
    unrealised_pnl = client.get_unrealised_pnl()
    
    # Get positions
    positions = client.get_open_positions()
    
    # Get today's realised P&L
    today_pl = client.get_today_pl()
    
    # Get complete snapshot
    snapshot = client.get_account_snapshot()
    
    # Disconnect when done
    client.disconnect()
```

## Risk Rules

### Daily Loss Limit
Monitors combined realised + unrealised P&L since broker midnight. Triggers critical alert when daily loss exceeds the configured percentage of account balance.

**Example**: With `MAX_DAILY_LOSS_PERCENT=5.0`, alert triggers if you lose more than 5% of your balance in a day.

### Position Size Limit
Checks each open position's value against account equity. Triggers warning when any single position exceeds the configured percentage.

**Example**: With `MAX_POSITION_SIZE_PERCENT=10.0`, alert triggers if any position is larger than 10% of your equity.

### Margin Level
Monitors margin usage:
- **Warning**: Margin level below 100% (using more margin than available)
- **Critical**: Margin level below 50% (high risk of margin call)

## Platform-Specific Details

### cTrader Open API

This monitor uses the cTrader Open API which provides:

- **REST API**: For polling account data, positions, and history
- **WebSocket API**: For real-time streaming of price updates and execution events
- **Authentication**: OAuth 2.0 with client credentials

**Data Format Notes**: cTrader API returns values in cents. The client automatically converts to dollars.

**Getting API Credentials**:
1. Create a cTrader Open API application at [https://openapi.ctrader.com](https://openapi.ctrader.com)
2. Get your Client ID and Client Secret
3. Generate an access token with account read permissions
4. Get your trading account ID from cTrader

### MetaTrader 5 Integration

This monitor connects directly to the MT5 terminal using the official MetaTrader5 Python package:

- **Direct terminal connection**: Communicates with local MT5 installation
- **Real-time data**: Access to account, positions, orders, and history
- **No external API**: Works offline with just terminal connection
- **Automatic reconnection**: Handles connection drops gracefully

**Requirements**:
1. MetaTrader 5 terminal installed on your computer
2. Active trading account with your broker
3. "AutoTrading" enabled in MT5 (Tools → Options → Expert Advisors)
4. Account number, password, and server name

**Note**: MT5 terminal should not be running when the monitor starts, or allow DLL imports in the terminal settings.

## Architecture

### REST Polling Mode (Both Platforms)
```
Runner → Client.get_account_snapshot() → API/Terminal
       → RiskRuleEngine.evaluate()
       → Notifier.send_violations()
       → Sleep 60s → Repeat
```

**cTrader**: Polls REST API endpoints  
**MT5**: Queries local terminal via Python API

### WebSocket Streaming Mode (cTrader Only)
```
AsyncRunner → CTraderClient.connect() → WebSocket
            → Subscribe to account events
            → On event: check rules + notify
            → Periodic REST snapshot for full state
```

## Notifications

Violations are sent via:
- Telegram (if configured)
- Console output (always)

## Development

To extend the system:
1. Add new rule validators in `src/rules.py`
2. Add new notification channels in `src/notifier.py`
3. Modify risk thresholds in `.env`

## License

MIT License

## Disclaimer

This software is for educational purposes only. Use at your own risk. The authors are not responsible for any financial losses incurred while using this software.
