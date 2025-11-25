"""
Reorganize files into cleaner folder structure
"""
import os
import shutil
from pathlib import Path

# Define base directory
base_dir = Path(__file__).parent

# Create docs folder structure
docs_structure = {
    'docs/integration': [
        'COMPLETE_INTEGRATION.md',
        'INTEGRATION_SUMMARY.md',
        'RISK_MONITOR_INTEGRATION.md'
    ],
    'docs/implementation': [
        'IMPLEMENTATION.md',
        'DATABASE_ARCHITECTURE.md',
        'DATABASE_COMPLETE.md',
        'TAXONOMY_INTEGRATION_COMPLETE.md'
    ],
    'docs/features': [
        'LLM_GUARDRAILS.md',
        'MAX_DAILY_DD_RULE.md',
        'NOTIFIER_REFACTOR.md',
        'PROP_RULES.md'
    ],
    'docs/summaries': [
        'LLM_GUARDRAILS_SUMMARY.md',
        'PIPELINE_UPDATE_SUMMARY.md',
        'QA_TESTING_SUMMARY.md',
        'PROJECT_STATUS.md'
    ],
    'docs/guides': [
        'TESTING_GUIDE.md',
        'CONTRIBUTING.md'
    ],
    'docs/references': [
        'PLATFORM_COMPARISON.md'
    ]
}

# Files to move to scripts folder
scripts_files = [
    'assess_scrape.py',
    'rescrape_missing.py',
    'validate_coverage.py',
    'run_all_tests.py'
]

# Files to move to tests folder
test_files = [
    'test_integration.py'
]

def move_file(src, dest_dir, filename):
    """Move file from src to dest_dir"""
    src_path = base_dir / filename
    dest_path = base_dir / dest_dir / filename
    
    if src_path.exists():
        # Create destination directory if it doesn't exist
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Move file
        shutil.move(str(src_path), str(dest_path))
        print(f"✓ Moved {filename} -> {dest_dir}/")
        return True
    else:
        print(f"✗ File not found: {filename}")
        return False

def main():
    print("\n" + "="*70)
    print("REORGANIZING FILES INTO CLEANER STRUCTURE")
    print("="*70)
    
    moved_count = 0
    failed_count = 0
    
    # 1. Move documentation files
    print("\n📁 Moving documentation files...")
    print("-" * 70)
    for folder, files in docs_structure.items():
        for file in files:
            if move_file('.', folder, file):
                moved_count += 1
            else:
                failed_count += 1
    
    # 2. Move script files
    print("\n📁 Moving script files...")
    print("-" * 70)
    for file in scripts_files:
        if move_file('.', 'scripts', file):
            moved_count += 1
        else:
            failed_count += 1
    
    # 3. Move test files
    print("\n📁 Moving test files...")
    print("-" * 70)
    for file in test_files:
        if move_file('.', 'tests', file):
            moved_count += 1
        else:
            failed_count += 1
    
    # Summary
    print("\n" + "="*70)
    print("REORGANIZATION COMPLETE")
    print("="*70)
    print(f"✓ Moved: {moved_count} files")
    print(f"✗ Failed: {failed_count} files")
    
    print("\n📂 New Structure:")
    print("  propfirm-scraper/")
    print("  ├── docs/")
    print("  │   ├── integration/      (integration guides)")
    print("  │   ├── implementation/   (technical details)")
    print("  │   ├── features/         (feature documentation)")
    print("  │   ├── summaries/        (project summaries)")
    print("  │   ├── guides/           (user guides)")
    print("  │   └── references/       (reference docs)")
    print("  ├── tests/                (all test files)")
    print("  ├── scripts/              (utility scripts)")
    print("  ├── config/")
    print("  ├── database/")
    print("  ├── examples/")
    print("  ├── output/")
    print("  └── src/")
    
    print("\n✨ Root directory is now much cleaner!")
    print("\nNote: Update any import paths if needed.")
    print("\nTo revert, run: git checkout -- <filename>")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
