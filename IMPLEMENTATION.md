# cTrader Open API Implementation

## Overview

The cTrader client has been fully implemented with both REST and WebSocket support, following cTrader's Open API specification.

## Implementation Details

### REST API (Synchronous)

The REST API implementation provides polling-based monitoring with these key methods:

#### Account Data Methods
- `get_account_info()` - Full account details (balance, equity, margin, unrealised P&L)
- `get_balance()` - Current account balance
- `get_equity()` - Current equity (balance + unrealised P&L)
- `get_margin_used()` - Margin currently in use
- `get_margin_free()` - Available free margin
- `get_unrealised_pnl()` - Unrealised profit/loss from open positions

#### Position & Order Methods
- `get_positions()` - List of open positions
- `get_open_positions()` - Parsed Position objects
- `get_orders()` - Pending orders
- `get_deals_history()` - Historical closed positions

#### Analysis Methods
- `get_today_pl()` - Realised P&L since broker midnight
- `get_account_snapshot()` - Complete account state snapshot

### WebSocket API (Asynchronous)

The WebSocket implementation provides real-time event streaming:

#### Connection Methods
- `async connect()` - Establish WebSocket connection
- `async subscribe_to_account()` - Subscribe to account updates
- `async listen_for_updates(callback)` - Listen for real-time events
- `async disconnect()` - Close connection

#### Event Types Handled
- **ProtoOASpotEvent** (2126) - Price updates
- **ProtoOAExecutionEvent** (2132) - Position/order events
- **ProtoOAAccountAuthRes** (2142) - Authentication response

## Data Conversion

cTrader API returns values in cents/hundredths. The client automatically converts:

```python
# API returns cents
api_balance = 50000  # = $500.00

# Client converts
balance = float(api_balance) / 100  # = 500.00
```

**Converted fields:**
- Balance, equity, margin values
- Profit/loss values
- Position volumes (to lots)

## Usage Patterns

### Simple REST Polling (Recommended)

Best for:
- Simple monitoring needs
- 5-60 second update intervals
- Easy to understand and debug
- Lower complexity

```python
client = CTraderClient()
snapshot = client.get_account_snapshot()
print(f"Equity: ${snapshot.equity:.2f}")
```

### Advanced WebSocket Streaming

Best for:
- Real-time event response
- Sub-second latency requirements
- High-frequency monitoring
- Event-driven architecture

```python
async def main():
    client = CTraderClient()
    await client.connect()
    await client.subscribe_to_account()
    
    async def on_update(data):
        if data['payloadType'] == 2132:  # Execution event
            # Position opened/closed
            await check_rules()
    
    await client.listen_for_updates(on_update)
```

## Today's P&L Calculation

The `get_today_pl()` method calculates realised P&L from midnight:

1. Get current UTC time
2. Calculate broker midnight (approximate - may need timezone adjustment)
3. Fetch all deals closed since midnight
4. Sum the `closeProfit` values
5. Convert from cents to dollars

**Note**: Broker timezone is typically UTC+2 or UTC+3. You may need to adjust the midnight calculation based on your broker's server location.

## Error Handling

All REST methods include:
- Timeout protection (10 seconds)
- Exception catching
- Empty/safe defaults on failure
- Error logging

```python
try:
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()
except requests.RequestException as e:
    print(f"Error: {e}")
    return {}  # Safe default
```

## API Endpoints

### REST Base URL
```
https://openapi.ctrader.com/v2
```

### WebSocket URL
```
wss://openapi.ctrader.com
```

### Key Endpoints
- `GET /accounts/{accountId}` - Account info
- `GET /accounts/{accountId}/positions` - Open positions
- `GET /accounts/{accountId}/orders` - Pending orders
- `GET /accounts/{accountId}/deals` - Historical deals

## Testing

Use the provided test script to verify your setup:

```bash
python examples/test_api.py
```

This will:
1. Test REST API connection
2. Display account data
3. Show open positions
4. Calculate today's P&L
5. Optionally test WebSocket streaming

## Next Steps

### For Basic Usage
1. Copy `.env.example` to `.env`
2. Fill in your cTrader credentials
3. Run: `python examples/test_api.py`
4. Start monitoring: `python -m src.runner`

### For Advanced Usage
1. Complete basic setup first
2. Test WebSocket: `python -m src.async_runner`
3. Customize `async_runner.py` for your needs
4. Implement custom event handlers

## Known Limitations

1. **Broker Timezone**: Today's P&L calculation uses UTC midnight approximation
2. **WebSocket Reconnection**: Basic implementation - may need enhancement for production
3. **Rate Limiting**: No built-in rate limiting - be mindful of API quotas
4. **Historical Data**: Limited to recent deals - full history may require pagination

## Future Enhancements

- [ ] Automatic broker timezone detection
- [ ] WebSocket auto-reconnection with exponential backoff
- [ ] Rate limiting and request throttling
- [ ] Historical data pagination
- [ ] Multiple account monitoring
- [ ] Position tracking and analytics
- [ ] Trade journal integration
