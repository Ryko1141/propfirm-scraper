# PropFirm Scraper - Examples

This directory contains usage examples for the propfirm scraper.

## Files

- **usage_example.py** - Complete examples showing all extraction methods

## Running Examples

```bash
# Full scrape and extraction
python examples/usage_example.py

# Fast extraction only (using existing scraped data)
python src/fast_extractor.py output/scraped_pages.json

# Hybrid extraction (patterns + LLM for gaps)
python src/hybrid_extractor.py output/scraped_pages.json

# Full LLM extraction
python src/llm_extractor.py output/scraped_pages.json
```

## Example Output

Extracted rules are saved as JSON in the `output/` directory with this structure:

```json
{
  "firm_name": "FundedNext",
  "general_rules": {
    "prohibited_strategies": [...]
  },
  "challenge_types": {
    "stellar_1_step": {
      "daily_loss_limit": "3",
      "max_drawdown": "6",
      ...
    }
  }
}
```
