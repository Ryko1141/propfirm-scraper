# Contributing to PropFirm Scraper

Thank you for considering contributing! This project welcomes contributions of all kinds.

## How to Contribute

### Reporting Bugs

- Use the GitHub Issues tab
- Include detailed steps to reproduce
- Provide error messages and logs
- Specify your Python version and OS

### Suggesting Features

- Open an issue with the `enhancement` label
- Describe the feature and use case
- Explain why it would be useful

### Submitting Pull Requests

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Code Guidelines

- Follow PEP 8 style guide
- Add docstrings to functions and classes
- Include type hints where possible
- Write descriptive commit messages
- Test your changes thoroughly

### Adding New Prop Firms

To add support for a new prop firm:

1. Test the scraper on the firm's help center
2. Add firm-specific patterns to `config/patterns.py` if needed
3. Create an example output in `output/` directory
4. Update `README.md` with the new firm name

### Testing

Before submitting a PR:

```bash
# Test scraper on a small number of pages
python src/scraper.py https://example.com/help --max-pages 5

# Test fast extraction
python src/fast_extractor.py output/scraped_pages.json

# Verify output format matches template
python -m json.tool output/rules_fast.json
```

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/propfirm-scraper.git
cd propfirm-scraper

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Install Ollama for LLM features
# Download from https://ollama.ai
```

## Project Structure

- `src/` - Core scraper and extraction modules
- `config/` - Templates and regex patterns
- `output/` - Scraped data and extracted rules
- `examples/` - Usage examples

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Maintain professional communication

## Questions?

Open an issue or reach out to the maintainers. We're happy to help!

---

Thank you for contributing! 🎉
