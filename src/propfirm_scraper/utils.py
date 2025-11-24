"""
Utility functions for text processing and file handling.
"""

import json
import re
from pathlib import Path


def clean_text(text):
    """Remove excessive whitespace and normalize text."""
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    return text


def extract_numbers(text):
    """Extract all numeric values from text."""
    pattern = r'\d+(?:,\d{3})*(?:\.\d+)?'
    matches = re.findall(pattern, text)
    return [m.replace(',', '') for m in matches]


def extract_percentages(text):
    """Extract all percentage values from text."""
    pattern = r'(\d+(?:\.\d+)?)\s*%'
    matches = re.findall(pattern, text)
    return matches


def save_json(data, filepath, indent=2):
    """Save data to JSON file with proper formatting."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)
    
    print(f"✓ Saved to {filepath}")


def load_json(filepath):
    """Load data from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def normalize_currency(value):
    """Normalize currency string to numeric value."""
    if isinstance(value, (int, float)):
        return value
    
    value = str(value).strip().replace(',', '')
    
    # Handle k/K for thousands
    if value.endswith('k') or value.endswith('K'):
        return int(float(value[:-1]) * 1000)
    
    # Handle m/M for millions
    if value.endswith('m') or value.endswith('M'):
        return int(float(value[:-1]) * 1000000)
    
    # Remove currency symbols
    value = re.sub(r'[$€£¥]', '', value)
    
    try:
        return float(value)
    except ValueError:
        return None


def format_rule_summary(grouped_rules):
    """Format extracted rules into human-readable summary."""
    lines = []
    lines.append("=" * 60)
    lines.append("EXTRACTED RULES SUMMARY")
    lines.append("=" * 60)
    
    # General rules
    lines.append("\n📋 GENERAL RULES")
    lines.append("-" * 60)
    
    prohibited = grouped_rules['general_rules'].get('prohibited_strategies', [])
    if prohibited:
        lines.append(f"Prohibited Strategies ({len(prohibited)}):")
        for strategy in prohibited:
            lines.append(f"  ✗ {strategy}")
    
    # Challenge types
    lines.append("\n🎯 CHALLENGE TYPES")
    lines.append("-" * 60)
    
    for ctype, data in grouped_rules['challenge_types'].items():
        lines.append(f"\n{ctype.upper().replace('_', '-')}:")
        
        if data.get('account_sizes'):
            sizes = ', '.join(f"${s}" for s in data['account_sizes'])
            lines.append(f"  💰 Account Sizes: {sizes}")
        
        if data.get('profit_targets'):
            targets = ', '.join(f"{t}%" for t in data['profit_targets'])
            lines.append(f"  🎯 Profit Targets: {targets}")
        
        if data.get('daily_loss'):
            losses = ', '.join(f"{l}%" for l in data['daily_loss'])
            lines.append(f"  📉 Daily Loss Limit: {losses}")
        
        if data.get('max_drawdown'):
            drawdowns = ', '.join(f"{d}%" for d in data['max_drawdown'])
            lines.append(f"  ⚠️  Max Drawdown: {drawdowns}")
        
        if data.get('sources'):
            lines.append(f"  📄 Sources: {len(data['sources'])} pages")
    
    lines.append("\n" + "=" * 60)
    
    return '\n'.join(lines)


def deduplicate_list(items):
    """Remove duplicates while preserving order."""
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def merge_rule_sets(*rule_sets):
    """Merge multiple rule sets, combining unique values."""
    merged = {
        'general_rules': {
            'prohibited_strategies': set(),
            'payout_rules': {},
        },
        'challenge_types': {}
    }
    
    for rules in rule_sets:
        # Merge general rules
        merged['general_rules']['prohibited_strategies'].update(
            rules.get('general_rules', {}).get('prohibited_strategies', [])
        )
        
        # Merge challenge types
        for ctype, data in rules.get('challenge_types', {}).items():
            if ctype not in merged['challenge_types']:
                merged['challenge_types'][ctype] = {
                    'account_sizes': set(),
                    'profit_targets': set(),
                    'daily_loss': set(),
                    'max_drawdown': set(),
                    'sources': set()
                }
            
            ct_merged = merged['challenge_types'][ctype]
            for key in ['account_sizes', 'profit_targets', 'daily_loss', 'max_drawdown', 'sources']:
                ct_merged[key].update(data.get(key, []))
    
    # Convert sets to sorted lists
    merged['general_rules']['prohibited_strategies'] = sorted(
        merged['general_rules']['prohibited_strategies']
    )
    
    for ctype, data in merged['challenge_types'].items():
        for key in ['account_sizes', 'profit_targets', 'daily_loss', 'max_drawdown']:
            data[key] = sorted(data[key], key=lambda x: float(x) if str(x).replace('.', '').isdigit() else 0)
        data['sources'] = sorted(data['sources'])
    
    return merged
