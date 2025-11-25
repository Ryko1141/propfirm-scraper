# Prop Firm Rules Configuration Guide

## Overview

The prop risk monitor now supports **firm-specific rule configurations**, making it easy to monitor different prop trading accounts with their unique requirements. You can use predefined rules for popular firms or create custom rules.

## Quick Start

### Option 1: Single Account (Environment Variables)

Set `FIRM_NAME` in your `.env` file to use predefined rules:

```bash
FIRM_NAME=ftmo
STARTING_BALANCE=100000.0
ACCOUNT_ID=your_account_id
# ... other settings
```

### Option 2: Multiple Accounts (JSON Configuration)

Create an `accounts.json` file for monitoring multiple accounts:

```bash
cp accounts.json.example accounts.json
# Edit accounts.json with your account details
python -m src.multi_runner --config accounts.json
```

## Predefined Prop Firm Rules

### FTMO
```python
Firm: "ftmo"
Daily Drawdown: 5%
Total Drawdown: 10%
Risk Per Trade: 1%
Max Open Lots: 20
Max Positions: 10
```

### Alpha Capital Group
```python
Firm: "alpha" or "alpha_capital"
Daily Drawdown: 5%
Total Drawdown: 10%
Risk Per Trade: 1%
Max Open Lots: 10
Max Positions: 8
Requires Stop Loss: Yes
```

### The Funded Trader
```python
Firm: "funded_trader" or "the_funded_trader"
Daily Drawdown: 5%
Total Drawdown: 8%
Risk Per Trade: 2%
Max Open Lots: 15
Max Positions: 12
```

### TopstepFX
```python
Firm: "topstep" or "topstepfx"
Daily Drawdown: 4%
Total Drawdown: 6%
Risk Per Trade: 1.5%
Max Open Lots: 12
Max Positions: 10
```

### 5%ers
```python
Firm: "5percenters" or "5%ers"
Daily Drawdown: 5%
Total Drawdown: 10%
Risk Per Trade: 2%
Max Open Lots: 20
Max Positions: 15
Trading Days Only: No (calendar days)
```

## Rule Types Explained

### Daily Drawdown Limit
**What it checks**: Maximum loss allowed in a single trading day as percentage of balance.

**Example**: With 5% daily drawdown on $100k account:
- ✅ Loss of $4,500 (4.5%) → OK
- ⚠️ Loss of $4,000 (4.0%) at 80% threshold → Warning
- 🚨 Loss of $5,000 (5.0%) → Critical violation

### Total Drawdown Limit
**What it checks**: Maximum drawdown from starting balance (or highest balance).

**Example**: Starting with $100k, total drawdown 10%:
- Balance drops to $92k → 8% drawdown (OK)
- Balance drops to $90k → 10% drawdown (CRITICAL)
- Even if you recover to $95k then drop to $89k → Violation

### Risk Per Trade
**What it checks**: Maximum position size as percentage of balance.

**Example**: With 1% risk per trade on $100k:
- Single position worth $800 → 0.8% (OK)
- Single position worth $1,200 → 1.2% (VIOLATION)

### Max Open Lots
**What it checks**: Total lot size across all open positions.

**Example**: With 10 lot maximum:
- 5 positions × 2 lots = 10 lots (OK)
- 6 positions × 2 lots = 12 lots (VIOLATION)

### Max Positions
**What it checks**: Number of concurrent open trades.

**Example**: With 10 position maximum:
- 9 open trades → OK
- 11 open trades → Warning

### Warning Buffer
**What it checks**: Early warning before hitting limits.

**Example**: With 80% warning buffer on 5% daily drawdown:
- 4.0% loss (80% of 5%) → Warning notification
- 5.0% loss → Critical violation

## Custom Rules Configuration

### Via Environment Variables

Create custom rules in `.env`:

```bash
FIRM_NAME=  # Leave empty for custom rules
MAX_DAILY_LOSS_PERCENT=4.0
MAX_TOTAL_DRAWDOWN_PERCENT=8.0
MAX_POSITION_SIZE_PERCENT=1.5
MAX_OPEN_LOTS=12.0
MAX_POSITIONS=8
WARN_BUFFER_PCT=0.75
```

### Via JSON Configuration

Define custom rules inline in `accounts.json`:

```json
{
  "label": "My Custom Account",
  "firm": "Custom Firm",
  "platform": "mt5",
  "account_id": "12345",
  "starting_balance": 50000.0,
  "rules": {
    "name": "My Custom Rules",
    "max_daily_drawdown_pct": 4.0,
    "max_total_drawdown_pct": 8.0,
    "max_risk_per_trade_pct": 1.5,
    "max_open_lots": 12.0,
    "max_positions": 8,
    "warn_buffer_pct": 0.75,
    "trading_days_only": true,
    "require_stop_loss": true,
    "max_leverage": 100.0
  }
}
```

## Advanced Features

### Trading Days Only
Some firms only count trading days (Mon-Fri) for daily drawdown, while others use calendar days.

```python
trading_days_only: true   # Only Mon-Fri count
trading_days_only: false  # All days count (5%ers style)
```

### Stop Loss Requirement
Some firms require all positions to have a stop loss.

```python
require_stop_loss: true   # Alert if position has no SL
require_stop_loss: false  # SL is optional
```

### Max Leverage
Set maximum allowed leverage (if applicable).

```python
max_leverage: 100.0  # 1:100 max leverage
max_leverage: null   # No leverage limit
```

## Multi-Account Monitoring

Monitor multiple accounts with different rules simultaneously:

```json
{
  "accounts": [
    {
      "label": "FTMO Challenge",
      "firm": "FTMO",
      "platform": "mt5",
      "account_id": "12345",
      "starting_balance": 100000.0,
      "rules": "ftmo",
      "check_interval": 60
    },
    {
      "label": "Alpha Live",
      "firm": "Alpha Capital",
      "platform": "ctrader",
      "account_id": "67890",
      "starting_balance": 50000.0,
      "rules": "alpha",
      "check_interval": 30,
      "telegram_chat_id": "-1001234567890"
    }
  ]
}
```

Run with:
```bash
python -m src.multi_runner --config accounts.json
```

## Notification Examples

### Warning (80% of limit)
```
⚠️ Daily Drawdown Warning

WARNING: Daily drawdown of 4.00% approaching FTMO limit of 5.00%

Value: 4.00
Threshold: 4.00

Time: 2025-11-22 14:30:00
```

### Critical Violation
```
🚨 Daily Drawdown Limit

CRITICAL: Daily drawdown of 5.20% exceeds FTMO limit of 5.00%!

Value: 5.20
Threshold: 5.00

Time: 2025-11-22 14:30:00
```

## Best Practices

### 1. Use Predefined Rules When Available
Predefined rules are tested and match firm requirements:
```bash
FIRM_NAME=ftmo  # Better than custom rules
```

### 2. Set Appropriate Warning Buffers
Get notified before hitting limits:
```bash
WARN_BUFFER_PCT=0.8  # Alert at 80% of limit
```

### 3. Monitor Multiple Accounts Separately
Use `accounts.json` for better organization:
- Different check intervals per account
- Account-specific Telegram chats
- Easy enable/disable per account

### 4. Track Starting Balance Accurately
Total drawdown calculation depends on accurate starting balance:
```bash
STARTING_BALANCE=100000.0  # Set to actual starting balance
```

### 5. Test Configuration First
Use test mode to verify rules:
```bash
python examples/test_api.py  # cTrader
python examples/test_mt5.py  # MT5
```

## Programmatic Usage

### Create Rules Programmatically

```python
from src.config import PropRules, AccountConfig

# Create custom rules
custom_rules = PropRules(
    name="My Firm",
    max_daily_drawdown_pct=4.0,
    max_total_drawdown_pct=8.0,
    max_risk_per_trade_pct=1.5,
    max_open_lots=12.0,
    max_positions=8
)

# Create account config
account = AccountConfig(
    label="My Account",
    firm="My Firm",
    platform="mt5",
    account_id="12345",
    starting_balance=50000.0,
    rules=custom_rules
)

# Use in monitor
from src.runner import RiskMonitor
monitor = RiskMonitor(account_config=account)
monitor.start()
```

### Load from JSON

```python
from src.config import AccountManager

# Load accounts from file
manager = AccountManager("accounts.json")

# Get specific account
account = manager.get_account("12345")

# Get all enabled accounts
enabled = manager.get_enabled_accounts()
```

## Troubleshooting

### "Unknown firm rules: xyz"
Make sure firm name matches predefined options:
- `ftmo`, `alpha`, `alpha_capital`, `funded_trader`, `topstep`, `5percenters`

### "Missing required configuration"
Ensure all required fields are set:
- Platform-specific credentials
- Account ID
- Starting balance (if using total drawdown)

### Rules Not Applied
Check that `.env` or `accounts.json` is properly configured:
```bash
# Verify .env is loaded
python -c "from src.config import Config; print(Config.PLATFORM)"

# Verify JSON is valid
python -c "import json; json.load(open('accounts.json'))"
```

## Adding New Firm Rules

To add a new prop firm's rules to the codebase:

1. Edit `src/config.py`
2. Add new `PropRules` object:

```python
NEW_FIRM_RULES = PropRules(
    name="New Firm Name",
    max_daily_drawdown_pct=5.0,
    max_total_drawdown_pct=10.0,
    max_risk_per_trade_pct=1.0,
    max_open_lots=10.0,
    max_positions=10
)
```

3. Add to `FIRM_RULES` dictionary:

```python
FIRM_RULES = {
    # ... existing firms
    "newfirm": NEW_FIRM_RULES,
}
```

4. Use with `FIRM_NAME=newfirm`

## Summary

The prop rules system provides:
- ✅ Predefined rules for popular firms
- ✅ Custom rule configuration
- ✅ Multi-account support
- ✅ Warning thresholds
- ✅ Flexible notifications
- ✅ Easy JSON configuration

Choose the approach that works best for your setup!
