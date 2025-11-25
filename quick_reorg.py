import os
import shutil
from pathlib import Path

base = Path(r"C:\Users\sossi\OneDrive - University of Reading\Documents\GitHub\propfirm-scraper")

moves = {
    'docs/integration': ['COMPLETE_INTEGRATION.md', 'INTEGRATION_SUMMARY.md', 'RISK_MONITOR_INTEGRATION.md'],
    'docs/implementation': ['IMPLEMENTATION.md', 'DATABASE_ARCHITECTURE.md', 'DATABASE_COMPLETE.md', 'TAXONOMY_INTEGRATION_COMPLETE.md'],
    'docs/features': ['LLM_GUARDRAILS.md', 'MAX_DAILY_DD_RULE.md', 'NOTIFIER_REFACTOR.md', 'PROP_RULES.md'],
    'docs/summaries': ['LLM_GUARDRAILS_SUMMARY.md', 'PIPELINE_UPDATE_SUMMARY.md', 'QA_TESTING_SUMMARY.md', 'PROJECT_STATUS.md'],
    'docs/guides': ['TESTING_GUIDE.md', 'CONTRIBUTING.md'],
    'docs/references': ['PLATFORM_COMPARISON.md'],
    'scripts': ['assess_scrape.py', 'rescrape_missing.py', 'validate_coverage.py', 'run_all_tests.py'],
    'tests': ['test_integration.py']
}

moved = 0
for dest, files in moves.items():
    (base / dest).mkdir(parents=True, exist_ok=True)
    for f in files:
        src = base / f
        dst = base / dest / f
        if src.exists() and src.is_file():
            shutil.move(str(src), str(dst))
            print(f"✓ {f} → {dest}/")
            moved += 1

print(f"\n✨ Done! Moved {moved} files")
print("\nNext: git add . && git commit -m 'Reorganize files' && git push")
