"""
Tests for taxonomy validation (LLM guardrails)
"""
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.taxonomy_validator import (
    TaxonomyValidator,
    map_alias_to_program,
    validate_llm_output
)


def test_valid_mappings():
    """Test that valid program names map correctly"""
    print("="*60)
    print("TEST 1: Valid Program Name Mappings")
    print("="*60)
    
    test_cases = [
        ("FundedNext", "stellar 1-step", "stellar_1step"),
        ("FundedNext", "Stellar 1-Step Challenge", "stellar_1step"),
        ("FundedNext", "stellar_1step", "stellar_1step"),
        ("FundedNext", "stellar 2-step", "stellar_2step"),
        ("FundedNext", "evaluation", "evaluation_2step"),
        ("FundedNext", "Evaluation Challenge", "evaluation_2step"),
        ("FundedNext", "stellar lite", "stellar_lite"),
        ("FundedNext", "lite", "stellar_lite"),
        ("FundedNext", "stellar instant", "stellar_instant"),
        ("FundedNext", "instant", "stellar_instant"),
    ]
    
    passed = 0
    failed = 0
    
    for firm, input_name, expected in test_cases:
        result = map_alias_to_program(firm, input_name.lower())
        
        if result == expected:
            print(f"✓ '{input_name}' → {result}")
            passed += 1
        else:
            print(f"✗ '{input_name}' → {result} (expected: {expected})")
            failed += 1
    
    print(f"\nResult: {passed} passed, {failed} failed\n")
    return failed == 0


def test_hallucination_detection():
    """Test that hallucinations are detected"""
    print("="*60)
    print("TEST 2: Hallucination Detection")
    print("="*60)
    
    # These should all return None (hallucinations)
    hallucinations = [
        "Stellar Instant 2-Step Challenge",  # Mixing two programs
        "Stellar Premium Challenge",          # Non-existent
        "Evaluation 1-Step",                  # Wrong step count
        "Stellar 3-Step Challenge",           # Wrong step count
        "Gold Challenge",                     # Completely wrong
        "Ultra Funding Program",              # Made up
        "Stellar Express Account",            # Non-existent variant
    ]
    
    detected = 0
    missed = 0
    
    for hallucination in hallucinations:
        result = map_alias_to_program("FundedNext", hallucination.lower())
        
        if result is None:
            print(f"✓ Detected hallucination: '{hallucination}'")
            detected += 1
        else:
            print(f"✗ Missed hallucination: '{hallucination}' → {result}")
            missed += 1
    
    print(f"\nResult: {detected} detected, {missed} missed\n")
    return missed == 0


def test_fuzzy_matching():
    """Test fuzzy matching for variations"""
    print("="*60)
    print("TEST 3: Fuzzy Matching")
    print("="*60)
    
    test_cases = [
        ("FundedNext", "stellar1step", "stellar_1step"),         # No spaces
        ("FundedNext", "2 step stellar", "stellar_2step"),        # Reversed order
        ("FundedNext", "evaluation 2 step", "evaluation_2step"),  # Variation
        ("FundedNext", "stellar-lite", "stellar_lite"),           # Hyphenated
        ("FundedNext", "stellarlite", "stellar_lite"),            # Concatenated
    ]
    
    passed = 0
    failed = 0
    
    for firm, input_name, expected in test_cases:
        result = map_alias_to_program(firm, input_name.lower())
        
        if result == expected:
            print(f"✓ Fuzzy matched: '{input_name}' → {result}")
            passed += 1
        else:
            print(f"✗ Failed to match: '{input_name}' → {result} (expected: {expected})")
            failed += 1
    
    print(f"\nResult: {passed} passed, {failed} failed\n")
    return failed == 0


def test_llm_validation():
    """Test full LLM output validation"""
    print("="*60)
    print("TEST 4: LLM Output Validation")
    print("="*60)
    
    # Valid outputs
    valid_outputs = [
        "Stellar 1-Step Challenge",
        "The Stellar 2-Step",
        "Evaluation Challenge (2-Step)",
        "Stellar Lite Account",
    ]
    
    print("Valid outputs:")
    for output in valid_outputs:
        program_id, is_valid, error = validate_llm_output("FundedNext", output)
        status = "✓" if is_valid else "✗"
        print(f"{status} '{output}' → {program_id}")
    
    print()
    
    # Invalid outputs (hallucinations)
    invalid_outputs = [
        "Stellar Instant 2-Step Challenge",
        "Premium Funding Account",
        "Stellar Gold Challenge",
    ]
    
    print("Invalid outputs (should be rejected):")
    for output in invalid_outputs:
        program_id, is_valid, error = validate_llm_output("FundedNext", output)
        status = "✓" if not is_valid else "✗"  # Should be invalid
        print(f"{status} '{output}' → {program_id} ({'REJECTED' if not is_valid else 'INCORRECTLY ACCEPTED'})")
        if error:
            print(f"    Error: {error}")
    
    print()


def test_validation_report():
    """Test validation reporting"""
    print("="*60)
    print("TEST 5: Validation Reporting")
    print("="*60)
    
    from src.propfirm_scraper.validated_extractor import ValidatedLLMExtractor
    
    extractor = ValidatedLLMExtractor("FundedNext", strict=True)
    
    # Simulate some extractions
    test_extractions = [
        "Stellar 1-Step Challenge",       # Valid
        "Stellar 2-Step Challenge",       # Valid
        "Stellar Premium Account",        # Hallucination
        "Evaluation Challenge",           # Valid
        "Stellar Instant 2-Step",         # Hallucination
        "Stellar Lite",                   # Valid
    ]
    
    for extraction in test_extractions:
        extractor.validate_extracted_program(extraction)
    
    report = extractor.get_validation_report()
    
    print(f"Valid extractions: {report['valid_extractions']}")
    print(f"Hallucinations: {report['hallucinations_detected']}")
    print(f"Hallucination rate: {report['hallucination_rate']:.1%}")
    
    print("\nHallucinations detected:")
    for h in report['hallucinations']:
        print(f"  - {h['extracted_name']}")
    
    print("\nValid programs:")
    for p in set(report['valid_programs']):
        print(f"  - {p}")
    
    print()


def test_suggestions():
    """Test correction suggestions"""
    print("="*60)
    print("TEST 6: Correction Suggestions")
    print("="*60)
    
    validator = TaxonomyValidator()
    
    # Test invalid names that might have suggestions
    test_cases = [
        "Stellar Challenge",
        "2 Step Challenge",
        "Instant Account",
    ]
    
    for invalid_name in test_cases:
        suggestions = validator.suggest_corrections("FundedNext", invalid_name)
        
        print(f"Invalid: '{invalid_name}'")
        if suggestions:
            print(f"  Suggestions:")
            for prog_id, name in suggestions:
                print(f"    - {prog_id}: {name}")
        else:
            print(f"  No suggestions found")
        print()


def main():
    """Run all tests"""
    print("\n🧪 Testing LLM Taxonomy Validation (Guardrails)")
    print("="*60)
    print()
    
    results = []
    
    results.append(("Valid Mappings", test_valid_mappings()))
    results.append(("Hallucination Detection", test_hallucination_detection()))
    results.append(("Fuzzy Matching", test_fuzzy_matching()))
    
    # These are demo tests, not pass/fail
    test_llm_validation()
    test_validation_report()
    test_suggestions()
    
    # Summary
    print("="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    print()
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
