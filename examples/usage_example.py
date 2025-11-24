"""
Example usage of the propfirm scraper with all three extraction methods.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from propfirm_scraper.scraper import crawl_site
from propfirm_scraper.fast_extractor import extract_all_rules as fast_extract
from propfirm_scraper.llm_extractor import extract_with_llm
from propfirm_scraper.hybrid_extractor import hybrid_extract
from propfirm_scraper.utils import format_rule_summary, load_json


def example_scrape_and_extract(url, firm_name="PropFirm", max_pages=50):
    """
    Complete example: scrape website and extract rules using hybrid method.
    """
    print(f"\n{'='*60}")
    print(f"SCRAPING AND EXTRACTING: {firm_name}")
    print(f"{'='*60}\n")
    
    # Step 1: Scrape the website
    print("STEP 1: Scraping website...")
    scraped_file = f"output/{firm_name.lower().replace(' ', '_')}_scraped.json"
    crawl_site(url, max_pages=max_pages, output_file=scraped_file)
    
    # Step 2: Extract rules using hybrid method (fast + LLM for gaps)
    print("\n\nSTEP 2: Extracting rules (hybrid method)...")
    output_file = f"output/{firm_name.lower().replace(' ', '_')}_rules.json"
    rules = hybrid_extract(scraped_file, output_file)
    
    # Step 3: Display summary
    print("\n\nSTEP 3: Summary")
    print(format_rule_summary(rules))
    
    return rules


def example_fast_only(scraped_file):
    """
    Example: Fast pattern-based extraction only (no LLM).
    Completes in ~2 seconds.
    """
    print("\nExample: Fast Pattern Extraction")
    print("-" * 60)
    
    output_file = scraped_file.replace('.json', '_fast.json')
    rules = fast_extract(scraped_file, output_file)
    
    print(format_rule_summary(rules))
    return rules


def example_llm_only(scraped_file, model='qwen2.5-coder:14b'):
    """
    Example: Full LLM extraction (slow but comprehensive).
    Takes 15-30 minutes depending on model and page count.
    """
    print(f"\nExample: Full LLM Extraction ({model})")
    print("-" * 60)
    
    output_file = scraped_file.replace('.json', '_llm.json')
    rules = extract_with_llm(scraped_file, output_file, model)
    
    return rules


def example_compare_methods(scraped_file):
    """
    Example: Run all three methods and compare results.
    """
    print("\nExample: Comparing Extraction Methods")
    print("=" * 60)
    
    # Fast extraction
    print("\n1. FAST PATTERN-BASED")
    fast_rules = fast_extract(scraped_file, "output/comparison_fast.json")
    
    # Hybrid extraction
    print("\n2. HYBRID (Pattern + LLM)")
    hybrid_rules = hybrid_extract(scraped_file, "output/comparison_hybrid.json")
    
    # Compare
    print("\n" + "=" * 60)
    print("COMPARISON")
    print("=" * 60)
    
    fast_prohibited = len(fast_rules['general_rules']['prohibited_strategies'])
    hybrid_prohibited = len(hybrid_rules['general_rules']['prohibited_strategies'])
    
    print(f"Prohibited Strategies Found:")
    print(f"  Fast:   {fast_prohibited}")
    print(f"  Hybrid: {hybrid_prohibited}")
    
    print(f"\nChallenge Types Detected:")
    print(f"  Fast:   {len(fast_rules['challenge_types'])}")
    print(f"  Hybrid: {len(hybrid_rules['challenge_types'])}")


if __name__ == "__main__":
    # Example 1: Full scrape and extract for FundedNext
    example_scrape_and_extract(
        url="https://help.fundednext.com/en",
        firm_name="FundedNext",
        max_pages=50
    )
    
    # Example 2: Use existing scraped data with fast extraction
    # example_fast_only("output/fundednext_scraped.json")
    
    # Example 3: Compare all methods
    # example_compare_methods("output/fundednext_scraped.json")
