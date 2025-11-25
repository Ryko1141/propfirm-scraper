# Risk Monitor Integration with PropFirm Scraper

## Overview

The prop-risk-monitor has been successfully integrated into the propfirm-scraper repository. The integration enables **database-driven rule loading** using `program_id` fields, allowing the risk monitor to pull specific program rules from the scraped help center documentation.

## Key Features

### 1. Program-Based Rule Loading

Instead of using free-form challenge type strings, the system now supports:

- **`program_id` field** in PropRules and AccountConfig models
- **Database lookup** by program_id to load extracted rules
- **Backward compatibility** with predefined firm rules

### 2. Three-Tier Rule Loading Strategy

The system attempts to load rules in this order:

1. **Database lookup** (if `program_id` provided) - Load rules extracted from help center docs
2. **Predefined rules** (if firm name matches) - Use hardcoded rules for known firms
3. **Custom rules** (fallback) - Use manually defined rules from config

### 3. Integration Points

```
┌─────────────────────────────────────────────────────────────┐
│                    PROPFIRM SCRAPER                          │
│                                                              │
│  ┌────────────────┐         ┌──────────────────┐            │
│  │   Web Scraper  │────────▶│    Database      │            │
│  │  (Playwright)  │         │  (SQLite)        │            │
│  └────────────────┘         │                  │            │
│                             │  • prop_firm     │            │
│                             │  • firm_rule     │            │
│                             │  • help_document │            │
│                             └────────┬─────────┘            │
│                                      │                      │
│                                      │ program_id lookup    │
│                                      ▼                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            RISK MONITOR                              │   │
│  │                                                      │   │
│  │  ┌──────────────┐        ┌──────────────────┐      │   │
│  │  │AccountManager│───────▶│   PropRules      │      │   │
│  │  │              │        │   (with program) │      │   │
│  │  └──────────────┘        └──────────────────┘      │   │
│  │         │                         │                 │   │
│  │         │                         ▼                 │   │
│  │         │                ┌──────────────────┐      │   │
│  │         └───────────────▶│  Rule Validator  │      │   │
│  │                          │  (check_account_ │      │   │
│  │                          │   rules)         │      │   │
│  │                          └──────────────────┘      │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Usage Examples

### Example 1: Load Rules from Database

```json
{
  "accounts": [
    {
      "label": "FundedNext - Stellar 1-Step Challenge",
      "firm": "FundedNext",
      "program_id": "stellar_1step",
      "platform": "mt5",
      "account_id": "12345678",
      "starting_balance": 100000.0,
      "check_interval": 60,
      "enabled": true
    }
  ]
}
```

**What happens:**
1. AccountManager looks up `program_id="stellar_1step"` in database
2. Queries `firm_rule` table for FundedNext + stellar_1step
3. Extracts daily drawdown, total drawdown, and other rules
4. Creates PropRules object with program-specific limits
5. Applies these rules during monitoring

### Example 2: Environment Variables with Program ID

```bash
FIRM_NAME=FundedNext
PROGRAM_ID=stellar_2step
PLATFORM=mt5
ACCOUNT_ID=12345678
STARTING_BALANCE=100000.0
```

**What happens:**
1. `create_account_from_env()` is called with program_id
2. System queries database for stellar_2step rules
3. Falls back to predefined FundedNext rules if not found
4. Falls back to custom rules from MAX_DAILY_LOSS_PERCENT etc.

### Example 3: Predefined Rules (No Database)

```json
{
  "accounts": [
    {
      "label": "FTMO Challenge",
      "firm": "FTMO",
      "platform": "mt5",
      "account_id": "98765432",
      "starting_balance": 100000.0,
      "rules": "ftmo",
      "enabled": true
    }
  ]
}
```

**What happens:**
1. System recognizes `"rules": "ftmo"` as predefined
2. Loads FTMO_RULES from config.py
3. No database lookup needed

## API Changes

### PropRules Model

**Before:**
```python
class PropRules(BaseModel):
    name: str
    max_daily_drawdown_pct: float
    max_total_drawdown_pct: float
    # ...
```

**After:**
```python
class PropRules(BaseModel):
    name: str
    program_id: Optional[str]  # NEW: links to database
    max_daily_drawdown_pct: float
    max_total_drawdown_pct: float
    # ...
```

### AccountConfig Model

**Before:**
```python
class AccountConfig(BaseModel):
    label: str
    firm: str
    platform: str
    # ...
```

**After:**
```python
class AccountConfig(BaseModel):
    label: str
    firm: str
    program_id: Optional[str]  # NEW: for database lookup
    platform: str
    # ...
```

### AccountManager Methods

**New method:**
```python
def get_rules_by_program_id(
    self, 
    firm_name: str, 
    program_id: str
) -> Optional[PropRules]:
    """
    Load rules from database by program_id
    
    Args:
        firm_name: Name of the prop firm
        program_id: Program identifier (e.g., 'stellar_1step')
    
    Returns:
        PropRules object if found, None otherwise
    """
```

**Updated method:**
```python
def create_account_from_env(
    self, 
    firm_name: str = None, 
    program_id: str = None  # NEW parameter
) -> AccountConfig:
```

## Database Schema

The integration relies on this database structure:

```sql
-- Firm table
CREATE TABLE prop_firm (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    domain TEXT NOT NULL
);

-- Rules table (populated by scraper)
CREATE TABLE firm_rule (
    id INTEGER PRIMARY KEY,
    firm_id INTEGER,
    challenge_type TEXT,  -- This is the program_id!
    rule_type TEXT,       -- 'daily_loss_limit', 'max_drawdown', etc.
    value TEXT,           -- '5%', '$5000', etc.
    details TEXT,
    FOREIGN KEY (firm_id) REFERENCES prop_firm(id)
);
```

**Key mapping:**
- `firm_rule.challenge_type` = AccountConfig.program_id
- `firm_rule.rule_type` = Rule category (daily drawdown, total drawdown, etc.)
- `firm_rule.value` = Parsed to extract percentage or numeric values

## Program Taxonomy

The system uses `config/program_taxonomy.json` to map aliases to official program IDs:

```json
{
  "FundedNext": {
    "official_programs": {
      "evaluation_2step": "Evaluation Challenge",
      "stellar_1step": "Stellar 1-Step Challenge",
      "stellar_2step": "Stellar 2-Step Challenge"
    },
    "aliases": {
      "stellar": "stellar_1step",
      "evaluation": "evaluation_2step"
    }
  }
}
```

## Rule Parsing Logic

When loading from database, the system:

1. **Queries by program_id:**
   ```sql
   SELECT rule_type, value, details
   FROM firm_rule
   WHERE firm_id = ? AND challenge_type = ?
   ```

2. **Parses percentage values:**
   - "5%" → 5.0 for max_daily_drawdown_pct
   - "10%" → 10.0 for max_total_drawdown_pct
   - "8%" → 8.0 for profit_target (stored but not used in risk rules)

3. **Falls back to defaults:**
   - If parsing fails, uses safe defaults
   - If no rules found, tries predefined firm rules
   - If all else fails, uses custom rules from environment

## Benefits

### 1. Dynamic Rule Updates
- Scraper extracts new rules from help center
- Risk monitor automatically loads updated rules
- No code changes needed for new programs

### 2. Program-Specific Monitoring
- Different rules for different challenge types
- Stellar 1-Step vs Stellar 2-Step have different limits
- Evaluation vs Instant Funding have different rules

### 3. Centralized Rule Management
- Single source of truth (database)
- Scraper maintains up-to-date rules
- Risk monitor consumes current rules

### 4. Backward Compatibility
- Existing configs still work
- Predefined rules still available
- Custom rules still supported

## Migration Guide

### For Existing Users

**No changes required!** Your existing configuration will continue to work:

```json
{
  "label": "My Account",
  "firm": "FTMO",
  "rules": "ftmo",
  "account_id": "12345"
}
```

### To Enable Database Rules

**Add program_id to your config:**

```json
{
  "label": "My Account",
  "firm": "FundedNext",
  "program_id": "stellar_1step",  // Add this line
  "account_id": "12345"
}
```

**Or set environment variable:**

```bash
PROGRAM_ID=stellar_1step
```

## Testing

### Test Database Lookup

```python
from src.config import AccountManager

# Initialize with database path
manager = AccountManager(db_path="database/propfirm_scraper.db")

# Try loading rules by program_id
rules = manager.get_rules_by_program_id("FundedNext", "stellar_1step")

if rules:
    print(f"Loaded rules: {rules.name}")
    print(f"Daily DD: {rules.max_daily_drawdown_pct}%")
    print(f"Total DD: {rules.max_total_drawdown_pct}%")
else:
    print("No rules found in database")
```

### Test Account Creation

```python
from src.config import AccountManager

manager = AccountManager()

# Create account with program_id
account = manager.create_account_from_env(
    firm_name="FundedNext",
    program_id="stellar_1step"
)

print(f"Account: {account.label}")
print(f"Program: {account.program_id}")
print(f"Rules: {account.rules.name}")
```

## Troubleshooting

### Issue: "No rules found for program_id"

**Cause:** Database doesn't have rules for that program yet.

**Solution:**
1. Run scraper to populate database:
   ```bash
   python -m src.scraper
   ```
2. Check if firm_rule table has entries:
   ```bash
   python database/query_rules.py
   ```
3. Falls back to predefined rules automatically

### Issue: "Firm not found in database"

**Cause:** Firm name doesn't match database entry.

**Solution:**
1. Check exact firm name in database:
   ```sql
   SELECT name FROM prop_firm;
   ```
2. Use exact name in config (case-insensitive)
3. System falls back to predefined rules

### Issue: "Database not found"

**Cause:** Database file doesn't exist at expected path.

**Solution:**
1. Check database path: `database/propfirm_scraper.db`
2. Run database setup if needed:
   ```bash
   python database/ingest_documents.py
   ```
3. System falls back to predefined rules

## Future Enhancements

### Planned Features

1. **Auto-sync**: Automatically sync rules when scraper runs
2. **Rule versioning**: Track rule changes over time
3. **Multi-firm support**: Load rules for multiple firms simultaneously
4. **Rule validation**: Validate extracted rules before applying
5. **Web UI**: Browse and manage rules through web interface

### Possible Extensions

- **Risk profiles**: Save and reuse custom risk profiles
- **Rule templates**: Create templates for common scenarios
- **Rule inheritance**: Inherit base rules with program-specific overrides
- **A/B testing**: Compare performance under different rule sets

## Summary

The integration provides a robust, flexible system for managing prop trading rules:

✅ **Database-driven**: Rules loaded from scraped help center docs  
✅ **Program-specific**: Different rules for different challenge types  
✅ **Backward compatible**: Existing configs continue to work  
✅ **Fallback chain**: Database → Predefined → Custom  
✅ **Easy to use**: Just add program_id to config  

The system bridges the gap between web scraping and real-time risk monitoring, creating a complete solution for prop trading account management.
