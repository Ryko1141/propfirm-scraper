# PropFirm Scraper

🚀 **Universal web scraper for proprietary trading firm rules with Cloudflare bypass and AI-powered extraction**

Extract trading rules, drawdown limits, profit targets, and prohibited strategies from any prop firm's help center automatically.

## Features

- ✅ **Cloudflare Bypass** - Stealth browser automation with persistent sessions
- ✅ **Hybrid Extraction** - Fast pattern matching + LLM for complex rules
- ✅ **Universal Template** - Works with any prop firm (FundedNext, FTMO, MyForexFunds, etc.)
- ✅ **Challenge Type Detection** - Automatically groups rules by account type
- ✅ **Structured Output** - JSON format ready for databases or APIs

## Installation

### Prerequisites

- Python 3.10+
- Playwright
- Ollama (for LLM features)

### Setup

```bash
# Clone repository
git clone https://github.com/yourusername/propfirm-scraper.git
cd propfirm-scraper

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Install Ollama models (optional, for LLM extraction)
ollama pull qwen2.5-coder:14b
ollama pull qwen:latest
```

## Quick Start

### 1. Scrape a Prop Firm Website

```bash
python src/scraper.py
```

Enter the prop firm's help center URL (e.g., `https://help.fundednext.com/en`)

### 2. Extract Rules (Hybrid Mode)

```bash
python src/hybrid_extractor.py
```

Choose whether to use LLM for missing rules or pattern-only extraction.

### 3. View Results

Structured rules will be saved to `output/hybrid_rules.json`

## Usage Examples

### Scraping FundedNext

```bash
python src/scraper.py
# Enter: https://help.fundednext.com/en
```

### Pattern-Only Extraction (Fast)

```bash
python src/fast_extractor.py
```

### Full LLM Extraction (Most Accurate)

```bash
python src/llm_extractor.py
```

## Project Structure

```
propfirm-scraper/
├── src/
│   ├── scraper.py              # Main web scraper with Cloudflare bypass
│   ├── hybrid_extractor.py     # Hybrid pattern + LLM extraction
│   ├── fast_extractor.py       # Fast pattern-based extraction
│   ├── llm_extractor.py        # Full LLM-powered extraction
│   ├── extractors.py           # Extraction utilities
│   └── utils.py                # Helper functions
├── config/
│   ├── template.py             # Universal prop firm template
│   └── patterns.py             # Regex patterns for rule extraction
├── output/                     # Generated JSON files
├── requirements.txt            # Python dependencies
├── .gitignore
└── README.md
```

## Output Format

```json
{
  "firm_name": "FundedNext",
  "scraped_date": "2025-11-24T...",
  "general_rules": {
    "prohibited_strategies": ["copy trading", "HFT", "tick scalping"],
    "kyc_required": true,
    "payout_rules": {
      "frequency": "bi-weekly",
      "minimum_amount": "$100"
    }
  },
  "challenge_types": {
    "stellar_1_step": {
      "display_name": "Stellar 1-Step Challenge",
      "account_sizes": ["5000", "10000", "25000"],
      "phase_details": [{
        "profit_target": "10%",
        "daily_loss_limit": "5%",
        "max_drawdown": "10%"
      }],
      "funded_account_rules": {
        "profit_split": "90%"
      }
    }
  }
}
```

## Configuration

### Template Customization

Edit `config/template.py` to add/remove rule categories:

```python
UNIVERSAL_TEMPLATE = {
    "general_rules": {
        "prohibited_strategies": [],
        "your_custom_field": []
    }
}
```

### Pattern Customization

Edit `config/patterns.py` to adjust extraction patterns:

```python
PROHIBITED_STRATEGIES = [
    'copy trading',
    'your_custom_strategy'
]
```

## How It Works

1. **Web Scraping** - Playwright with stealth mode bypasses Cloudflare
2. **Pattern Extraction** - Regex patterns extract 90% of common rules instantly
3. **LLM Gap Filling** - Local LLM (Ollama) finds missing or unusual rules
4. **Structuring** - Rules organized by challenge type and general/specific categories

## Supported Prop Firms

- ✅ FundedNext
- ✅ FTMO (coming soon)
- ✅ MyForexFunds (coming soon)
- ✅ The5ers (coming soon)
- ✅ Any firm with structured help docs

## Troubleshooting

### Cloudflare Blocking

If Cloudflare blocks the scraper:
1. Browser will open - manually solve the challenge once
2. Session persists in `acg_profile/` folder
3. Subsequent runs will bypass Cloudflare automatically

### LLM Too Slow

Use fast-only mode:
```bash
python src/fast_extractor.py
```

### Missing Rules

Enable full LLM mode:
```bash
python src/llm_extractor.py
```

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License - see LICENSE file

## Disclaimer

This tool is for educational and research purposes. Always respect website terms of service and robots.txt. Use responsibly.

## Author

Created for prop traders who need structured, accurate rule data.

## Support

- Issues: [GitHub Issues](https://github.com/yourusername/propfirm-scraper/issues)
- Discussions: [GitHub Discussions](https://github.com/yourusername/propfirm-scraper/discussions)
