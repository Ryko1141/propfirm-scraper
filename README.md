# Prop Risk Monitor

A Python-based trading account monitoring system that tracks risk metrics and sends alerts when predefined rules are violated. Supports both REST API polling and WebSocket streaming for real-time updates.

## Features

- **Real-time monitoring** of cTrader trading accounts via Open API
- **Dual modes**: REST polling (simple) or WebSocket streaming (advanced)
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
    models.py            # Data models
    rules.py             # Risk rule engine
    notifier.py          # Notification system
    runner.py            # Main application runner (REST polling)
    async_runner.py      # Async runner (WebSocket streaming)
  examples/
    test_api.py          # API testing and examples
  .env                   # Environment variables (not committed)
  requirements.txt       # Python dependencies
  README.md             # This file
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
   - Copy `.env` and fill in your credentials
   - Update cTrader API credentials
   - (Optional) Add Telegram bot token for notifications

## Configuration

Edit the `.env` file with your settings:

- `CTRADER_CLIENT_ID`: Your cTrader API client ID
- `CTRADER_CLIENT_SECRET`: Your cTrader API client secret
- `CTRADER_ACCESS_TOKEN`: Your cTrader access token
- `ACCOUNT_ID`: Your trading account ID
- `TELEGRAM_BOT_TOKEN`: (Optional) Telegram bot token for notifications
- `TELEGRAM_CHAT_ID`: (Optional) Telegram chat ID for notifications
- `MAX_DAILY_LOSS_PERCENT`: Maximum allowed daily loss percentage (default: 5.0)
- `MAX_POSITION_SIZE_PERCENT`: Maximum position size as percentage of equity (default: 10.0)

## Usage

### Quick Start - Test Your Connection

First, test your API connection:

```bash
python examples/test_api.py
```

This will verify your credentials and show live account data.

### Option 1: REST Polling (Recommended for Beginners)

Run the monitor with REST API polling (checks every 60 seconds):

```bash
python -m src.runner
```

The monitor will:
1. Connect to your cTrader account via REST API
2. Check account status every 60 seconds
3. Evaluate risk rules
4. Send notifications when violations occur

### Option 2: WebSocket Streaming (Advanced)

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

The `CTraderClient` supports both sync and async operations:

### Synchronous REST API
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

### Asynchronous WebSocket API
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

## cTrader Open API Details

This monitor uses the cTrader Open API which provides:

- **REST API**: For polling account data, positions, and history
- **WebSocket API**: For real-time streaming of price updates and execution events
- **Authentication**: OAuth 2.0 with client credentials

### Data Format Notes

cTrader API returns values in cents (multiply by 100). The client automatically converts:
- Balance, equity, margin → dollars
- Position volumes → lots
- Profit/loss values → dollars

### Getting API Credentials

1. Create a cTrader Open API application at [https://openapi.ctrader.com](https://openapi.ctrader.com)
2. Get your Client ID and Client Secret
3. Generate an access token with account read permissions
4. Get your trading account ID from cTrader

## Architecture

### REST Polling Mode (Simple)
```
Runner → CTraderClient.get_account_snapshot() → REST API
       → RiskRuleEngine.evaluate()
       → Notifier.send_violations()
       → Sleep 60s → Repeat
```

### WebSocket Streaming Mode (Advanced)
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
