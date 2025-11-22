# Prop Risk Monitor

A Python-based trading account monitoring system that tracks risk metrics and sends alerts when predefined rules are violated.

## Features

- Real-time monitoring of cTrader trading accounts
- Configurable risk rules:
  - Daily loss limits
  - Position size limits
  - Margin level monitoring
- Telegram notifications for rule violations
- Easy configuration via environment variables

## Project Structure

```
prop-risk-monitor/
  src/
    __init__.py          # Package initialization
    config.py            # Configuration management
    ctrader_client.py    # cTrader API client
    models.py            # Data models
    rules.py             # Risk rule engine
    notifier.py          # Notification system
    runner.py            # Main application runner
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

Run the monitor:

```bash
python -m src.runner
```

The monitor will:
1. Connect to your cTrader account
2. Check account status every 60 seconds (configurable)
3. Evaluate risk rules
4. Send notifications when violations occur

Press `Ctrl+C` to stop the monitor.

## Risk Rules

### Daily Loss Limit
Triggers when daily loss exceeds the configured percentage of account balance.

### Position Size Limit
Triggers when any single position exceeds the configured percentage of account equity.

### Margin Level
- **Warning**: Margin level below 100%
- **Critical**: Margin level below 50%

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
