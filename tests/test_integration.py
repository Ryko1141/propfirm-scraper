"""
Test script for program_id-based rule loading integration

Tests the database lookup functionality without requiring API credentials
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import AccountManager, PropRules, AccountConfig


def test_database_lookup():
    """Test loading rules from database by program_id"""
    print("=" * 60)
    print("Testing Database Rule Lookup by program_id")
    print("=" * 60)
    
    manager = AccountManager()
    
    # Test 1: Load rules for FundedNext Stellar 1-Step
    print("\n1. Loading rules for FundedNext - stellar_1step...")
    rules = manager.get_rules_by_program_id("FundedNext", "stellar_1step")
    
    if rules:
        print(f"✓ Successfully loaded rules!")
        print(f"  Name: {rules.name}")
        print(f"  Program ID: {rules.program_id}")
        print(f"  Daily Drawdown Limit: {rules.max_daily_drawdown_pct}%")
        print(f"  Total Drawdown Limit: {rules.max_total_drawdown_pct}%")
        print(f"  Max Risk Per Trade: {rules.max_risk_per_trade_pct}%")
    else:
        print("✗ No rules found (database may not be populated yet)")
        print("  Tip: Run 'python database/ingest_documents.py' first")
    
    # Test 2: Load rules for different program
    print("\n2. Loading rules for FundedNext - stellar_2step...")
    rules2 = manager.get_rules_by_program_id("FundedNext", "stellar_2step")
    
    if rules2:
        print(f"✓ Successfully loaded rules!")
        print(f"  Name: {rules2.name}")
        print(f"  Program ID: {rules2.program_id}")
    else:
        print("✗ No rules found for stellar_2step")
    
    # Test 3: Fallback to predefined rules
    print("\n3. Testing fallback to predefined rules...")
    print("  Loading rules for non-existent program...")
    rules3 = manager.get_rules_by_program_id("FundedNext", "nonexistent_program")
    
    if rules3:
        print(f"  Loaded: {rules3.name}")
    else:
        print("  ✓ Correctly returned None (no fallback in get_rules_by_program_id)")


def test_account_creation():
    """Test creating account with program_id"""
    print("\n" + "=" * 60)
    print("Testing Account Creation with program_id")
    print("=" * 60)
    
    # Test with program_id
    print("\n1. Creating account with program_id...")
    account = AccountConfig(
        label="Test Account - Stellar 1-Step",
        firm="FundedNext",
        program_id="stellar_1step",
        platform="mt5",
        account_id="TEST123",
        starting_balance=100000.0,
        rules=PropRules(
            name="Test Rules",
            program_id="stellar_1step",
            max_daily_drawdown_pct=3.0,
            max_total_drawdown_pct=6.0,
            max_risk_per_trade_pct=1.0,
            max_open_lots=10.0,
            max_positions=5
        )
    )
    
    print(f"✓ Account created successfully!")
    print(f"  Label: {account.label}")
    print(f"  Firm: {account.firm}")
    print(f"  Program ID: {account.program_id}")
    print(f"  Rules: {account.rules.name}")
    print(f"  Rules Program ID: {account.rules.program_id}")


def test_json_loading():
    """Test loading account from JSON with program_id"""
    print("\n" + "=" * 60)
    print("Testing JSON Account Loading")
    print("=" * 60)
    
    import json
    import tempfile
    
    # Create test JSON
    test_config = {
        "accounts": [
            {
                "label": "Test - Stellar 1-Step",
                "firm": "FundedNext",
                "program_id": "stellar_1step",
                "platform": "mt5",
                "account_id": "TEST456",
                "starting_balance": 100000.0,
                "check_interval": 60,
                "enabled": True
            }
        ]
    }
    
    # Write to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_config, f)
        temp_path = f.name
    
    try:
        print(f"\n1. Loading accounts from JSON...")
        manager = AccountManager(config_file=temp_path)
        
        accounts = manager.get_enabled_accounts()
        print(f"✓ Loaded {len(accounts)} account(s)")
        
        for account in accounts:
            print(f"\n  Account: {account.label}")
            print(f"  Firm: {account.firm}")
            print(f"  Program ID: {account.program_id}")
            print(f"  Platform: {account.platform}")
            print(f"  Rules: {account.rules.name}")
            
    finally:
        # Cleanup
        Path(temp_path).unlink()


def main():
    """Run all tests"""
    print("\n🧪 PropFirm Scraper + Risk Monitor Integration Test")
    print("Testing program_id-based rule loading...\n")
    
    try:
        test_database_lookup()
        test_account_creation()
        test_json_loading()
        
        print("\n" + "=" * 60)
        print("✓ All tests completed!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Populate database: python database/ingest_documents.py")
        print("2. Configure account: Edit .env or accounts.json")
        print("3. Run monitor: python -m src.runner")
        print("\nFor more info, see RISK_MONITOR_INTEGRATION.md")
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
