"""
Validated LLM extraction wrapper

Wraps LLM extraction with taxonomy validation to prevent hallucinations
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.taxonomy_validator import map_alias_to_program, validate_llm_output


class ValidatedLLMExtractor:
    """LLM extractor with built-in validation"""
    
    def __init__(self, firm_name: str, strict: bool = True):
        """
        Initialize validated extractor
        
        Args:
            firm_name: Name of the prop firm (for taxonomy lookup)
            strict: If True, reject invalid program names. If False, warn only
        """
        self.firm_name = firm_name
        self.strict = strict
        self.hallucinations_detected = []
        self.valid_extractions = []
    
    def validate_extracted_program(self, extracted_name: str) -> Optional[str]:
        """
        Validate an extracted program name
        
        Args:
            extracted_name: Program name extracted by LLM
        
        Returns:
            Official program_id if valid, None if hallucination
        """
        if not extracted_name:
            return None
        
        # Normalize and validate
        candidate = extracted_name.lower().strip()
        program_id = map_alias_to_program(self.firm_name, candidate)
        
        if program_id is None:
            # Hallucination detected!
            warning = {
                'extracted_name': extracted_name,
                'normalized': candidate,
                'firm': self.firm_name,
                'reason': 'Not found in taxonomy'
            }
            self.hallucinations_detected.append(warning)
            
            print(f"    ⚠️  HALLUCINATION DETECTED: '{extracted_name}'")
            print(f"        Reason: Not found in {self.firm_name} taxonomy")
            
            if self.strict:
                print(f"        Action: REJECTED (strict mode)")
                return None
            else:
                print(f"        Action: FLAGGED (permissive mode)")
        else:
            self.valid_extractions.append({
                'extracted_name': extracted_name,
                'program_id': program_id
            })
            print(f"    ✓ Validated: '{extracted_name}' → {program_id}")
        
        return program_id
    
    def validate_extraction_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate an entire extraction result
        
        Checks for program names in various fields and validates them
        
        Args:
            result: Extraction result dict
        
        Returns:
            Validated result with program_ids added and invalid entries removed
        """
        validated_result = result.copy()
        
        # Check for challenge_type field
        if 'challenge_type' in result:
            challenge_type = result['challenge_type']
            program_id = self.validate_extracted_program(challenge_type)
            
            if program_id:
                validated_result['program_id'] = program_id
                validated_result['challenge_type'] = program_id  # Normalize
            elif self.strict:
                # Remove invalid challenge_type in strict mode
                del validated_result['challenge_type']
        
        # Check for challenge_types array
        if 'challenge_types' in result and isinstance(result['challenge_types'], dict):
            validated_types = {}
            
            for challenge_name, rules in result['challenge_types'].items():
                program_id = self.validate_extracted_program(challenge_name)
                
                if program_id:
                    validated_types[program_id] = rules
                elif not self.strict:
                    # Keep original but flag it
                    validated_types[challenge_name] = rules
                    if 'validation_warnings' not in validated_types[challenge_name]:
                        validated_types[challenge_name] = rules.copy()
                        validated_types[challenge_name]['validation_warning'] = 'Invalid program name'
            
            validated_result['challenge_types'] = validated_types
        
        # Check for program_name field (common LLM output)
        if 'program_name' in result:
            program_name = result['program_name']
            program_id = self.validate_extracted_program(program_name)
            
            if program_id:
                validated_result['program_id'] = program_id
            elif self.strict:
                del validated_result['program_name']
        
        return validated_result
    
    def get_validation_report(self) -> Dict[str, Any]:
        """
        Get validation report
        
        Returns:
            Report with statistics on validations and hallucinations
        """
        return {
            'firm_name': self.firm_name,
            'strict_mode': self.strict,
            'valid_extractions': len(self.valid_extractions),
            'hallucinations_detected': len(self.hallucinations_detected),
            'hallucination_rate': (
                len(self.hallucinations_detected) / 
                (len(self.valid_extractions) + len(self.hallucinations_detected))
                if (len(self.valid_extractions) + len(self.hallucinations_detected)) > 0
                else 0
            ),
            'hallucinations': self.hallucinations_detected,
            'valid_programs': [v['program_id'] for v in self.valid_extractions]
        }


def validate_extraction_file(
    input_file: str,
    firm_name: str,
    output_file: Optional[str] = None,
    strict: bool = True
) -> Dict[str, Any]:
    """
    Validate an entire extraction file
    
    Args:
        input_file: Path to extraction results JSON
        firm_name: Name of the prop firm
        output_file: Optional output file for validated results
        strict: Use strict validation
    
    Returns:
        Validation report
    """
    print(f"🔍 Validating LLM extractions for {firm_name}")
    print(f"   Mode: {'STRICT (reject invalid)' if strict else 'PERMISSIVE (flag invalid)'}")
    print(f"   Input: {input_file}\n")
    
    # Load extraction results
    with open(input_file, 'r', encoding='utf-8') as f:
        extractions = json.load(f)
    
    if not isinstance(extractions, list):
        extractions = [extractions]
    
    # Validate each extraction
    validator = ValidatedLLMExtractor(firm_name, strict)
    validated_results = []
    
    for idx, result in enumerate(extractions, 1):
        print(f"[{idx}/{len(extractions)}] Validating extraction...")
        
        validated = validator.validate_extraction_result(result)
        validated_results.append(validated)
        print()
    
    # Get report
    report = validator.get_validation_report()
    
    # Save validated results if output file specified
    if output_file:
        output_data = {
            'firm_name': firm_name,
            'validation_mode': 'strict' if strict else 'permissive',
            'results': validated_results,
            'validation_report': report
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"✓ Saved validated results to {output_file}")
    
    # Print summary
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    print(f"Firm: {report['firm_name']}")
    print(f"Mode: {'STRICT' if report['strict_mode'] else 'PERMISSIVE'}")
    print(f"Valid Extractions: {report['valid_extractions']}")
    print(f"Hallucinations Detected: {report['hallucinations_detected']}")
    print(f"Hallucination Rate: {report['hallucination_rate']:.1%}")
    
    if report['hallucinations_detected'] > 0:
        print(f"\n⚠️  HALLUCINATIONS FOUND:")
        for h in report['hallucinations']:
            print(f"   - '{h['extracted_name']}' (not in taxonomy)")
    
    if report['valid_extractions'] > 0:
        print(f"\n✓ VALID PROGRAMS:")
        for prog in set(report['valid_programs']):
            print(f"   - {prog}")
    
    return report


# Example usage functions
def validate_challenge_extraction(
    firm_name: str,
    extracted_challenges: List[str]
) -> List[str]:
    """
    Validate a list of extracted challenge names
    
    Example:
        >>> challenges = ["Stellar 1-Step", "Stellar Instant 2-Step", "Evaluation"]
        >>> valid = validate_challenge_extraction("FundedNext", challenges)
        >>> print(valid)
        ['stellar_1step', 'evaluation_2step']
    """
    validated = []
    
    for challenge in extracted_challenges:
        program_id = map_alias_to_program(firm_name, challenge.lower())
        
        if program_id:
            validated.append(program_id)
        else:
            print(f"⚠️  Hallucination detected: '{challenge}' (ignored)")
    
    return validated


def safe_extract_program_name(firm_name: str, llm_output: str) -> Optional[str]:
    """
    Safely extract program name with validation
    
    Use this as a wrapper around LLM extraction:
    
    Example:
        >>> # Get LLM output
        >>> llm_output = llm_extract_challenge_name(text)
        >>> 
        >>> # Validate before using
        >>> program_id = safe_extract_program_name("FundedNext", llm_output)
        >>> 
        >>> if program_id is None:
        ...     # Hallucination - don't save to database
        ...     log_warning(f"LLM hallucinated: {llm_output}")
        ... else:
        ...     # Valid - safe to save
        ...     save_to_database(program_id=program_id)
    """
    program_id, is_valid, error = validate_llm_output(firm_name, llm_output)
    
    if not is_valid:
        print(f"⚠️  LLM Validation Failed: {error}")
        return None
    
    return program_id


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate LLM extraction results")
    parser.add_argument("input_file", help="Input extraction JSON file")
    parser.add_argument("--firm", required=True, help="Firm name (e.g., FundedNext)")
    parser.add_argument("--output", help="Output file for validated results")
    parser.add_argument("--permissive", action="store_true", help="Use permissive mode (flag only)")
    
    args = parser.parse_args()
    
    validate_extraction_file(
        args.input_file,
        args.firm,
        args.output,
        strict=not args.permissive
    )
