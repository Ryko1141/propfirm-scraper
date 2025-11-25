# Platform Comparison: cTrader vs MetaTrader 5

## Overview

This risk monitor supports both **cTrader** and **MetaTrader 5** platforms. Here's how they compare and which one to choose.

## Quick Comparison

| Feature | cTrader | MetaTrader 5 |
|---------|---------|--------------|
| **Connection Type** | REST API + WebSocket | Direct terminal connection |
| **Setup Complexity** | Moderate (OAuth setup) | Easy (just login credentials) |
| **Real-time Streaming** | ✅ Yes (WebSocket) | ❌ No (polling only) |
| **Offline Operation** | ❌ No (requires internet) | ✅ Yes (local terminal) |
| **Platform Support** | Windows, Linux, macOS | Windows only |
| **API Limitations** | Rate limits apply | No limits (local) |
| **Terminal Required** | ❌ No | ✅ Yes (MT5 must be installed) |
| **Multiple Accounts** | Easy (multiple tokens) | Moderate (multiple connections) |
| **Server Time Detection** | ✅ Automatic | ✅ Automatic |

## cTrader Open API

### Advantages
- ✅ **Cloud-based**: No need for terminal to be running
- ✅ **WebSocket streaming**: Real-time event notifications
- ✅ **Cross-platform**: Works on any OS
- ✅ **Multiple accounts**: Easy to manage multiple accounts
- ✅ **Modern API**: RESTful + WebSocket architecture

### Disadvantages
- ❌ **Setup complexity**: OAuth configuration required
- ❌ **Rate limits**: API calls are limited
- ❌ **Internet required**: Cannot work offline
- ❌ **Data format**: Values in cents (auto-converted)

### Best For
- Cloud-based monitoring solutions
- Real-time event-driven alerts
- Multiple account monitoring
- Cross-platform deployments
- VPS/server deployments

### Setup Requirements
1. Register at [https://openapi.ctrader.com](https://openapi.ctrader.com)
2. Create an application
3. Generate OAuth credentials
4. Get access token
5. Find your account ID

## MetaTrader 5 Python API

### Advantages
- ✅ **Simple setup**: Just account credentials
- ✅ **No rate limits**: Local API calls
- ✅ **Offline capable**: Works without internet (after login)
- ✅ **Direct access**: No intermediary services
- ✅ **Native integration**: Official MetaQuotes API

### Disadvantages
- ❌ **Windows only**: MT5 terminal runs on Windows
- ❌ **Terminal required**: MT5 must be installed
- ❌ **No real-time events**: Must poll for updates
- ❌ **Single machine**: Monitor tied to machine with terminal
- ❌ **Terminal dependency**: Issues if terminal crashes

### Best For
- Windows desktop monitoring
- Simple setup requirements
- Local/personal monitoring
- Brokers without cTrader
- No API rate limit concerns

### Setup Requirements
1. Install MetaTrader 5 terminal
2. Have account number, password, server name
3. Enable "AutoTrading" in terminal
4. Allow DLL imports (if terminal is running)

## Technical Differences

### Data Access

**cTrader**:
```python
# REST API call over HTTPS
GET https://openapi.ctrader.com/v2/accounts/{id}
Authorization: Bearer {token}

# Response in JSON (values in cents)
{
  "balance": 50000,  # $500.00
  "equity": 52500,   # $525.00
  ...
}
```

**MetaTrader 5**:
```python
# Direct Python API call to terminal
import MetaTrader5 as mt5
mt5.initialize()
mt5.login(account, password, server)
account_info = mt5.account_info()

# Native Python objects (values in dollars)
account_info.balance  # 500.00
account_info.equity   # 525.00
```

### Real-time Updates

**cTrader** (WebSocket):
```python
# Event-driven updates
async def on_position_opened(event):
    await check_rules()  # Immediate response

# Subscribe to events
await client.listen_for_updates(on_position_opened)
```

**MetaTrader 5** (Polling):
```python
# Must poll periodically
while True:
    snapshot = client.get_account_snapshot()
    check_rules(snapshot)
    time.sleep(60)  # Check every minute
```

### Connection Management

**cTrader**:
- Stateless REST calls (no persistent connection needed)
- WebSocket maintains connection for streaming
- Automatic token refresh required
- Works from anywhere with internet

**MetaTrader 5**:
- Must connect to terminal on startup
- Connection persists until disconnect
- Automatic reconnection on failure
- Terminal must be accessible (local or RDP)

## Performance Considerations

### Latency

**cTrader**:
- REST API: ~100-500ms per request (depends on location)
- WebSocket: <50ms for event notifications
- Network dependent

**MetaTrader 5**:
- Local API: <10ms per request
- No network latency
- CPU/memory dependent

### Resource Usage

**cTrader**:
- Minimal CPU (just HTTP requests)
- Low memory (~50MB)
- Network bandwidth required

**MetaTrader 5**:
- Moderate CPU (terminal + Python)
- Higher memory (~200MB terminal + ~50MB Python)
- No network bandwidth (after login)

## Choosing Your Platform

### Choose cTrader if:
- ✅ You want real-time event notifications
- ✅ You need cross-platform support
- ✅ You're deploying to VPS/cloud
- ✅ You manage multiple accounts
- ✅ Your broker supports cTrader Open API
- ✅ You prefer cloud-based solutions

### Choose MetaTrader 5 if:
- ✅ You want simple setup
- ✅ You're running on Windows desktop
- ✅ Your broker doesn't have cTrader
- ✅ You prefer local/offline solutions
- ✅ You want zero API rate limits
- ✅ You already use MT5 terminal

### Choose Both if:
- ✅ You trade on multiple platforms
- ✅ You want backup monitoring
- ✅ You're testing/comparing platforms

## Migration

Switching between platforms is easy - just change your `.env` file:

```bash
# Switch from cTrader to MT5
PLATFORM=mt5  # Change from "ctrader" to "mt5"

# Update credentials
ACCOUNT_ID=your_mt5_account_number
MT5_PASSWORD=your_password
MT5_SERVER=your_broker_server
```

The same monitoring code, rules, and notifications work for both platforms!

## Common Use Cases

### Use Case 1: Personal Desktop Trader
**Recommendation**: MetaTrader 5
- Simple setup with credentials
- No API registration needed
- Works great for single machine

### Use Case 2: Professional Prop Trader
**Recommendation**: cTrader
- Real-time alerts critical
- Multiple accounts to monitor
- Cloud-based reliability

### Use Case 3: VPS/Cloud Deployment
**Recommendation**: cTrader
- No terminal required on server
- Easier to scale
- Better for automation

### Use Case 4: Development/Testing
**Recommendation**: MetaTrader 5
- Quick to set up
- Easy to debug locally
- No API quotas to worry about

## Summary

Both platforms are fully supported with identical features (except WebSocket for cTrader). Choose based on your:
- Broker availability
- Operating system
- Deployment environment
- Real-time requirements
- Setup preferences

The monitor abstracts platform differences, providing consistent risk management regardless of your choice!
