# PropFirm Scraper

Tools for crawling prop-firm help centers and extracting their trading rules. The project includes a Playwright-based scraper, fast regex extractors, and LLM-assisted extraction for filling gaps. Examples and helper scripts are organized so you can experiment quickly or plug the components into your own workflow.

## Project layout
- `src/propfirm_scraper/` – core scraper and extraction modules.
- `examples/` – runnable examples and sample output (`example_output.json`).
- `scripts/` – utility scripts such as scrape quality assessment.
- `requirements.txt` – Python dependencies for scraping and extraction.

## Quickstart
1. Install dependencies (preferably in a virtual environment):
   ```bash
   pip install -r requirements.txt
   ```
2. Add the source tree to `PYTHONPATH` so the package is importable:
   ```bash
   export PYTHONPATH="$(pwd)/src"
   ```
3. Run the end-to-end example from the repository root:
   ```bash
   python examples/usage_example.py
   ```

## Running individual components
- Crawl a site and save HTML content:
  ```bash
  python -m propfirm_scraper.scraper "https://help.example.com" --max-pages 100
  ```
- Fast pattern-only extraction on scraped data:
  ```bash
  python -m propfirm_scraper.fast_extractor output/scraped_pages.json
  ```
- Hybrid extraction (patterns + LLM for gaps):
  ```bash
  python -m propfirm_scraper.hybrid_extractor output/scraped_pages.json
  ```
- Full LLM extraction:
  ```bash
  python -m propfirm_scraper.llm_extractor output/scraped_pages.json
  ```

The output directory is created automatically when you run the scripts, and extracted rules are written as JSON for downstream analysis.

## Sample output structure
Extracted rules resemble the following JSON format:

```json
{
  "firm_name": "FundedNext",
  "general_rules": {
    "prohibited_strategies": ["copy trading", "martingale"],
    "payout_rules": {}
  },
  "challenge_types": {
    "stellar_1_step": {
      "daily_loss_limit": "3",
      "max_drawdown": "6",
      "profit_targets": ["10"],
      "account_sizes": ["50000", "100000"]
    }
  }
}
```

For additional ideas, see `examples/usage_example.py` for a guided walkthrough and `scripts/assess_scrape.py` for assessing scrape coverage and quality.
