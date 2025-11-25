"""
Unit tests for program taxonomy validation

Tests map_alias_to_program to verify it resolves correct names and rejects unknowns
"""
import pytest
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.taxonomy_validator import (
    TaxonomyValidator,
    map_alias_to_program,
    validate_llm_output,
    get_validator
)


class TestProgramTaxonomy:
    """Test program taxonomy validation"""
    
    @pytest.fixture
    def validator(self):
        """Get validator instance"""
        return TaxonomyValidator()
    
    # =========================================================================
    # Test: Exact Program ID Matches
    # =========================================================================
    
    def test_exact_program_id_match(self, validator):
        """Test exact program_id matches return unchanged"""
        assert validator.map_alias_to_program("FundedNext", "stellar_1step") == "stellar_1step"
        assert validator.map_alias_to_program("FundedNext", "stellar_2step") == "stellar_2step"
        assert validator.map_alias_to_program("FundedNext", "evaluation_2step") == "evaluation_2step"
        assert validator.map_alias_to_program("FundedNext", "stellar_lite") == "stellar_lite"
        assert validator.map_alias_to_program("FundedNext", "stellar_instant") == "stellar_instant"
    
    # =========================================================================
    # Test: Official Program Name Matches
    # =========================================================================
    
    def test_official_program_names(self, validator):
        """Test official program names map to program_ids"""
        assert validator.map_alias_to_program(
            "FundedNext", 
            "Stellar 1-Step Challenge"
        ) == "stellar_1step"
        
        assert validator.map_alias_to_program(
            "FundedNext", 
            "Stellar 2-Step Challenge"
        ) == "stellar_2step"
        
        assert validator.map_alias_to_program(
            "FundedNext", 
            "Evaluation Challenge"
        ) == "evaluation_2step"
        
        assert validator.map_alias_to_program(
            "FundedNext", 
            "Stellar Lite Challenge"
        ) == "stellar_lite"
        
        assert validator.map_alias_to_program(
            "FundedNext", 
            "Stellar Instant Account"
        ) == "stellar_instant"
    
    # =========================================================================
    # Test: Alias Resolution
    # =========================================================================
    
    def test_alias_resolution(self, validator):
        """Test aliases map to correct program_ids"""
        # Common aliases
        assert validator.map_alias_to_program("FundedNext", "stellar") == "stellar_1step"
        assert validator.map_alias_to_program("FundedNext", "evaluation") == "evaluation_2step"
        assert validator.map_alias_to_program("FundedNext", "lite") == "stellar_lite"
        assert validator.map_alias_to_program("FundedNext", "instant") == "stellar_instant"
        assert validator.map_alias_to_program("FundedNext", "funded") == "stellar_instant"
        
        # Verbose aliases
        assert validator.map_alias_to_program("FundedNext", "stellar 1-step") == "stellar_1step"
        assert validator.map_alias_to_program("FundedNext", "stellar 2-step") == "stellar_2step"
        assert validator.map_alias_to_program("FundedNext", "stellar lite") == "stellar_lite"
        assert validator.map_alias_to_program("FundedNext", "stellar instant") == "stellar_instant"
        assert validator.map_alias_to_program("FundedNext", "evaluation challenge") == "evaluation_2step"
    
    # =========================================================================
    # Test: Case Insensitivity
    # =========================================================================
    
    def test_case_insensitive(self, validator):
        """Test validation is case-insensitive"""
        assert validator.map_alias_to_program("FundedNext", "STELLAR_1STEP") == "stellar_1step"
        assert validator.map_alias_to_program("FundedNext", "Stellar 1-Step") == "stellar_1step"
        assert validator.map_alias_to_program("FundedNext", "stellar 1-step") == "stellar_1step"
        assert validator.map_alias_to_program("FundedNext", "EVALUATION") == "evaluation_2step"
    
    # =========================================================================
    # Test: Fuzzy Matching
    # =========================================================================
    
    def test_fuzzy_matching(self, validator):
        """Test fuzzy matching handles common variations"""
        # No spaces
        assert validator.map_alias_to_program("FundedNext", "stellar1step") == "stellar_1step"
        assert validator.map_alias_to_program("FundedNext", "stellar2step") == "stellar_2step"
        
        # Reversed order
        assert validator.map_alias_to_program("FundedNext", "1 step stellar") == "stellar_1step"
        assert validator.map_alias_to_program("FundedNext", "2 step stellar") == "stellar_2step"
        
        # Hyphenated
        assert validator.map_alias_to_program("FundedNext", "stellar-lite") == "stellar_lite"
        assert validator.map_alias_to_program("FundedNext", "stellar-instant") == "stellar_instant"
        
        # Concatenated
        assert validator.map_alias_to_program("FundedNext", "stellarlite") == "stellar_lite"
        
        # Different spacing
        assert validator.map_alias_to_program("FundedNext", "evaluation 2 step") == "evaluation_2step"
    
    # =========================================================================
    # Test: Hallucination Detection
    # =========================================================================
    
    def test_hallucination_detection(self, validator):
        """Test that hallucinations return None"""
        # Mixing programs
        assert validator.map_alias_to_program(
            "FundedNext", 
            "Stellar Instant 2-Step Challenge"
        ) is None
        
        assert validator.map_alias_to_program(
            "FundedNext", 
            "Evaluation Lite Challenge"
        ) is None
        
        # Non-existent variants
        assert validator.map_alias_to_program(
            "FundedNext", 
            "Stellar Premium Challenge"
        ) is None
        
        assert validator.map_alias_to_program(
            "FundedNext", 
            "Stellar Gold Challenge"
        ) is None
        
        assert validator.map_alias_to_program(
            "FundedNext", 
            "Stellar Express"
        ) is None
        
        # Wrong numbers
        assert validator.map_alias_to_program(
            "FundedNext", 
            "Stellar 3-Step Challenge"
        ) is None
        
        assert validator.map_alias_to_program(
            "FundedNext", 
            "Evaluation 1-Step"
        ) is None
        
        # Completely made up
        assert validator.map_alias_to_program(
            "FundedNext", 
            "Ultra Funding Program"
        ) is None
        
        assert validator.map_alias_to_program(
            "FundedNext", 
            "Elite Trader Challenge"
        ) is None
        
        assert validator.map_alias_to_program(
            "FundedNext", 
            "Pro Account Package"
        ) is None
    
    # =========================================================================
    # Test: Invalid Firm
    # =========================================================================
    
    def test_invalid_firm(self, validator):
        """Test that invalid firm names return None"""
        assert validator.map_alias_to_program("InvalidFirm", "stellar 1-step") is None
        assert validator.map_alias_to_program("", "stellar 1-step") is None
    
    # =========================================================================
    # Test: Empty/Null Inputs
    # =========================================================================
    
    def test_empty_inputs(self, validator):
        """Test empty inputs return None"""
        assert validator.map_alias_to_program("FundedNext", "") is None
        assert validator.map_alias_to_program("FundedNext", "   ") is None
    
    # =========================================================================
    # Test: Program ID Validation
    # =========================================================================
    
    def test_validate_program_id(self, validator):
        """Test validate_program_id method"""
        # Valid program_ids
        assert validator.validate_program_id("FundedNext", "stellar_1step") is True
        assert validator.validate_program_id("FundedNext", "stellar_2step") is True
        assert validator.validate_program_id("FundedNext", "evaluation_2step") is True
        assert validator.validate_program_id("FundedNext", "stellar_lite") is True
        assert validator.validate_program_id("FundedNext", "stellar_instant") is True
        
        # Invalid program_ids
        assert validator.validate_program_id("FundedNext", "stellar_3step") is False
        assert validator.validate_program_id("FundedNext", "invalid") is False
        assert validator.validate_program_id("InvalidFirm", "stellar_1step") is False
    
    # =========================================================================
    # Test: Get Valid Programs
    # =========================================================================
    
    def test_get_all_valid_programs(self, validator):
        """Test getting list of valid programs"""
        programs = validator.get_all_valid_programs("FundedNext")
        
        assert "stellar_1step" in programs
        assert "stellar_2step" in programs
        assert "evaluation_2step" in programs
        assert "stellar_lite" in programs
        assert "stellar_instant" in programs
        assert len(programs) == 5
        
        # Invalid firm
        assert validator.get_all_valid_programs("InvalidFirm") == []
    
    # =========================================================================
    # Test: Correction Suggestions
    # =========================================================================
    
    def test_correction_suggestions(self, validator):
        """Test correction suggestions for invalid names"""
        # Partial match should suggest corrections
        suggestions = validator.suggest_corrections("FundedNext", "Stellar Challenge")
        
        # Should suggest stellar programs
        program_ids = [s[0] for s in suggestions]
        assert any("stellar" in pid for pid in program_ids)
        
        # Should have multiple suggestions
        assert len(suggestions) >= 1
    
    # =========================================================================
    # Test: Full LLM Validation
    # =========================================================================
    
    def test_validate_llm_output_success(self, validator):
        """Test validate_llm_output with valid input"""
        program_id, is_valid, error = validator.validate_llm_output(
            "FundedNext",
            "Stellar 1-Step Challenge"
        )
        
        assert program_id == "stellar_1step"
        assert is_valid is True
        assert error is None
    
    def test_validate_llm_output_failure(self, validator):
        """Test validate_llm_output with invalid input"""
        program_id, is_valid, error = validator.validate_llm_output(
            "FundedNext",
            "Stellar Premium Challenge"
        )
        
        assert program_id is None
        assert is_valid is False
        assert error is not None
        assert "not found" in error.lower()
    
    def test_validate_llm_output_with_suggestions(self, validator):
        """Test validate_llm_output with suggestions in permissive mode"""
        program_id, is_valid, error = validator.validate_llm_output(
            "FundedNext",
            "Stellar Challenge",
            strict=False
        )
        
        assert program_id is None
        assert is_valid is False
        assert error is not None
        # Should contain suggestions
        assert "did you mean" in error.lower() or "not found" in error.lower()
    
    # =========================================================================
    # Test: Convenience Functions
    # =========================================================================
    
    def test_convenience_map_alias_to_program(self):
        """Test convenience function map_alias_to_program"""
        assert map_alias_to_program("FundedNext", "stellar 1-step") == "stellar_1step"
        assert map_alias_to_program("FundedNext", "invalid") is None
    
    def test_convenience_validate_llm_output(self):
        """Test convenience function validate_llm_output"""
        program_id, is_valid, error = validate_llm_output(
            "FundedNext",
            "Stellar 1-Step Challenge"
        )
        
        assert program_id == "stellar_1step"
        assert is_valid is True
    
    # =========================================================================
    # Test: Singleton Validator
    # =========================================================================
    
    def test_singleton_validator(self):
        """Test get_validator returns same instance"""
        v1 = get_validator()
        v2 = get_validator()
        assert v1 is v2


# =============================================================================
# Parametrized Tests for Comprehensive Coverage
# =============================================================================

@pytest.mark.parametrize("candidate,expected", [
    # Exact matches
    ("stellar_1step", "stellar_1step"),
    ("stellar_2step", "stellar_2step"),
    ("evaluation_2step", "evaluation_2step"),
    ("stellar_lite", "stellar_lite"),
    ("stellar_instant", "stellar_instant"),
    
    # Official names
    ("Stellar 1-Step Challenge", "stellar_1step"),
    ("Stellar 2-Step Challenge", "stellar_2step"),
    ("Evaluation Challenge", "evaluation_2step"),
    
    # Aliases
    ("stellar", "stellar_1step"),
    ("evaluation", "evaluation_2step"),
    ("lite", "stellar_lite"),
    ("instant", "stellar_instant"),
    
    # Case variations
    ("STELLAR_1STEP", "stellar_1step"),
    ("Stellar 1-Step", "stellar_1step"),
    
    # Fuzzy matches
    ("stellar1step", "stellar_1step"),
    ("2 step stellar", "stellar_2step"),
    ("stellar-lite", "stellar_lite"),
    ("stellarlite", "stellar_lite"),
])
def test_valid_program_mappings(candidate, expected):
    """Parametrized test for valid program mappings"""
    result = map_alias_to_program("FundedNext", candidate)
    assert result == expected, f"Expected {candidate} → {expected}, got {result}"


@pytest.mark.parametrize("hallucination", [
    # Mixing programs
    "Stellar Instant 2-Step Challenge",
    "Evaluation Lite Challenge",
    "Stellar 1-Step Instant",
    
    # Non-existent variants
    "Stellar Premium Challenge",
    "Stellar Gold Challenge",
    "Stellar Express",
    "Stellar Pro Account",
    "Stellar Advanced",
    
    # Wrong numbers
    "Stellar 3-Step Challenge",
    "Stellar 4-Step",
    "Evaluation 1-Step",
    "Evaluation 3-Step",
    
    # Made up names
    "Ultra Funding Program",
    "Elite Trader Challenge",
    "Pro Account Package",
    "Diamond Challenge",
    "Platinum Account",
])
def test_hallucination_rejection(hallucination):
    """Parametrized test for hallucination rejection"""
    result = map_alias_to_program("FundedNext", hallucination)
    assert result is None, f"Hallucination '{hallucination}' should return None, got {result}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
