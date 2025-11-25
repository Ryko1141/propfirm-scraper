# Max Daily Drawdown - "Whichever Is Higher" Rule

## Overview

This implementation ensures that max daily drawdown enforcement cannot be circumvented by hiding risk in floating losses. The rule always uses the **WORST CASE** between equity-based and balance-based calculations.

## The Rule

### Day Start Anchor (Server Midnight)

At the first tick after server date changes (00:00 server time):

```python
day_start_balance = account_balance
day_start_equity = account_equity
day_start_anchor = max(day_start_balance, day_start_equity)
```

The `day_start_anchor` becomes the reference point for that calendar day's max daily drawdown.

### Daily Drawdown Calculation (Every Tick)

On each check, calculate losses from both perspectives:

```python
# Get current values
current_balance = account_balance
current_equity = account_equity

# Calculate loss from anchor using both metrics
daily_loss_by_equity = day_start_anchor - current_equity
daily_loss_by_balance = day_start_anchor - current_balance

# USE WHICHEVER SHOWS THE LARGER LOSS
daily_loss_money = max(daily_loss_by_equity, daily_loss_by_balance)

# Convert to percentage
daily_loss_pct = -(100.0 * daily_loss_money / day_start_anchor)
```

### Rule Enforcement

```python
if abs(daily_loss_pct) >= max_daily_drawdown_pct:
    # HARD LIMIT BREACH
    # - Close all open positions
    # - Disable new trading
    # - Send critical alert

elif abs(daily_loss_pct) >= (max_daily_drawdown_pct * warn_buffer):
    # WARNING THRESHOLD (e.g., 80% of limit)
    # - Send warning alert
    # - Continue monitoring
```

## Why This Matters

### Scenario 1: Floating Loss Dominates

**Situation**: Trader has $5k floating loss in open positions, no closed trades

- **Balance**: $100k (unchanged)
- **Equity**: $95k (balance - $5k floating loss)
- **Loss by Balance**: $0 (0%)
- **Loss by Equity**: $5k (5%)
- **Loss Used**: $5k (5%) ← **EQUITY DOMINATES**

**Without this rule**: Trader could keep losses "floating" and not trigger drawdown limit.

**With this rule**: Floating loss is immediately captured and enforced.

### Scenario 2: Realized Loss Dominates

**Situation**: Trader closed trades at $5k loss, has $2k floating profit

- **Balance**: $95k (realized $5k loss)
- **Equity**: $97k (balance + $2k floating profit)
- **Loss by Balance**: $5k (5%)
- **Loss by Equity**: $3k (3%)
- **Loss Used**: $5k (5%) ← **BALANCE DOMINATES**

**Without this rule**: Floating profit could mask realized losses.

**With this rule**: Realized loss is enforced regardless of floating profit.

### Scenario 3: Combined Losses

**Situation**: Trader has both realized ($4k) and floating ($2k) losses

- **Balance**: $96k (realized $4k loss)
- **Equity**: $94k (balance - $2k floating loss)
- **Loss by Balance**: $4k (4%)
- **Loss by Equity**: $6k (6%)
- **Loss Used**: $6k (6%) ← **TOTAL EXPOSURE**

**This captures the TRUE RISK**: Total exposure regardless of what's realized vs floating.

### Scenario 4: Day Start With Floating Profit

**Situation**: Day starts with $2k floating profit from open positions

- **Day Start Balance**: $98k
- **Day Start Equity**: $100k (has $2k floating profit)
- **Day Start Anchor**: $100k ← **Uses higher value**

Later in the day:
- **Current Balance**: $98k
- **Current Equity**: $95k (lost the $2k profit + $3k more)
- **Loss Used**: $5k (5%) calculated from $100k anchor

**This prevents gaming**: Can't benefit from starting the day with high equity then losing it.

## Implementation Details

### AccountSnapshot Model

```python
@dataclass
class AccountSnapshot:
    # ... existing fields ...
    day_start_balance: Optional[float] = None
    day_start_equity: Optional[float] = None
    
    @property
    def day_start_anchor(self) -> float:
        """Get day start anchor - max of balance or equity"""
        if self.day_start_balance and self.day_start_equity:
            return max(self.day_start_balance, self.day_start_equity)
        # Fallback to balance if not set
        return self.balance
    
    @property
    def daily_drawdown_pct(self) -> float:
        """Calculate daily DD using worst-case rule"""
        anchor = self.day_start_anchor
        
        # Calculate losses from both perspectives
        loss_by_equity = anchor - self.equity
        loss_by_balance = anchor - self.balance
        
        # Use whichever is larger (worst case)
        daily_loss = max(loss_by_equity, loss_by_balance)
        
        # Return as negative percentage
        return -(100.0 * daily_loss / anchor)
```

### Client Implementation

Both `CTraderClient` and `MT5Client` implement day start tracking with automatic broker server time detection:

```python
def _update_day_start_anchor(self, balance: float, equity: float):
    """Update day start values when new day detected"""
    now = self.get_server_time()  # Uses broker server time, not local time
    current_date = now.date()
    
    # New day detected
    if self._current_date is None or current_date != self._current_date:
        self._day_start_balance = balance
        self._day_start_equity = equity
        self._current_date = current_date
        
        anchor = max(balance, equity)
        print(f"Day start anchor: ${anchor:,.2f} (using higher)")
```

### Automatic Day Start Detection

The clients automatically detect new trading days and update the anchor using **broker server time**:

1. **First connection**: Detects broker timezone offset automatically
2. **First run**: Sets anchor to current balance/equity (whichever is higher)
3. **Each snapshot**: Checks if broker server date changed (uses `get_server_time()`)
4. **New day detected**: Updates anchor to new day's higher value at broker midnight
5. **Same day**: Continues using existing anchor

**Important**: Day rollover detection uses the broker's server time, not your local time. This ensures accurate daily drawdown tracking regardless of your location or timezone.

## Configuration

### Prop Firm Rules

All predefined prop firm rules use this calculation:

```python
FTMO_RULES = PropRules(
    name="FTMO",
    max_daily_drawdown_pct=5.0,  # 5% max loss per day
    warn_buffer_pct=0.8,         # Warn at 80% (4% loss)
    # ... other rules ...
)
```

### Warning Buffer

The `warn_buffer_pct` provides early warning:

- **max_daily_drawdown_pct**: 5.0% (hard limit)
- **warn_buffer_pct**: 0.8 (80%)
- **Warning triggers at**: 4.0% loss (5.0% × 0.8)
- **Hard limit triggers at**: 5.0% loss

This gives traders time to react before hitting the hard limit.

## Testing

See `examples/test_daily_dd_worst_case.py` for comprehensive examples:

```bash
python examples/test_daily_dd_worst_case.py
```

This demonstrates:
1. Floating loss dominates (equity-based)
2. Realized loss dominates (balance-based)
3. Combined losses (both types)
4. Day start with higher equity
5. Comparison table across scenarios

## Key Behaviors

### ✅ Captures Floating Losses

Unrealized losses in open positions are immediately counted toward daily drawdown.

### ✅ Captures Realized Losses

Closed trades at a loss are counted even if floating profit exists.

### ✅ Cannot Game the System

Traders cannot:
- Hide losses by keeping positions open
- Mask losses with floating profits
- Benefit unfairly from high starting equity

### ✅ Fair Treatment

Uses the same calculation consistently:
- New traders starting with $100k balance, $100k equity
- Experienced traders with floating positions

### ✅ Transparent Calculation

The exact calculation is visible in logs:
```
Day start anchor updated: Balance=$100,000.00, Equity=$102,000.00, 
Anchor=$102,000.00 (using higher)
```

## Comparison With Simple Methods

### Method 1: Balance Only (❌ VULNERABLE)

```python
daily_loss_pct = (balance - day_start_balance) / day_start_balance
```

**Problem**: Doesn't count floating losses. Trader can rack up $10k floating loss and show 0% drawdown.

### Method 2: Equity Only (❌ VULNERABLE)

```python
daily_loss_pct = (equity - day_start_equity) / day_start_equity
```

**Problem**: Floating profits can mask realized losses. Trader loses $5k realized but shows $2k profit from floating = only $3k loss counted.

### Method 3: Whichever Is Higher (✅ CORRECT)

```python
loss_by_equity = anchor - equity
loss_by_balance = anchor - balance
daily_loss = max(loss_by_equity, loss_by_balance)
daily_loss_pct = -(100.0 * daily_loss / anchor)
```

**Solution**: Always captures worst case. Cannot be gamed.

## Example Output

```
================================================================================
Example 2: Realized Loss Dominates (Balance-Based)
================================================================================

Day Start Anchor: $100,000.00 (max of balance/equity)
Current Balance:  $95,000.00 (realized $5k loss)
Current Equity:   $97,000.00 (balance + $2k floating profit)

Loss by Equity:   $3,000.00 (-3.00%)
Loss by Balance:  $5,000.00 (-5.00%)
Loss Used: $5,000.00 (-5.00%) ← WORST CASE

╭───────────────────────────────────────────────────────╮
│ EXAMPLE-2:                                            │
│ HARD DAILY_DD – 🚨 Daily DD limit breached: -5.00%    │
╰───────────────────────────────────────────────────────╯
```

## References

This implementation follows the prop firm industry standard for daily drawdown enforcement, ensuring traders cannot circumvent risk limits through any trading strategy or timing.

The "whichever is higher" approach is used by major prop firms including FTMO, The5%ers, and others to maintain fair and consistent risk management.
