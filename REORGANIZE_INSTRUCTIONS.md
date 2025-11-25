# File Reorganization Instructions

## 🎯 Goal
Reorganize scattered documentation files into a clean, organized structure.

## 📋 Steps to Reorganize

### Option 1: Run the Batch Script (Easiest)

Simply double-click or run from command prompt:

```cmd
reorganize_files.bat
```

This will automatically:
- Create the `docs/` folder structure
- Move all documentation files to appropriate locations
- Move utility scripts to `scripts/`
- Move test files to `tests/`
- Show a summary of what was moved

### Option 2: Run the Python Script

```cmd
python reorganize_files.py
```

This provides more detailed output and error checking.

### Option 3: Manual Reorganization

If you prefer to do it manually, follow this structure:

```
Create folders:
- mkdir docs\integration
- mkdir docs\implementation
- mkdir docs\features
- mkdir docs\summaries
- mkdir docs\guides
- mkdir docs\references

Move files:
docs\integration\
  - COMPLETE_INTEGRATION.md
  - INTEGRATION_SUMMARY.md
  - RISK_MONITOR_INTEGRATION.md

docs\implementation\
  - IMPLEMENTATION.md
  - DATABASE_ARCHITECTURE.md
  - DATABASE_COMPLETE.md
  - TAXONOMY_INTEGRATION_COMPLETE.md

docs\features\
  - LLM_GUARDRAILS.md
  - MAX_DAILY_DD_RULE.md
  - NOTIFIER_REFACTOR.md
  - PROP_RULES.md

docs\summaries\
  - LLM_GUARDRAILS_SUMMARY.md
  - PIPELINE_UPDATE_SUMMARY.md
  - QA_TESTING_SUMMARY.md
  - PROJECT_STATUS.md

docs\guides\
  - TESTING_GUIDE.md
  - CONTRIBUTING.md

docs\references\
  - PLATFORM_COMPARISON.md

scripts\
  - assess_scrape.py
  - rescrape_missing.py
  - validate_coverage.py
  - run_all_tests.py

tests\
  - test_integration.py (from root)
```

## ✅ After Reorganization

### 1. Verify Structure

The root directory should now be much cleaner:
```
propfirm-scraper/
├── README.md
├── LICENSE
├── requirements.txt
├── .env.example
├── .gitignore
├── accounts.json.example
├── docs/               ← NEW! All documentation here
├── tests/              ← All tests together
├── scripts/            ← All utility scripts together
├── config/
├── database/
├── examples/
├── output/
└── src/
```

### 2. Update Import Paths

If any Python files import from relocated files, update paths:

```python
# Old
from run_all_tests import something

# New
from scripts.run_all_tests import something
```

### 3. Test Everything Still Works

```cmd
# Run tests
python scripts\run_all_tests.py

# Or individual tests
python tests\test_program_taxonomy.py
python tests\test_migration.py
python tests\test_risk_monitor.py
python tests\test_taxonomy_validation.py
python tests\test_integration.py
```

### 4. Update Git

```cmd
# Stage all changes
git add .

# Check what's being committed
git status

# Commit
git commit -m "Reorganize documentation and scripts into cleaner folder structure

- Created docs/ folder with organized subfolders
- Moved all documentation to docs/ (integration, features, implementation, etc.)
- Moved utility scripts to scripts/
- Consolidated all tests in tests/
- Updated README.md with new paths
- Root directory now much cleaner and easier to navigate"

# Push
git push origin main
```

## 📂 New Documentation Structure

```
docs/
├── README.md              ← Documentation index (NEW!)
├── integration/           ← Integration guides
│   ├── COMPLETE_INTEGRATION.md
│   ├── INTEGRATION_SUMMARY.md
│   └── RISK_MONITOR_INTEGRATION.md
├── implementation/        ← Technical details
│   ├── DATABASE_ARCHITECTURE.md
│   ├── DATABASE_COMPLETE.md
│   ├── IMPLEMENTATION.md
│   └── TAXONOMY_INTEGRATION_COMPLETE.md
├── features/             ← Feature docs
│   ├── LLM_GUARDRAILS.md
│   ├── MAX_DAILY_DD_RULE.md
│   ├── NOTIFIER_REFACTOR.md
│   └── PROP_RULES.md
├── summaries/            ← Project summaries
│   ├── LLM_GUARDRAILS_SUMMARY.md
│   ├── PIPELINE_UPDATE_SUMMARY.md
│   ├── QA_TESTING_SUMMARY.md
│   └── PROJECT_STATUS.md
├── guides/               ← User guides
│   ├── TESTING_GUIDE.md
│   └── CONTRIBUTING.md
└── references/           ← Reference docs
    └── PLATFORM_COMPARISON.md
```

## 🎉 Benefits

After reorganization:

✅ **Cleaner Root Directory**
- Only essential files (README, LICENSE, configs) in root
- Easy to find what you need

✅ **Organized Documentation**
- Logical grouping by purpose
- Easy to navigate
- Clear documentation index

✅ **Better Maintenance**
- Easy to add new docs
- Clear where things belong
- Consistent structure

✅ **Professional Structure**
- Industry-standard organization
- Easy for new contributors
- Better for open source

## 🔧 Troubleshooting

**Files not moving?**
- Make sure you're in the project root directory
- Check if files exist before running script
- Run with administrator privileges if needed

**Git shows too many changes?**
- This is normal! Git tracks the file moves
- Use `git status` to see what changed
- Commit message explains the reorganization

**Tests failing?**
- Check if import paths need updating
- Verify files are in correct locations
- Run from project root: `python scripts\run_all_tests.py`

**Need to revert?**
- Before committing: `git checkout -- .`
- After committing: `git revert <commit-hash>`

## 📞 Need Help?

If something doesn't work:
1. Check this file for troubleshooting
2. Verify file paths in the script
3. Try manual reorganization (Option 3)
4. Check README.md for updated paths

---

**Ready to reorganize?** Run `reorganize_files.bat` and enjoy your clean structure! 🚀
