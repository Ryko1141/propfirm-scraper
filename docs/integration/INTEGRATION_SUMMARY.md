# Integration Summary: prop-risk-monitor → propfirm-scraper

## Date
2025-11-25

## Overview
Successfully merged prop-risk-monitor into propfirm-scraper and implemented program_id-based rule loading, enabling database-driven risk monitoring.

## Changes Made

### 1. Model Updates (`src/config.py`)

#### Added `program_id` field to PropRules
```python
class PropRules(BaseModel):
    name: str
    program_id: Optional[str] = Field(default=None)  # NEW
    max_daily_drawdown_pct: float
    # ... other fields
```

#### Added `program_id` field to AccountConfig
```python
class AccountConfig(BaseModel):
    label: str
    firm: str
    program_id: Optional[str] = Field(default=None)  # NEW
    platform: str
    # ... other fields
```

### 2. AccountManager Enhancements

#### Added database path parameter
```python
def __init__(self, config_file: Optional[str] = None, db_path: Optional[str] = None):
    self.db_path = db_path or os.path.join(Path(__file__).parent.parent, "database", "propfirm_scraper.db")
```

#### Added database rule lookup method
```python
def get_rules_by_program_id(self, firm_name: str, program_id: str) -> Optional[PropRules]:
    """
    Load rules from database by program_id
    
    Queries the firm_rule table for rules matching:
    - firm_id (from firm_name lookup)
    - challenge_type (mapped to program_id)
    
    Returns PropRules object with extracted values or None
    """
```

#### Enhanced `load_from_file` with program_id support
- Checks for `program_id` field in JSON
- Attempts database lookup if program_id provided
- Falls back to predefined rules if database fails
- Falls back to custom rules as last resort

#### Enhanced `create_account_from_env` with program_id parameter
- Added `program_id` parameter
- Tries database lookup first
- Falls back to predefined then custom rules

### 3. Configuration File Updates

#### `.env.example`
Added PROGRAM_ID field:
```bash
# Program ID (optional, for database rule lookup)
# Examples: stellar_1step, stellar_2step, evaluation_2step, stellar_lite
PROGRAM_ID=
```

#### `accounts.json.example`
Added example with program_id:
```json
{
  "label": "FundedNext - Stellar 1-Step",
  "firm": "FundedNext",
  "program_id": "stellar_1step",
  "account_id": "23456789",
  "starting_balance": 100000.0
}
```

### 4. Documentation

#### Created `RISK_MONITOR_INTEGRATION.md`
Comprehensive guide covering:
- Integration architecture
- Usage examples
- API changes
- Database schema mapping
- Migration guide
- Troubleshooting
- Future enhancements

#### Updated `README.md`
- Merged both project READMEs
- Resolved merge conflicts
- Added integration section
- Updated quick start guide
- Added database-driven examples

#### Created `test_integration.py`
Test script covering:
- Database rule lookup
- Account creation with program_id
- JSON configuration loading
- Fallback behavior

### 5. Integration Architecture

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

## Rule Loading Flow

### 1. Database-First Approach (NEW)
```python
# JSON config
{
  "firm": "FundedNext",
  "program_id": "stellar_1step"
}

# Loading process
1. Query database: SELECT * FROM firm_rule WHERE firm_id=? AND challenge_type='stellar_1step'
2. Parse rules: Extract daily_drawdown, max_drawdown from database
3. Create PropRules object with program-specific values
4. Apply during monitoring
```

### 2. Predefined Rules (Existing)
```python
# JSON config
{
  "firm": "FTMO",
  "rules": "ftmo"
}

# Loading process
1. Lookup FIRM_RULES["ftmo"]
2. Use hardcoded FTMO_RULES
3. Apply during monitoring
```

### 3. Custom Rules (Fallback)
```python
# JSON config
{
  "rules": {
    "name": "Custom",
    "max_daily_drawdown_pct": 5.0,
    ...
  }
}

# Loading process
1. Parse rules object
2. Create PropRules from dict
3. Apply during monitoring
```

## Backward Compatibility

✓ All existing configurations continue to work
✓ Predefined firm rules still available
✓ Custom rules still supported
✓ New program_id field is optional

## Benefits

1. **Dynamic Rule Updates**: Scraper updates rules, monitor loads automatically
2. **Program-Specific Rules**: Different rules for different challenge types
3. **Centralized Management**: Single source of truth (database)
4. **Flexible Configuration**: Three-tier fallback (DB → Predefined → Custom)
5. **Easy Integration**: Just add program_id to existing configs

## Database Schema Mapping

```
database.firm_rule.challenge_type  →  AccountConfig.program_id
database.firm_rule.rule_type       →  PropRules field mapping
database.firm_rule.value           →  Parsed percentage values
```

## Testing

Run integration test:
```bash
python test_integration.py
```

Tests:
- ✓ Database rule lookup by program_id
- ✓ Account creation with program_id
- ✓ JSON configuration loading
- ✓ Fallback behavior

## Usage Examples

### Example 1: Database Rules
```bash
# .env
FIRM_NAME=FundedNext
PROGRAM_ID=stellar_1step

# Monitor loads rules from database
python -m src.runner
```

### Example 2: Multi-Account with Mixed Rules
```json
{
  "accounts": [
    {
      "label": "FundedNext - Database Rules",
      "firm": "FundedNext",
      "program_id": "stellar_1step",
      "account_id": "123"
    },
    {
      "label": "FTMO - Predefined Rules",
      "firm": "FTMO",
      "rules": "ftmo",
      "account_id": "456"
    }
  ]
}
```

## Files Modified

1. `src/config.py` - Added program_id support
2. `.env.example` - Added PROGRAM_ID field
3. `accounts.json.example` - Added program_id example
4. `README.md` - Merged and updated documentation

## Files Created

1. `RISK_MONITOR_INTEGRATION.md` - Complete integration guide
2. `INTEGRATION_SUMMARY.md` - This file
3. `test_integration.py` - Integration test script
4. `config/taxonomy_validator.py` - LLM output validation
5. `src/propfirm_scraper/validated_extractor.py` - Validated LLM extraction wrapper
6. `tests/test_taxonomy_validation.py` - Taxonomy validation tests
7. `LLM_GUARDRAILS.md` - Documentation for LLM guardrails

## Next Steps

### For Users
1. ✓ Configuration updated with program_id support
2. ✓ Documentation complete
3. → Run scraper to populate database
4. → Add program_id to account configs
5. → Test with live accounts

### For Developers
1. ✓ Core integration complete
2. ✓ Backward compatibility maintained
3. → Add more rule parsing logic for different rule types
4. → Add rule validation and sanity checks
5. → Add rule versioning and change tracking
6. → Build web UI for rule management

## Migration Guide

### No Changes Required
Existing configs work as-is:
```json
{
  "firm": "FTMO",
  "rules": "ftmo",
  "account_id": "12345"
}
```

### To Enable Database Rules
Add program_id:
```json
{
  "firm": "FundedNext",
  "program_id": "stellar_1step",
  "account_id": "12345"
}
```

### To Test
```bash
# Test integration
python test_integration.py

# Test with live account (after configuring .env)
python -m src.runner
```

## Known Limitations

1. **Database must be populated**: Run scraper first or falls back to predefined rules
2. **Limited rule parsing**: Currently only parses daily_drawdown and max_drawdown percentages
3. **No validation**: Database rules not validated before use
4. **Manual updates**: Database updates require re-running scraper

## Future Enhancements

### Short Term
- [ ] Parse more rule types (profit targets, trading days, etc.)
- [ ] Add rule validation before applying
- [ ] Better error messages for failed lookups
- [ ] Logging for rule loading process
- [x] LLM output validation to prevent hallucinations

### Medium Term
- [ ] Auto-sync rules on schedule
- [ ] Rule change notifications
- [ ] Rule comparison tools
- [ ] Historical rule tracking
- [ ] LLM hallucination rate monitoring

### Long Term
- [ ] Web UI for rule management
- [ ] Rule templates and inheritance
- [ ] A/B testing framework
- [ ] Multi-firm comparison

## Conclusion

The integration successfully bridges web scraping and real-time risk monitoring, creating a complete solution for prop trading account management. The system maintains backward compatibility while adding powerful new capabilities through program_id-based database rule loading.

Key achievements:
1. **Automated rule extraction and application** - scrape help centers, store rules in database, load rules by program during monitoring, all without manual rule updates
2. **LLM guardrails** - prevent hallucinated program names from corrupting the database through taxonomy validation
3. **Three-tier fallback** - Database → Predefined → Custom rules for maximum flexibility

## LLM Guardrails Implementation

To prevent hallucinated program names (like "Stellar Instant 2-Step Challenge") from entering the system, comprehensive LLM output validation was implemented:

### Core Validation Function

```python
from config.taxonomy_validator import map_alias_to_program

# Validate LLM output
candidate = llm_output.lower()
program_id = map_alias_to_program("FundedNext", candidate)

if program_id is None:
    # Hallucination detected → reject
    log_warning(f"LLM hallucinated: {candidate}")
else:
    # Valid program → safe to use
    save_to_database(program_id)
```

### Features

- **Taxonomy validation** against `program_taxonomy.json`
- **Fuzzy matching** for common variations (e.g., "stellar1step" → "stellar_1step")
- **Alias support** (e.g., "lite" → "stellar_lite")
- **Hallucination detection** with detailed reporting
- **Strict/permissive modes** for different use cases
- **Validation reports** with hallucination rates

### Integration Points

1. **LLM Extractor** - Validates all extracted program names before saving
2. **Hybrid Extractor** - Validates LLM additions to pattern-based extraction
3. **Database Ingestion** - Validates at database boundary before INSERT
4. **Risk Monitor** - Validates program_id when loading from config

### Testing

Run validation tests:
```bash
python tests/test_taxonomy_validation.py
```

Validate extraction file:
```bash
python -m src.propfirm_scraper.validated_extractor \
    output/rules_llm.json \
    --firm FundedNext \
    --output output/rules_validated.json
```

See [LLM_GUARDRAILS.md](LLM_GUARDRAILS.md) for complete documentation.
