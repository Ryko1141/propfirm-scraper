"""
Master test runner for complete QA testing

Runs all integration, validation, migration, and risk monitor tests
"""
import sys
import subprocess
from pathlib import Path


def run_test(test_file, description):
    """Run a test file and return result"""
    print(f"\n{'='*70}")
    print(f"Running: {description}")
    print(f"{'='*70}")
    
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=False,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        return result.returncode == 0
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        return False


def main():
    """Run all QA tests"""
    print("\n" + "="*70)
    print("🧪 COMPLETE QA TEST SUITE")
    print("="*70)
    print("\nRunning comprehensive tests for PropFirm Scraper + Risk Monitor")
    print("This includes:")
    print("  • Unit tests for taxonomy validation")
    print("  • Migration tests for database integrity")
    print("  • Integration tests for system components")
    print("  • Risk monitor simulation tests")
    
    results = []
    
    # Test 1: Program Taxonomy Unit Tests
    print("\n" + "="*70)
    print("TEST SUITE 1: Program Taxonomy (Unit Tests)")
    print("="*70)
    print("Purpose: Verify map_alias_to_program resolves correct names and rejects unknowns")
    
    result1 = run_test(
        "tests/test_program_taxonomy.py",
        "Program Taxonomy Unit Tests"
    )
    results.append(("Program Taxonomy Tests", result1))
    
    # Test 2: Migration Tests
    print("\n" + "="*70)
    print("TEST SUITE 2: Database Migration")
    print("="*70)
    print("Purpose: Ensure all existing rules have valid program_id after migration")
    
    result2 = run_test(
        "tests/test_migration.py",
        "Database Migration Tests"
    )
    results.append(("Migration Tests", result2))
    
    # Test 3: Integration Tests
    print("\n" + "="*70)
    print("TEST SUITE 3: System Integration")
    print("="*70)
    print("Purpose: Verify database rule loading and configuration")
    
    result3 = run_test(
        "test_integration.py",
        "Integration Tests"
    )
    results.append(("Integration Tests", result3))
    
    # Test 4: Risk Monitor Tests
    print("\n" + "="*70)
    print("TEST SUITE 4: Risk Monitor Simulation")
    print("="*70)
    print("Purpose: Simulate FundedNext accounts and confirm correct rule loading")
    
    result4 = run_test(
        "tests/test_risk_monitor.py",
        "Risk Monitor Simulation Tests"
    )
    results.append(("Risk Monitor Tests", result4))
    
    # Test 5: LLM Validation Tests (if not already run in taxonomy)
    print("\n" + "="*70)
    print("TEST SUITE 5: LLM Guardrails")
    print("="*70)
    print("Purpose: Verify hallucination detection and validation reporting")
    
    result5 = run_test(
        "tests/test_taxonomy_validation.py",
        "LLM Guardrails Tests"
    )
    results.append(("LLM Guardrails Tests", result5))
    
    # Final Summary
    print("\n" + "="*70)
    print("🎯 FINAL QA TEST RESULTS")
    print("="*70)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print("\n" + "="*70)
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("\n🎉 System is ready for production:")
        print("  • Taxonomy validation working correctly")
        print("  • Database migration complete and valid")
        print("  • Integration points functioning")
        print("  • Risk monitor loading program-specific rules")
        print("  • LLM guardrails preventing hallucinations")
        
        print("\n📋 Next Steps:")
        print("  1. Deploy to production environment")
        print("  2. Configure accounts with program_id")
        print("  3. Monitor hallucination rates")
        print("  4. Validate against live trading rules")
        
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("\n⚠️  Action Required:")
        print("  1. Review failed test output above")
        print("  2. Fix issues in code or configuration")
        print("  3. Re-run: python run_all_tests.py")
        print("  4. Ensure all tests pass before production")
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
