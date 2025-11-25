"""
Taxonomy validator for LLM output validation

Prevents hallucinated program names from entering the database
by validating against the official program taxonomy.
"""
import json
import re
from pathlib import Path
from typing import Optional, Dict, List, Tuple


class TaxonomyValidator:
    """Validates program names against official taxonomy"""
    
    def __init__(self, taxonomy_path: Optional[str] = None):
        """
        Initialize validator with program taxonomy
        
        Args:
            taxonomy_path: Path to program_taxonomy.json file
        """
        if taxonomy_path is None:
            taxonomy_path = Path(__file__).parent / "program_taxonomy.json"
        
        with open(taxonomy_path, 'r') as f:
            self.taxonomy = json.load(f)
    
    def map_alias_to_program(self, firm_name: str, candidate: str) -> Optional[str]:
        """
        Map a candidate program name to official program_id
        
        Args:
            firm_name: Name of the prop firm (e.g., "FundedNext")
            candidate: Candidate program name from LLM or user input
        
        Returns:
            Official program_id if valid, None if invalid/hallucination
        
        Example:
            >>> validator = TaxonomyValidator()
            >>> validator.map_alias_to_program("FundedNext", "stellar 1-step")
            'stellar_1step'
            >>> validator.map_alias_to_program("FundedNext", "fake program")
            None
        """
        # Normalize inputs
        candidate_normalized = self._normalize_name(candidate)
        
        # Get firm taxonomy
        firm_taxonomy = self.taxonomy.get(firm_name)
        if not firm_taxonomy:
            return None
        
        # Check if it's already an official program_id
        if candidate_normalized in firm_taxonomy.get("official_programs", {}):
            return candidate_normalized
        
        # Check aliases
        aliases = firm_taxonomy.get("aliases", {})
        for alias, program_id in aliases.items():
            if self._normalize_name(alias) == candidate_normalized:
                return program_id
        
        # Check if candidate matches any official program name
        official_programs = firm_taxonomy.get("official_programs", {})
        for program_id, official_name in official_programs.items():
            if self._normalize_name(official_name) == candidate_normalized:
                return program_id
        
        # Try fuzzy matching for common variations
        fuzzy_match = self._fuzzy_match(candidate_normalized, firm_taxonomy)
        if fuzzy_match:
            return fuzzy_match
        
        return None
    
    def validate_program_id(self, firm_name: str, program_id: str) -> bool:
        """
        Check if a program_id is valid for a firm
        
        Args:
            firm_name: Name of the prop firm
            program_id: Program identifier to validate
        
        Returns:
            True if valid, False otherwise
        """
        firm_taxonomy = self.taxonomy.get(firm_name)
        if not firm_taxonomy:
            return False
        
        return program_id in firm_taxonomy.get("official_programs", {})
    
    def get_all_valid_programs(self, firm_name: str) -> List[str]:
        """
        Get list of all valid program_ids for a firm
        
        Args:
            firm_name: Name of the prop firm
        
        Returns:
            List of valid program_ids
        """
        firm_taxonomy = self.taxonomy.get(firm_name)
        if not firm_taxonomy:
            return []
        
        return list(firm_taxonomy.get("official_programs", {}).keys())
    
    def suggest_corrections(self, firm_name: str, invalid_name: str) -> List[Tuple[str, str]]:
        """
        Suggest possible corrections for an invalid program name
        
        Args:
            firm_name: Name of the prop firm
            invalid_name: Invalid program name
        
        Returns:
            List of (program_id, official_name) tuples as suggestions
        """
        firm_taxonomy = self.taxonomy.get(firm_name)
        if not firm_taxonomy:
            return []
        
        suggestions = []
        invalid_normalized = self._normalize_name(invalid_name)
        
        # Find similar program names
        official_programs = firm_taxonomy.get("official_programs", {})
        for program_id, official_name in official_programs.items():
            # Check if any words match
            invalid_words = set(invalid_normalized.split())
            official_words = set(self._normalize_name(official_name).split())
            
            common_words = invalid_words & official_words
            if common_words and len(common_words) >= 2:
                suggestions.append((program_id, official_name))
        
        return suggestions
    
    def _normalize_name(self, name: str) -> str:
        """
        Normalize a program name for comparison
        
        Converts to lowercase, removes extra spaces, removes special chars
        """
        # Convert to lowercase
        normalized = name.lower().strip()
        
        # Replace hyphens and underscores with spaces
        normalized = re.sub(r'[-_]', ' ', normalized)
        
        # Remove special characters except spaces and numbers
        normalized = re.sub(r'[^a-z0-9\s]', '', normalized)
        
        # Collapse multiple spaces
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Remove common filler words
        filler_words = ['the', 'a', 'an', 'and', 'or', 'of']
        words = [w for w in normalized.split() if w not in filler_words]
        
        return ' '.join(words)
    
    def _fuzzy_match(self, candidate: str, firm_taxonomy: Dict) -> Optional[str]:
        """
        Attempt fuzzy matching for common variations
        
        Handles cases like:
        - "stellar1step" → "stellar_1step"
        - "2 step stellar" → "stellar_2step"
        - "evaluation 2 step" → "evaluation_2step"
        """
        # Try to construct program_id from candidate
        candidate_parts = candidate.split()
        
        # Pattern: [name] [number] step
        if 'step' in candidate_parts:
            # Extract number
            numbers = [p for p in candidate_parts if any(c.isdigit() for c in p)]
            if numbers:
                step_num = ''.join(filter(str.isdigit, numbers[0]))
                
                # Check for stellar/evaluation
                if 'stellar' in candidate:
                    program_id = f"stellar_{step_num}step"
                    if program_id in firm_taxonomy.get("official_programs", {}):
                        return program_id
                elif 'evaluation' in candidate:
                    program_id = f"evaluation_{step_num}step"
                    if program_id in firm_taxonomy.get("official_programs", {}):
                        return program_id
        
        # Pattern: stellar lite
        if 'stellar' in candidate and 'lite' in candidate:
            program_id = "stellar_lite"
            if program_id in firm_taxonomy.get("official_programs", {}):
                return program_id
        
        # Pattern: stellar instant
        if 'stellar' in candidate and ('instant' in candidate or 'funded' in candidate):
            program_id = "stellar_instant"
            if program_id in firm_taxonomy.get("official_programs", {}):
                return program_id
        
        return None
    
    def validate_llm_output(
        self, 
        firm_name: str, 
        llm_output: str, 
        strict: bool = True
    ) -> Tuple[Optional[str], bool, Optional[str]]:
        """
        Validate LLM output for program name extraction
        
        Args:
            firm_name: Name of the prop firm
            llm_output: Raw output from LLM
            strict: If True, reject any invalid names. If False, suggest corrections
        
        Returns:
            Tuple of (program_id, is_valid, error_message)
            
        Example:
            >>> validator = TaxonomyValidator()
            >>> program_id, valid, error = validator.validate_llm_output(
            ...     "FundedNext", 
            ...     "Stellar 1-Step Challenge"
            ... )
            >>> print(program_id)  # "stellar_1step"
            >>> print(valid)       # True
            
            >>> program_id, valid, error = validator.validate_llm_output(
            ...     "FundedNext", 
            ...     "Stellar Instant 2-Step Challenge"  # Hallucination!
            ... )
            >>> print(program_id)  # None
            >>> print(valid)       # False
            >>> print(error)       # "Invalid program name: not in taxonomy"
        """
        # Try to map the candidate
        program_id = self.map_alias_to_program(firm_name, llm_output)
        
        if program_id:
            return program_id, True, None
        
        # Invalid/hallucination detected
        error_msg = f"Invalid program name: '{llm_output}' not found in {firm_name} taxonomy"
        
        if not strict:
            # Try to suggest corrections
            suggestions = self.suggest_corrections(firm_name, llm_output)
            if suggestions:
                suggestion_text = ", ".join([f"{pid} ({name})" for pid, name in suggestions])
                error_msg += f". Did you mean: {suggestion_text}?"
        
        return None, False, error_msg


# Singleton instance for easy import
_validator_instance = None

def get_validator(taxonomy_path: Optional[str] = None) -> TaxonomyValidator:
    """Get or create singleton validator instance"""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = TaxonomyValidator(taxonomy_path)
    return _validator_instance


def map_alias_to_program(firm_name: str, candidate: str) -> Optional[str]:
    """
    Convenience function to map alias to program_id
    
    This is the main function to use for guardrailing LLM output.
    
    Args:
        firm_name: Name of the prop firm
        candidate: Candidate program name from LLM
    
    Returns:
        Official program_id if valid, None if hallucination
    
    Example:
        >>> from config.taxonomy_validator import map_alias_to_program
        >>> 
        >>> # LLM extracted a program name
        >>> llm_output = "Stellar 1-Step Challenge"
        >>> program_id = map_alias_to_program("FundedNext", llm_output.lower())
        >>> 
        >>> if program_id is None:
        ...     # Hallucination detected - ignore or flag
        ...     print("Warning: LLM hallucinated program name")
        ... else:
        ...     # Valid program - safe to use
        ...     save_to_database(program_id)
    """
    validator = get_validator()
    return validator.map_alias_to_program(firm_name, candidate)


def validate_llm_output(
    firm_name: str, 
    llm_output: str, 
    strict: bool = True
) -> Tuple[Optional[str], bool, Optional[str]]:
    """
    Convenience function to validate LLM output
    
    Args:
        firm_name: Name of the prop firm
        llm_output: Raw LLM output
        strict: Reject invalid names strictly
    
    Returns:
        Tuple of (program_id, is_valid, error_message)
    """
    validator = get_validator()
    return validator.validate_llm_output(firm_name, llm_output, strict)


# Example usage in extraction pipelines
def safe_extract_program_name(firm_name: str, extracted_name: str) -> Optional[str]:
    """
    Safely extract program name with validation
    
    Use this in your extraction pipelines to prevent hallucinations.
    """
    program_id, is_valid, error = validate_llm_output(firm_name, extracted_name)
    
    if not is_valid:
        print(f"⚠️  LLM Validation Warning: {error}")
        return None
    
    return program_id
