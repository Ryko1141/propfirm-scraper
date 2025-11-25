"""
Execute file reorganization immediately
"""
import os
import shutil
from pathlib import Path

# Define base directory
base_dir = Path(r"C:\Users\sossi\OneDrive - University of Reading\Documents\GitHub\propfirm-scraper")
os.chdir(base_dir)

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

def move_file(dest_dir, filename):
    """Move file from root to dest_dir"""
    src_path = base_dir / filename
    dest_path = base_dir / dest_dir / filename
    
    if src_path.exists() and src_path.is_file():
        # Create destination directory if it doesn't exist
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Move file
        try:
            shutil.move(str(src_path), str(dest_path))
            print(f"✓ Moved {filename} -> {dest_dir}/")
            return True
        except Exception as e:
            print(f"✗ Error moving {filename}: {e}")
            return False
    else:
        print(f"⊘ File not found: {filename}")
        return False

def main():
    print("\n" + "="*70)
    print("REORGANIZING FILES INTO CLEANER STRUCTURE")
    print("="*70)
    print(f"Working directory: {base_dir}")
    
    moved_count = 0
    failed_count = 0
    notfound_count = 0
    
    # 1. Move documentation files
    print("\n📁 Moving documentation files...")
    print("-" * 70)
    for folder, files in docs_structure.items():
        for file in files:
            result = move_file(folder, file)
            if result:
                moved_count += 1
            elif (base_dir / file).exists():
                failed_count += 1
            else:
                notfound_count += 1
    
    # 2. Move script files
    print("\n📁 Moving script files...")
    print("-" * 70)
    for file in scripts_files:
        result = move_file('scripts', file)
        if result:
            moved_count += 1
        elif (base_dir / file).exists():
            failed_count += 1
        else:
            notfound_count += 1
    
    # 3. Move test files
    print("\n📁 Moving test files...")
    print("-" * 70)
    for file in test_files:
        result = move_file('tests', file)
        if result:
            moved_count += 1
        elif (base_dir / file).exists():
            failed_count += 1
        else:
            notfound_count += 1
    
    # Summary
    print("\n" + "="*70)
    print("REORGANIZATION COMPLETE")
    print("="*70)
    print(f"✓ Successfully moved: {moved_count} files")
    print(f"✗ Failed to move: {failed_count} files")
    print(f"⊘ Not found (already moved?): {notfound_count} files")
    
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
    
    if moved_count > 0:
        print("\n📝 Next Steps:")
        print("  1. Verify files are in correct locations")
        print("  2. Test: python scripts\\run_all_tests.py")
        print("  3. Git commit:")
        print("     git add .")
        print('     git commit -m "Reorganize docs and scripts into folders"')
        print("     git push origin main")
    
    print("\nDone! 🎉")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
