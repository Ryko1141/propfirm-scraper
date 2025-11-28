# Guardian

**Real-time trading account monitoring and risk management system for proprietary trading firms.**

Guardian is a comprehensive Python framework that combines intelligent web scraping, rule extraction, and live account monitoring to help prop traders stay within their firm's risk parameters. It monitors MT5 and cTrader accounts in real-time, enforces daily drawdown limits, tracks position sizes, and alerts you before you breach critical rules.

## 🎯 What Guardian Does

### 1. **Intelligent Rule Extraction**
- Scrapes prop firm help centers with Cloudflare bypass capabilities
- Extracts trading rules using hybrid pattern matching + LLM analysis
- Stores structured rule data in SQLite with versioning and change detection
- Supports firm-specific program taxonomies (e.g., FundedNext's Stellar 1-Step vs Evaluation challenges)

### 2. **Real-Time Account Monitoring**
- Connects to **MetaTrader 5** and **cTrader** platforms
- Monitors account balance, equity, positions, and margin in real-time
- Implements "whichever is higher" daily drawdown calculation (worst-case between equity and balance)
- Multi-account monitoring with independent rule sets
- Async monitoring for multiple accounts simultaneously

### 3. **MT5 REST API** ⭐ NEW
- **RESTful API** for remote MT5 account access
- **Session-based authentication** with secure token management
- **Multi-client support** - multiple users can connect with their own credentials
- **Comprehensive endpoints** for account data, positions, orders, and history
- **Interactive documentation** via Swagger UI
- **Web and mobile ready** with CORS support
- **Easy integration** with any programming language or platform

### 4. **Risk Rule Enforcement**
Guardian monitors and enforces critical prop firm rules:
- **Daily Drawdown Limits** - Prevents catastrophic daily losses
- **Total Drawdown Limits** - Tracks drawdown from starting balance
- **Risk Per Trade** - Ensures position sizes stay within limits
- **Maximum Lot Sizes** - Controls total exposure
- **Position Limits** - Caps concurrent open positions
- **Margin Levels** - Warns when margin gets dangerously low
- **Stop Loss Requirements** - Validates required stop losses

### 5. **Smart Alerts**
- Console notifications with rich formatting
- Warning thresholds (default 80% of limit)
- Critical breach alerts
- Extensible notification system (email, Telegram, Discord ready)

## 📁 Project Structure

```
guardian/
├── src/                      # Core monitoring and API clients
│   ├── mt5_client.py         # MetaTrader 5 integration
│   ├── mt5_api.py            # ⭐ MT5 REST API server
│   ├── ctrader_client.py     # cTrader integration
│   ├── rules.py              # Risk rule engine
│   ├── models.py             # Data models (Position, AccountSnapshot, RuleBreach)
│   ├── config.py             # Configuration and predefined firm rules
│   ├── notifier.py           # Alert notification system
│   ├── runner.py             # Single-account monitoring
│   ├── multi_runner.py       # Multi-account monitoring
│   ├── async_runner.py       # Async monitoring
│   └── propfirm_scraper/     # Web scraping and extraction
│       ├── scraper.py        # Cloudflare-proof web scraper
│       ├── fast_extractor.py # Pattern-based rule extraction
│       ├── hybrid_extractor.py # Pattern + LLM extraction
│       └── validated_extractor.py # Taxonomy-aware extraction
├── database/                 # Rule storage and analysis
│   ├── schema.sql            # Database schema
│   ├── ingest_documents.py   # Load scraped docs into DB
│   ├── extract_rules.py      # Extract structured rules
│   └── query_rules.py        # Query rule database
├── config/                   # Firm-specific configurations
│   ├── program_taxonomy.json # Program type mappings
│   ├── patterns.py           # Extraction patterns
│   └── taxonomy_validator.py # Taxonomy validation
├── examples/                 # Usage examples
│   ├── api/                  # ⭐ MT5 REST API examples
│   │   ├── test_mt5_api.py  # Python client example
│   │   └── mt5_api_client.html # Web-based API client
│   ├── usage_example.py      # End-to-end demo
│   ├── test_mt5.py           # MT5 monitoring example
│   ├── test_rules_offline.py # Rule testing without API
│   └── test_daily_dd_worst_case.py # Drawdown calculation demo
├── scripts/                  # Utility scripts
│   ├── assess_scrape.py      # Scraping quality assessment
│   ├── validate_coverage.py  # Test coverage validation
│   └── run_all_tests.py      # Test runner
├── tests/                    # Test suite
├── run_mt5_api.py            # ⭐ MT5 REST API server launcher
├── setup_mt5_api.py          # ⭐ API setup script
└── docs/                     # Documentation
    ├── api/                  # ⭐ MT5 REST API documentation
    │   ├── MT5_REST_API.md          # Complete API reference
    │   ├── MT5_API_QUICKSTART.md    # Quick start guide
    │   ├── MT5_API_GETTING_STARTED.md # Beginner guide
    │   ├── MT5_API_IMPLEMENTATION.md # Technical details
    │   ├── MT5_API_ARCHITECTURE.md   # Architecture overview
    │   ├── MT5_API_FILE_INDEX.md     # Complete file index
    │   ├── MT5_API_QUICK_REFERENCE.md # Quick reference card
    │   └── MT5_API_SUMMARY.md        # Implementation summary
    ├── features/             # Feature documentation
    ├── guides/               # User guides
    ├── implementation/       # Implementation details
    └── integration/          # Integration guides
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/Ryko1141/Guardian.git
cd Guardian

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file with your credentials:

```env
# MT5 Configuration
MT5_ACCOUNT=12345678
MT5_PASSWORD=your_password
MT5_SERVER=YourBroker-Demo

# cTrader Configuration (optional)
CTRADER_CLIENT_ID=your_client_id
CTRADER_CLIENT_SECRET=your_client_secret
CTRADER_ACCESS_TOKEN=your_access_token

# LLM API (for rule extraction)
OPENAI_API_KEY=your_openai_key
```

Create `accounts.json` for multi-account monitoring:

```json
{
  "accounts": [
    {
      "label": "FTMO Challenge 100k",
      "firm": "FTMO",
      "platform": "mt5",
      "account_id": "12345678",
      "starting_balance": 100000.0,
      "check_interval": 60,
      "enabled": true,
      "rules": {
        "name": "FTMO",
        "max_daily_drawdown_pct": 5.0,
        "max_total_drawdown_pct": 10.0,
        "max_risk_per_trade_pct": 1.0,
        "max_open_lots": 20.0,
        "max_positions": 10
      }
    }
  ]
}
```

### 3. Run Monitoring

```bash
# Single account monitoring
python -m src.runner

# Multi-account monitoring
python -m src.multi_runner

# Async multi-account monitoring (recommended for >3 accounts)
python -m src.async_runner
```

### 4. MT5 REST API (Optional) ⭐ NEW

Start the REST API server to allow remote access to MT5 accounts:

```bash
# Start the API server
python run_mt5_api.py
```

The server starts on `http://localhost:8000` with:
- Interactive documentation at `/docs`
- Alternative docs at `/redoc`
- Full authentication and session management

**Quick test with Python:**
```python
from examples.api.test_mt5_api import MT5ApiClient

client = MT5ApiClient()
client.login(account_number=12345678, password="your_password", server="YourBroker-Demo")
account = client.get_account_info()
print(f"Balance: ${account['balance']:,.2f}")
client.logout()
```

**Or use the web interface:**
- Open `examples/api/mt5_api_client.html` in your browser
- Enter MT5 credentials and start monitoring

📖 **Full API Documentation:** See `docs/api/MT5_REST_API.md` and `docs/api/MT5_API_QUICKSTART.md`

### 5. Launch the Compliance Review API

Use Guardian's rule engine as a backend service to accept user-provided account data, review live prop compliance, and surface soft-rule insights from the rules database.

```bash
# Start the Compliance API (port 8010 by default)
python -m src.compliance_api

# Or with auto-reload during development
uvicorn src.compliance_api:app --host 0.0.0.0 --port 8010 --reload
```

Example compliance review request:

```bash
curl -X POST "http://localhost:8010/compliance/review" \
  -H "Content-Type: application/json" \
  -d '{
        "firm": "FundedNext",
        "program_id": "stellar_1step",
        "account_id": "demo-001",
        "account": {
          "balance": 100000,
          "equity": 98500,
          "starting_balance": 100000,
          "day_start_balance": 100000,
          "day_start_equity": 100000,
          "margin_used": 5000,
          "margin_available": 15000,
          "positions": []
        },
        "include_soft_rules": true
      }'
```

The response summarizes hard breaches, warnings, and soft-rule guidance pulled from the latest database contents.

### 6. Scrape and Extract Rules

```bash
# Scrape a prop firm help center
python -m src.propfirm_scraper.scraper "https://help.fundednext.com" --max-pages 100

# Extract rules with hybrid approach (pattern + LLM)
python -m src.propfirm_scraper.hybrid_extractor output/scraped_pages.json

# Ingest into database
python database/ingest_documents.py

# Query extracted rules
python database/query_rules.py --firm "FundedNext" --program "stellar_1step"
```

## 📊 Features in Detail

### Daily Drawdown Calculation ("Whichever is Higher" Rule)

Guardian implements the industry-standard worst-case daily drawdown calculation:

```python
# Uses WORST CASE between:
# 1. Loss from day start balance (realized losses)
# 2. Loss from day start equity (floating losses)

day_start_anchor = max(day_start_balance, day_start_equity)
daily_loss_by_balance = day_start_anchor - current_balance
daily_loss_by_equity = day_start_anchor - current_equity
daily_loss = max(daily_loss_by_balance, daily_loss_by_equity)
daily_drawdown_pct = (daily_loss / day_start_anchor) * 100
```

This prevents traders from "hiding" floating losses and ensures accurate risk tracking.

### Rule Storage and Versioning

Guardian maintains a normalized SQLite database with:
- **Firm profiles** - Prop firm metadata
- **Help documents** - Versioned help center content with change detection
- **Structured rules** - Extracted rules with confidence scores
- **Program taxonomy** - Challenge type mappings (e.g., "Stellar" → "stellar_1step")

### Extensible Notification System

```python
from src.notifier import notify_console

# Current: Console notifications
notify_console("FTMO-12345", breaches)

# Future: Add your own channels
# notify_telegram(account_label, breaches, bot_token, chat_id)
# notify_discord_webhook(account_label, breaches, webhook_url)
# notify_email(account_label, breaches, to_email, smtp_config)
```

## 🧪 Testing

```bash
# Run all tests
python scripts/run_all_tests.py

# Test rules without live connection
python examples/test_rules_offline.py

# Test MT5 connection
python examples/test_mt5.py

# Test drawdown calculation edge cases
python examples/test_daily_dd_worst_case.py
```

## 📚 Documentation

Comprehensive documentation is available in the `docs/` directory:

- **Integration Guides** - Platform setup and integration
- **Implementation Details** - Technical architecture
- **Feature Documentation** - Detailed feature explanations
- **User Guides** - How-to guides and tutorials
- **Reference Documentation** - API references

## 🛠️ Supported Platforms

- ✅ **MetaTrader 5** (Full support)
- ✅ **cTrader** (Full support via Open API)
- 🔄 **MT4** (Planned)

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](docs/guides/CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

## ⚠️ Disclaimer

**Guardian is a monitoring and alerting tool, not financial advice.** 

- This software does NOT place trades automatically
- You are responsible for your trading decisions
- Always understand your prop firm's rules completely
- Test thoroughly with demo accounts before using with funded accounts
- Use at your own risk

## 🙏 Acknowledgments

Built for the prop trading community. Stay disciplined, stay funded.

---

**Guardian** - Your partner in prop firm compliance.
