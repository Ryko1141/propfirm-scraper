"""
Fast pattern-based rule extraction from scraped HTML.
"""

import json
from pathlib import Path

from .extractors import (
    extract_account_sizes,
    extract_profit_targets,
    extract_drawdown_limits,
    extract_prohibited_strategies,
    extract_profit_split,
    extract_min_trading_days,
    extract_leverage,
    identify_challenge_type
)


def extract_rules_from_page(page_data):
    """Extract all possible rules from a single page using regex patterns."""
    text = page_data.get("body", page_data.get("html", ""))
    title = page_data.get("title", "")
    url = page_data.get("url", "")
    
    rules = {
        'source': url,
        'title': title,
        'challenge_types': identify_challenge_type(text, title, url),
        'account_sizes': extract_account_sizes(text),
        'profit_targets': extract_profit_targets(text),
        'drawdown_limits': extract_drawdown_limits(text),
        'prohibited_strategies': extract_prohibited_strategies(text),
        'profit_split': extract_profit_split(text),
        'min_trading_days': extract_min_trading_days(text),
        'leverage': extract_leverage(text),
    }
    
    return rules


def group_by_challenge_type(all_rules):
    """Group extracted rules by challenge type."""
    grouped = {
        'general_rules': {
            'prohibited_strategies': set(),
            'payout_rules': {},
        },
        'challenge_types': {}
    }
    
    for rule in all_rules:
        challenge_types = rule['challenge_types']
        
        # Add prohibited strategies to general (they apply to all)
        if rule['prohibited_strategies']:
            grouped['general_rules']['prohibited_strategies'].update(
                rule['prohibited_strategies']
            )
        
        # Group specific rules by challenge type
        for ctype in challenge_types:
            if ctype not in grouped['challenge_types']:
                grouped['challenge_types'][ctype] = {
                    'account_sizes': set(),
                    'profit_targets': set(),
                    'daily_loss': set(),
                    'max_drawdown': set(),
                    'sources': set()
                }
            
            ct_data = grouped['challenge_types'][ctype]
            ct_data['account_sizes'].update(rule['account_sizes'])
            ct_data['profit_targets'].update(rule['profit_targets'])
            ct_data['daily_loss'].update(rule['drawdown_limits']['daily_loss'])
            ct_data['max_drawdown'].update(rule['drawdown_limits']['max_drawdown'])
            ct_data['sources'].add(rule['source'])
    
    # Convert sets to sorted lists
    grouped['general_rules']['prohibited_strategies'] = sorted(
        grouped['general_rules']['prohibited_strategies']
    )
    
    for ctype, data in grouped['challenge_types'].items():
        for key in ['account_sizes', 'profit_targets', 'daily_loss', 'max_drawdown']:
            data[key] = sorted(data[key], key=lambda x: float(x) if x.replace('.', '').isdigit() else 0)
        data['sources'] = sorted(data['sources'])
    
    return grouped


def extract_all_rules(input_file, output_file='output/rules_fast.json'):
    """Run fast pattern-based extraction on all pages."""
    print("Loading scraped pages...")
    with open(input_file, 'r', encoding='utf-8') as f:
        pages = json.load(f)
    
    all_rules = []
    print(f"Extracting rules from {len(pages)} pages...")
    
    for idx, page in enumerate(pages, 1):
        print(f"  Processing page {idx}/{len(pages)}: {page.get('title', 'Untitled')}")
        rules = extract_rules_from_page(page)
        all_rules.append(rules)
    
    print("\nGrouping rules by challenge type...")
    grouped_rules = group_by_challenge_type(all_rules)
    
    # Save output
    print(f"Saving results to {output_file}...")
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open('w', encoding='utf-8') as f:
        json.dump(grouped_rules, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Extracted {len(all_rules)} rule sets")
    print(f"✓ Found {len(grouped_rules['general_rules']['prohibited_strategies'])} prohibited strategies")
    print(f"✓ Identified {len(grouped_rules['challenge_types'])} challenge types")
    
    return grouped_rules


if __name__ == "__main__":
    import sys
    
    input_file = sys.argv[1] if len(sys.argv) > 1 else "output/scraped_pages.json"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "output/rules_fast.json"
    
    extract_all_rules(input_file, output_file)
