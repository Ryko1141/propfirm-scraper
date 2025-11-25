"""
Migration test: Ensure all existing rules have valid program_id

Verifies that after migration, all rules in the database have a valid program_id
"""
import sys
from pathlib import Path
import sqlite3

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.taxonomy_validator import TaxonomyValidator


def test_database_rules_migration():
    """Test that all database rules have valid program_ids"""
    
    print("\n" + "="*70)
    print("MIGRATION TEST: Verify All Rules Have Valid program_id")
    print("="*70)
    
    # Database path
    db_path = Path(__file__).parent.parent / "database" / "propfirm_scraper.db"
    
    if not db_path.exists():
        print("\n⚠️  Database not found at:", db_path)
        print("   Skipping migration test (database needs to be populated)")
        return True
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get validator
    validator = TaxonomyValidator()
    
    # Query all firms
    cursor.execute("SELECT id, name FROM prop_firm")
    firms = cursor.fetchall()
    
    if not firms:
        print("\n⚠️  No firms found in database")
        print("   Skipping migration test (database needs to be populated)")
        conn.close()
        return True
    
    print(f"\nFound {len(firms)} firm(s) in database\n")
    
    total_rules = 0
    valid_rules = 0
    invalid_rules = 0
    missing_program_id = 0
    invalid_program_ids = []
    
    # Check each firm
    for firm_row in firms:
        firm_id = firm_row['id']
        firm_name = firm_row['name']
        
        print(f"Checking firm: {firm_name}")
        print("-" * 70)
        
        # Query rules for this firm
        cursor.execute("""
            SELECT 
                id,
                rule_type,
                challenge_type,
                value
            FROM firm_rule
            WHERE firm_id = ?
        """, (firm_id,))
        
        rules = cursor.fetchall()
        
        if not rules:
            print(f"  No rules found for {firm_name}\n")
            continue
        
        print(f"  Found {len(rules)} rule(s)")
        
        # Check each rule
        for rule in rules:
            total_rules += 1
            rule_id = rule['id']
            challenge_type = rule['challenge_type']
            rule_type = rule['rule_type']
            
            # Check if challenge_type (program_id) exists
            if not challenge_type:
                missing_program_id += 1
                print(f"  ✗ Rule ID {rule_id} ({rule_type}): Missing challenge_type/program_id")
                invalid_program_ids.append({
                    'firm': firm_name,
                    'rule_id': rule_id,
                    'rule_type': rule_type,
                    'program_id': None,
                    'reason': 'Missing challenge_type'
                })
                continue
            
            # Validate program_id against taxonomy
            is_valid = validator.validate_program_id(firm_name, challenge_type)
            
            if is_valid:
                valid_rules += 1
                print(f"  ✓ Rule ID {rule_id} ({rule_type}): '{challenge_type}' is valid")
            else:
                invalid_rules += 1
                print(f"  ✗ Rule ID {rule_id} ({rule_type}): '{challenge_type}' is INVALID")
                invalid_program_ids.append({
                    'firm': firm_name,
                    'rule_id': rule_id,
                    'rule_type': rule_type,
                    'program_id': challenge_type,
                    'reason': 'Not in taxonomy'
                })
        
        print()
    
    conn.close()
    
    # Print summary
    print("="*70)
    print("MIGRATION TEST SUMMARY")
    print("="*70)
    print(f"Total rules checked: {total_rules}")
    print(f"Valid program_ids: {valid_rules}")
    print(f"Invalid program_ids: {invalid_rules}")
    print(f"Missing program_ids: {missing_program_id}")
    print()
    
    # Show invalid rules
    if invalid_program_ids:
        print("⚠️  INVALID RULES FOUND:")
        print("-" * 70)
        for invalid in invalid_program_ids:
            print(f"  Firm: {invalid['firm']}")
            print(f"  Rule ID: {invalid['rule_id']}")
            print(f"  Rule Type: {invalid['rule_type']}")
            print(f"  Program ID: {invalid['program_id']}")
            print(f"  Reason: {invalid['reason']}")
            print()
        
        print("ACTION REQUIRED:")
        print("1. Update taxonomy in config/program_taxonomy.json")
        print("2. Or correct challenge_type in database")
        print("3. Or remove invalid rules")
        print()
        
        return False
    else:
        print("✅ All rules have valid program_ids!")
        print("\nMigration test: PASSED")
        return True


def test_database_program_coverage():
    """Test that database covers all taxonomy programs"""
    
    print("\n" + "="*70)
    print("COVERAGE TEST: Verify Taxonomy Programs in Database")
    print("="*70)
    
    # Database path
    db_path = Path(__file__).parent.parent / "database" / "propfirm_scraper.db"
    
    if not db_path.exists():
        print("\n⚠️  Database not found")
        print("   Skipping coverage test")
        return True
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get validator
    validator = TaxonomyValidator()
    
    # Query firms
    cursor.execute("SELECT id, name FROM prop_firm")
    firms = cursor.fetchall()
    
    if not firms:
        print("\n⚠️  No firms found")
        conn.close()
        return True
    
    for firm_row in firms:
        firm_id = firm_row['id']
        firm_name = firm_row['name']
        
        # Get all valid programs for this firm
        valid_programs = validator.get_all_valid_programs(firm_name)
        
        if not valid_programs:
            print(f"\n{firm_name}: No programs in taxonomy")
            continue
        
        print(f"\n{firm_name}:")
        print("-" * 70)
        print(f"Programs in taxonomy: {len(valid_programs)}")
        
        # Check which programs have rules in database
        programs_with_rules = []
        programs_without_rules = []
        
        for program_id in valid_programs:
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM firm_rule
                WHERE firm_id = ? AND challenge_type = ?
            """, (firm_id, program_id))
            
            count = cursor.fetchone()['count']
            
            if count > 0:
                programs_with_rules.append((program_id, count))
                print(f"  ✓ {program_id}: {count} rule(s)")
            else:
                programs_without_rules.append(program_id)
                print(f"  ✗ {program_id}: No rules found")
        
        print()
        print(f"Coverage: {len(programs_with_rules)}/{len(valid_programs)} programs have rules")
        
        if programs_without_rules:
            print(f"\nMissing rules for:")
            for program_id in programs_without_rules:
                print(f"  - {program_id}")
    
    conn.close()
    
    print("\n" + "="*70)
    print("Coverage test: COMPLETED")
    return True


def main():
    """Run migration tests"""
    print("\n🧪 Running Migration Tests")
    
    results = []
    
    # Test 1: Validate all rules have valid program_ids
    try:
        result1 = test_database_rules_migration()
        results.append(("Rule Migration", result1))
    except Exception as e:
        print(f"\n✗ Migration test failed with error: {e}")
        results.append(("Rule Migration", False))
    
    # Test 2: Check coverage
    try:
        result2 = test_database_program_coverage()
        results.append(("Program Coverage", result2))
    except Exception as e:
        print(f"\n✗ Coverage test failed with error: {e}")
        results.append(("Program Coverage", False))
    
    # Summary
    print("\n" + "="*70)
    print("MIGRATION TEST RESULTS")
    print("="*70)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print()
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("✅ All migration tests passed!")
        return 0
    else:
        print("❌ Some migration tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
