"""
Hybrid extraction: Fast pattern matching + LLM for missing values.
"""

import json
from pathlib import Path

from .fast_extractor import extract_rules_from_page, group_by_challenge_type
from .llm_extractor import query_llm


def needs_llm_help(rules, page_title=""):
    """
    Check if page needs LLM assistance based on:
    1. Page is about trading rules (check title/URL)
    2. Missing critical rule data despite being a rules page
    """
    title_lower = page_title.lower()
    
    # Skip FAQ/general pages that aren't about specific rules
    skip_keywords = ['faq', 'general', 'about', 'video', 'kyc', 'withdraw', 'payout', 'infinity points', 
                     'affiliate', 'dashboard', 'features', 'offers', 'promotions', 'refer', 'earn',
                     'slippage', 'fairness', 'transparency', 'merge']
    
    if any(keyword in title_lower for keyword in skip_keywords):
        return False  # These pages don't have trading rules, skip LLM
    
    # Check if this is a rules/challenge page
    rules_keywords = ['rule', 'challenge', 'stellar', 'step', 'lite', 'instant', 
                     'prohibited', 'restricted', 'strategy', 'drawdown', 'loss limit']
    
    is_rules_page = any(keyword in title_lower for keyword in rules_keywords)
    
    if not is_rules_page:
        return False  # Not a rules page, skip LLM
    
    # For rules pages, check if we're missing critical trading data
    has_any_critical_data = (
        rules.get('profit_targets') or
        rules.get('account_sizes') or
        (rules.get('drawdown_limits', {}).get('daily_loss') and 
         rules.get('drawdown_limits', {}).get('max_drawdown'))
    )
    
    # If it's a rules page but we got nothing, use LLM
    if not has_any_critical_data:
        return True
    
    return False


def merge_llm_results(pattern_rules, llm_rules):
    """Merge LLM results into pattern-based results, filling gaps."""
    if not llm_rules:
        return pattern_rules
    
    merged = pattern_rules.copy()
    
    # Fill missing fields with LLM data
    if not merged.get('account_sizes') and llm_rules.get('account_sizes'):
        merged['account_sizes'] = llm_rules['account_sizes']
    
    if not merged.get('profit_targets') and llm_rules.get('profit_targets'):
        merged['profit_targets'] = llm_rules['profit_targets']
    
    if not merged['drawdown_limits'].get('daily_loss') and llm_rules.get('daily_loss_limit'):
        merged['drawdown_limits']['daily_loss'] = [llm_rules['daily_loss_limit']]
    
    if not merged['drawdown_limits'].get('max_drawdown') and llm_rules.get('max_drawdown'):
        merged['drawdown_limits']['max_drawdown'] = [llm_rules['max_drawdown']]
    
    # Merge prohibited strategies
    pattern_prohibited = set(merged.get('prohibited_strategies', []))
    llm_prohibited = set(llm_rules.get('prohibited_strategies', []))
    merged['prohibited_strategies'] = sorted(pattern_prohibited | llm_prohibited)
    
    # Add soft rules if present
    if llm_rules.get('soft_rules'):
        merged['soft_rules'] = llm_rules['soft_rules']
    
    # Add other LLM fields
    if llm_rules.get('profit_split'):
        merged['profit_split'] = llm_rules['profit_split']
    
    if llm_rules.get('min_trading_days'):
        merged['min_trading_days'] = llm_rules['min_trading_days']
    
    if llm_rules.get('leverage'):
        merged['leverage'] = llm_rules['leverage']
    
    return merged


def hybrid_extract(input_file, output_file='output/rules_hybrid.json', model='qwen2.5-coder:14b'):
    """
    Hybrid extraction: Fast patterns first, LLM ONLY for pages with 0 rules or missing critical values.
    
    Workflow:
    1. Run fast pattern extraction on ALL pages
    2. Identify pages with missing/null rules
    3. Use LLM ONLY on those specific pages
    4. Merge results and output JSON
    """
    print("=" * 60)
    print("HYBRID EXTRACTION (Smart LLM Usage)")
    print("=" * 60)
    print("✓ Phase 1: Fast pattern extraction on ALL pages")
    print("✓ Phase 2: LLM ONLY for pages with missing/null rules")
    print("=" * 60 + "\n")
    
    # Load scraped pages
    print(f"Loading scraped pages from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        pages = json.load(f)
    
    all_rules = []
    pages_needing_llm = []
    
    print(f"\n🔍 Phase 1: Pattern extraction on {len(pages)} pages...")
    print("-" * 60)
    
    for idx, page in enumerate(pages, 1):
        title = page.get('title', 'Untitled')
        
        # Fast pattern extraction
        pattern_rules = extract_rules_from_page(page)
        
        # Check if this page needs LLM (only for rules pages with missing data)
        if needs_llm_help(pattern_rules, title):
            pages_needing_llm.append((idx, page, pattern_rules))
            status = "❌ Missing critical rule data"
        else:
            status = "✓ Complete"
        
        print(f"  [{idx}/{len(pages)}] {title[:50]}: {status}")
        all_rules.append(pattern_rules)
    
    # Phase 2: LLM for incomplete pages only
    if pages_needing_llm:
        print(f"\n🤖 Phase 2: LLM extraction for {len(pages_needing_llm)}/{len(pages)} pages...")
        print("-" * 60)
        
        for idx, page, pattern_rules in pages_needing_llm:
            title = page.get('title', 'Untitled')
            text = page.get('body', page.get('html', ''))
            url = page.get('url', '')
            
            print(f"  [{idx}/{len(pages)}] Querying LLM for: {title[:50]}")
            
            llm_result = query_llm(text, model=model)
            
            if llm_result:
                merged_rules = merge_llm_results(pattern_rules, llm_result)
                all_rules[idx - 1] = merged_rules  # Update in place
                print(f"      ✓ LLM filled missing fields")
            else:
                print(f"      ⚠ LLM failed - keeping pattern results")
    else:
        print(f"\n✓ Phase 2: Skipped - all pages have complete rules!")
    
    # Group by challenge type
    print(f"\n📊 Grouping rules by challenge type...")
    grouped_rules = group_by_challenge_type(all_rules)
    
    # Save results
    print(f"💾 Saving results to {output_file}...")
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open('w', encoding='utf-8') as f:
        json.dump(grouped_rules, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 60)
    print("✅ EXTRACTION COMPLETE")
    print("=" * 60)
    print(f"📄 Total pages processed: {len(pages)}")
    print(f"⚡ Pattern-only pages: {len(pages) - len(pages_needing_llm)}")
    print(f"🤖 LLM-assisted pages: {len(pages_needing_llm)} ({len(pages_needing_llm)/len(pages)*100:.1f}%)")
    print(f"🚫 Prohibited strategies: {len(grouped_rules['general_rules']['prohibited_strategies'])}")
    print(f"🎯 Challenge types: {len(grouped_rules['challenge_types'])}")
    print(f"💾 Output: {output_file}")
    print("=" * 60)
    
    return grouped_rules


if __name__ == "__main__":
    import sys
    
    input_file = sys.argv[1] if len(sys.argv) > 1 else "output/scraped_pages.json"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "output/rules_hybrid.json"
    model = sys.argv[3] if len(sys.argv) > 3 else "qwen2.5-coder:14b"
    
    hybrid_extract(input_file, output_file, model)
