# Propfirm Scraper Configuration

This directory contains configuration files for the propfirm scraper.

## Files

- **template.py**: Universal structure for extracted prop firm rules
- **patterns.py**: Regex patterns for rule extraction

## Usage

Import templates and patterns in your extraction scripts:

```python
from config.template import UNIVERSAL_TEMPLATE, create_challenge_template
from config.patterns import PROFIT_TARGET_PATTERNS, PROHIBITED_STRATEGIES
```
