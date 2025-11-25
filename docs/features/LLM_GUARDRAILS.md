# LLM Guardrails: Taxonomy Validation

## Overview

LLM guardrails prevent hallucinated program names from entering the database or risk monitor by validating all LLM outputs against the official program taxonomy.

## Problem Statement

LLMs can hallucinate program names that don't exist:
- ❌ "Stellar Instant 2-Step Challenge" (mixing two programs)
- ❌ "Stellar Premium Account" (doesn't exist)
- ❌ "Evaluation 1-Step" (wrong step count)

These hallucinations can:
1. Corrupt the database with invalid program names
2. Cause risk monitor to fail loading rules
3. Create confusion in reporting and analysis

## Solution: Taxonomy Validation

All LLM outputs are validated against `config/program_taxonomy.json` before being used.

```python
from config.taxonomy_validator import map_alias_to_program

# LLM extracted a program name
llm_output = "Stellar Instant 2-Step Challenge"

# Validate before using
program_id = map_alias_to_program("FundedNext", llm_output.lower())

if program_id is None:
    # Hallucination detected → ignore or flag
    print("⚠️ LLM hallucinated - rejecting")
else:
    # Valid program → safe to use
    save_to_database(program_id)
```

## Architecture

```
┌────────────────────────────────────────────────────────┐
│                    LLM EXTRACTION                       │
└────────────────┬───────────────────────────────────────┘
                 │
                 │ Raw output: "Stellar Instant 2-Step"
                 ▼
┌────────────────────────────────────────────────────────┐
│               TAXONOMY VALIDATOR                        │
│                                                         │
│  1. Normalize: "stellar instant 2 step"                │
│  2. Check official programs: ✗ not found               │
│  3. Check aliases: ✗ not found                         │
│  4. Try fuzzy match: ✗ no match                        │
│  5. Return: None (HALLUCINATION)                       │
└────────────────┬───────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────┐
│               EXTRACTION PIPELINE                       │
│                                                         │
│  if program_id is None:                                │
│      log_warning("Hallucination detected")            │
│      reject_extraction()                               │
│  else:                                                  │
│      save_to_database(program_id)                      │
└────────────────────────────────────────────────────────┘
```

## Components

### 1. TaxonomyValidator (`config/taxonomy_validator.py`)

Core validation class:

```python
from config.taxonomy_validator import TaxonomyValidator

validator = TaxonomyValidator()

# Validate a single program name
program_id = validator.map_alias_to_program("FundedNext", "stellar 1-step")
# Returns: "stellar_1step"

# Validate LLM output with details
program_id, is_valid, error = validator.validate_llm_output(
    "FundedNext", 
    "Stellar Premium Challenge"
)
# Returns: (None, False, "Invalid program name: not in taxonomy")
```

### 2. ValidatedLLMExtractor (`src/propfirm_scraper/validated_extractor.py`)

Wrapper for LLM extraction with automatic validation:

```python
from src.propfirm_scraper.validated_extractor import ValidatedLLMExtractor

extractor = ValidatedLLMExtractor("FundedNext", strict=True)

# Validate extracted program names
for challenge_name in llm_extracted_challenges:
    program_id = extractor.validate_extracted_program(challenge_name)
    
    if program_id:
        # Valid - save to database
        save_rule(program_id, rules)
    else:
        # Hallucination - logged and rejected
        pass

# Get validation report
report = extractor.get_validation_report()
print(f"Hallucination rate: {report['hallucination_rate']:.1%}")
```

### 3. Convenience Functions

Quick validation for common use cases:

```python
from config.taxonomy_validator import map_alias_to_program, validate_llm_output

# Simple mapping (most common)
program_id = map_alias_to_program("FundedNext", llm_output.lower())

# Full validation with error details
program_id, is_valid, error = validate_llm_output("FundedNext", llm_output)
```

## Usage Patterns

### Pattern 1: Single Extraction Validation

```python
from config.taxonomy_validator import map_alias_to_program

def extract_challenge_from_page(text):
    # LLM extracts challenge name
    llm_output = llm.extract(text)
    
    # Validate before using
    program_id = map_alias_to_program("FundedNext", llm_output.lower())
    
    if program_id is None:
        # Hallucination - don't save
        logger.warning(f"LLM hallucinated: {llm_output}")
        return None
    
    # Valid - safe to save
    return program_id
```

### Pattern 2: Batch Validation

```python
from src.propfirm_scraper.validated_extractor import validate_challenge_extraction

# LLM extracted multiple challenges
llm_challenges = [
    "Stellar 1-Step",
    "Stellar Premium",  # Hallucination
    "Evaluation"
]

# Validate all at once
valid_programs = validate_challenge_extraction("FundedNext", llm_challenges)

# Result: ['stellar_1step', 'evaluation_2step']
# "Stellar Premium" was filtered out
```

### Pattern 3: File Validation

```bash
# Validate an entire extraction file
python -m src.propfirm_scraper.validated_extractor \
    output/rules_llm.json \
    --firm FundedNext \
    --output output/rules_validated.json
```

### Pattern 4: Strict vs Permissive Mode

```python
from src.propfirm_scraper.validated_extractor import ValidatedLLMExtractor

# STRICT MODE: Reject invalid names
extractor = ValidatedLLMExtractor("FundedNext", strict=True)
program_id = extractor.validate_extracted_program("Stellar Premium")
# Returns: None (rejected)

# PERMISSIVE MODE: Flag but don't reject
extractor = ValidatedLLMExtractor("FundedNext", strict=False)
program_id = extractor.validate_extracted_program("Stellar Premium")
# Returns: None (but logged as warning, not error)
```

## Validation Logic

### 1. Exact Match
```python
"stellar_1step" → "stellar_1step" ✓
```

### 2. Alias Lookup
```python
"stellar" → "stellar_1step" ✓
"lite" → "stellar_lite" ✓
"instant" → "stellar_instant" ✓
```

### 3. Official Name Match
```python
"Stellar 1-Step Challenge" → "stellar_1step" ✓
"Evaluation Challenge" → "evaluation_2step" ✓
```

### 4. Fuzzy Match
```python
"stellar1step" → "stellar_1step" ✓
"2 step stellar" → "stellar_2step" ✓
"stellarlite" → "stellar_lite" ✓
```

### 5. Rejection (Hallucination)
```python
"Stellar Instant 2-Step" → None ✗
"Stellar Premium" → None ✗
"Evaluation 1-Step" → None ✗
```

## Integration Points

### 1. LLM Extractor (`src/propfirm_scraper/llm_extractor.py`)

```python
from config.taxonomy_validator import map_alias_to_program

def extract_with_llm(input_file, firm_name):
    for page in pages:
        # Extract with LLM
        result = query_llm(page['html'])
        
        # Validate challenge_type
        if 'challenge_type' in result:
            program_id = map_alias_to_program(firm_name, result['challenge_type'])
            
            if program_id:
                result['program_id'] = program_id
            else:
                # Hallucination - remove or flag
                del result['challenge_type']
                result['validation_warning'] = 'Invalid challenge type'
```

### 2. Hybrid Extractor (`src/propfirm_scraper/hybrid_extractor.py`)

```python
from config.taxonomy_validator import validate_llm_output

def hybrid_extract(text, firm_name):
    # Pattern extraction (always trusted)
    pattern_result = extract_with_patterns(text)
    
    # LLM extraction (needs validation)
    llm_result = extract_with_llm(text)
    
    # Validate LLM-extracted programs
    if 'challenge_type' in llm_result:
        program_id, is_valid, error = validate_llm_output(
            firm_name, 
            llm_result['challenge_type']
        )
        
        if is_valid:
            pattern_result['program_id'] = program_id
        else:
            logger.warning(f"LLM hallucination: {error}")
    
    return pattern_result
```

### 3. Database Ingestion (`database/ingest_documents.py`)

```python
from config.taxonomy_validator import map_alias_to_program

def ingest_rules(rules_data, firm_name):
    for rule in rules_data:
        challenge_type = rule.get('challenge_type')
        
        # Validate before inserting
        program_id = map_alias_to_program(firm_name, challenge_type)
        
        if program_id is None:
            logger.error(f"Invalid challenge_type: {challenge_type}")
            continue  # Skip this rule
        
        # Insert with validated program_id
        db.execute("""
            INSERT INTO firm_rule (challenge_type, ...)
            VALUES (?, ...)
        """, (program_id, ...))
```

## Testing

Run validation tests:

```bash
# Run all validation tests
python tests/test_taxonomy_validation.py

# Test specific validation
python -c "
from config.taxonomy_validator import map_alias_to_program
print(map_alias_to_program('FundedNext', 'stellar 1-step'))
"
```

## Validation Report

The validator generates detailed reports:

```python
from src.propfirm_scraper.validated_extractor import ValidatedLLMExtractor

extractor = ValidatedLLMExtractor("FundedNext", strict=True)

# ... extract and validate ...

report = extractor.get_validation_report()

"""
{
  'firm_name': 'FundedNext',
  'strict_mode': True,
  'valid_extractions': 15,
  'hallucinations_detected': 3,
  'hallucination_rate': 0.167,  # 16.7%
  'hallucinations': [
    {
      'extracted_name': 'Stellar Premium Challenge',
      'normalized': 'stellar premium challenge',
      'firm': 'FundedNext',
      'reason': 'Not found in taxonomy'
    },
    ...
  ],
  'valid_programs': ['stellar_1step', 'stellar_2step', ...]
}
"""
```

## Common Hallucinations

### Mixing Programs
- ❌ "Stellar Instant 2-Step Challenge" (instant + 2-step)
- ❌ "Evaluation Lite Challenge" (evaluation + lite)

### Non-Existent Variants
- ❌ "Stellar Premium Account"
- ❌ "Stellar Gold Challenge"
- ❌ "Stellar Express"

### Wrong Numbers
- ❌ "Stellar 3-Step Challenge"
- ❌ "Evaluation 1-Step"

### Made-Up Names
- ❌ "Ultra Funding Program"
- ❌ "Elite Trader Challenge"
- ❌ "Pro Account Package"

## Best Practices

### 1. Always Validate LLM Output
```python
# ❌ DON'T: Use LLM output directly
save_to_database(llm_output['challenge_type'])

# ✓ DO: Validate first
program_id = map_alias_to_program(firm_name, llm_output['challenge_type'])
if program_id:
    save_to_database(program_id)
```

### 2. Log Hallucinations
```python
if program_id is None:
    logger.warning(f"LLM hallucination detected: {llm_output}")
    metrics.increment('hallucinations_detected')
```

### 3. Use Strict Mode in Production
```python
# Development: Permissive mode for testing
extractor = ValidatedLLMExtractor("FundedNext", strict=False)

# Production: Strict mode to prevent corruption
extractor = ValidatedLLMExtractor("FundedNext", strict=True)
```

### 4. Validate Before Database Insert
```python
# Validate at the database boundary
def insert_rule(challenge_type, rules):
    program_id = map_alias_to_program(firm_name, challenge_type)
    
    if program_id is None:
        raise ValueError(f"Invalid challenge_type: {challenge_type}")
    
    db.execute("INSERT INTO firm_rule ...", (program_id, ...))
```

### 5. Monitor Hallucination Rates
```python
report = extractor.get_validation_report()

if report['hallucination_rate'] > 0.1:  # > 10%
    alert("High hallucination rate detected!")
    # Consider retraining or adjusting prompts
```

## Extending the Taxonomy

To add new programs:

1. Edit `config/program_taxonomy.json`:
```json
{
  "FundedNext": {
    "official_programs": {
      "stellar_3step": "Stellar 3-Step Challenge"
    },
    "aliases": {
      "stellar 3-step": "stellar_3step",
      "3 step stellar": "stellar_3step"
    }
  }
}
```

2. Validation automatically includes new programs
3. No code changes needed

## Summary

LLM guardrails prevent data corruption by:

✓ **Validating all LLM outputs** against official taxonomy  
✓ **Detecting hallucinations** before they enter the database  
✓ **Providing clear feedback** on invalid program names  
✓ **Supporting fuzzy matching** for common variations  
✓ **Generating reports** on hallucination rates  
✓ **Failing safe** - reject invalid rather than corrupt data  

Key function:
```python
program_id = map_alias_to_program(firm_name, llm_output.lower())
if program_id is None:
    # Hallucination → reject
    pass
```
