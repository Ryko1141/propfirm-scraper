"""
Validate scraping coverage - find missing articles from help center.
Analyzes collection pages to extract all article URLs and compare with scraped data.
"""

import json
import re
from urllib.parse import urlparse, urljoin, urlunparse
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
import time


def normalize_url(url):
    """Remove query params and fragments, return canonical URL."""
    parsed = urlparse(url)
    # Remove query string and fragment
    canonical = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path.rstrip('/'),  # Remove trailing slash
        '',  # params
        '',  # query
        ''   # fragment
    ))
    return canonical


def extract_article_urls_from_page(page):
    """Extract all article links from a collection page."""
    article_urls = []
    
    try:
        # Find all article links (various possible selectors)
        link_selectors = [
            'a[href*="/articles/"]',
            'a[href*="/en/articles/"]',
            '.article-list a',
            '.collection-content a',
            'article a',
            '[data-testid="article-link"]'
        ]
        
        for selector in link_selectors:
            links = page.locator(selector).all()
            for link in links:
                try:
                    href = link.get_attribute('href')
                    if href and '/articles/' in href:
                        article_urls.append(href)
                except:
                    continue
    except Exception as e:
        print(f"    ⚠ Error extracting links: {e}")
    
    return article_urls


def scrape_collection_page(page, collection_url):
    """Scrape a collection page to get all article URLs."""
    print(f"\n  📂 Scraping collection: {collection_url}")
    
    try:
        page.goto(collection_url, timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        
        article_urls = extract_article_urls_from_page(page)
        
        # Get collection name
        try:
            title = page.title()
            collection_name = title.split('|')[0].strip()
        except:
            collection_name = collection_url.split('/')[-1]
        
        print(f"    ✓ Found {len(article_urls)} article links")
        
        return {
            'collection_name': collection_name,
            'collection_url': collection_url,
            'articles': article_urls
        }
    
    except Exception as e:
        print(f"    ✗ Failed: {e}")
        return None


def discover_all_articles(start_url):
    """
    Discover all articles by:
    1. Finding all collection pages from homepage
    2. Scraping each collection for article links
    """
    USER_PROFILE = "acg_profile"
    expected_articles = {}
    
    with sync_playwright() as pw:
        browser = pw.chromium.launch_persistent_context(
            USER_PROFILE,
            headless=False,
            channel="chrome"
        )
        
        page = browser.new_page()
        stealth = Stealth()
        stealth.apply_stealth_sync(page)
        
        print("🔍 Step 1: Finding all collection pages...")
        page.goto(start_url, timeout=30000, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        
        # Find all collection links
        collection_selectors = [
            'a[href*="/collections/"]',
            '.collection-card a',
            '[data-testid="collection-link"]'
        ]
        
        collection_urls = set()
        for selector in collection_selectors:
            links = page.locator(selector).all()
            for link in links:
                try:
                    href = link.get_attribute('href')
                    if href and '/collections/' in href:
                        full_url = urljoin(start_url, href)
                        collection_urls.add(normalize_url(full_url))
                except:
                    continue
        
        print(f"  ✓ Found {len(collection_urls)} collections")
        
        # Also check for direct article links on homepage
        print("\n🔍 Step 2: Checking homepage for direct article links...")
        homepage_articles = extract_article_urls_from_page(page)
        if homepage_articles:
            expected_articles['_homepage'] = {
                'collection_name': 'Homepage',
                'collection_url': start_url,
                'articles': [urljoin(start_url, url) for url in homepage_articles]
            }
            print(f"  ✓ Found {len(homepage_articles)} articles on homepage")
        
        # Scrape each collection
        print("\n🔍 Step 3: Scraping each collection for articles...")
        for i, coll_url in enumerate(sorted(collection_urls), 1):
            print(f"\n[{i}/{len(collection_urls)}]", end="")
            collection_data = scrape_collection_page(page, coll_url)
            
            if collection_data and collection_data['articles']:
                # Normalize all article URLs
                normalized_articles = [
                    normalize_url(urljoin(start_url, url)) 
                    for url in collection_data['articles']
                ]
                collection_data['articles'] = list(set(normalized_articles))
                
                coll_id = coll_url.split('/')[-1]
                expected_articles[coll_id] = collection_data
            
            time.sleep(1)
        
        browser.close()
    
    return expected_articles


def analyze_coverage(scraped_file, expected_articles):
    """Compare scraped data against expected articles."""
    
    # Load scraped data
    import os
    if not os.path.exists(scraped_file):
        print(f"\n⚠ Scraped file not found: {scraped_file}")
        print(f"   Looking for file in parent directory...")
        parent_file = os.path.join('..', scraped_file)
        if os.path.exists(parent_file):
            scraped_file = parent_file
            print(f"   ✓ Found at: {parent_file}")
        else:
            print(f"\n❌ ERROR: Could not find scraped data file")
            print(f"   Searched locations:")
            print(f"   - {os.path.abspath(scraped_file)}")
            print(f"   - {os.path.abspath(parent_file)}")
            return None
    
    with open(scraped_file, 'r', encoding='utf-8') as f:
        scraped_data = json.load(f)
    
    # Normalize scraped URLs
    scraped_urls = {normalize_url(page['url']): page for page in scraped_data}
    
    print("\n" + "="*70)
    print("📊 COVERAGE ANALYSIS")
    print("="*70)
    
    # Flatten expected articles
    all_expected = {}
    for coll_id, coll_data in expected_articles.items():
        for url in coll_data['articles']:
            all_expected[url] = coll_data['collection_name']
    
    print(f"\n📈 STATS:")
    print(f"   Expected articles: {len(all_expected)}")
    print(f"   Scraped pages: {len(scraped_urls)}")
    
    # Find gaps
    missing = []
    present_empty = []
    present_good = []
    
    for expected_url, collection in all_expected.items():
        if expected_url in scraped_urls:
            scraped_page = scraped_urls[expected_url]
            body_len = len(scraped_page.get('body', ''))
            
            if body_len < 100:
                present_empty.append({
                    'url': expected_url,
                    'collection': collection,
                    'body_length': body_len
                })
            else:
                present_good.append(expected_url)
        else:
            missing.append({
                'url': expected_url,
                'collection': collection
            })
    
    # Coverage by collection
    print(f"\n📦 COVERAGE BY COLLECTION:")
    collection_stats = {}
    for coll_id, coll_data in expected_articles.items():
        coll_name = coll_data['collection_name']
        total = len(coll_data['articles'])
        found = sum(1 for url in coll_data['articles'] if url in scraped_urls)
        collection_stats[coll_name] = (found, total)
        
        status = "✓" if found == total else "⚠" if found > 0 else "✗"
        print(f"   {status} {coll_name}: {found}/{total} ({found/total*100:.1f}%)")
    
    # Summary
    print(f"\n🎯 RESULTS:")
    print(f"   ✓ Found with content: {len(present_good)} ({len(present_good)/len(all_expected)*100:.1f}%)")
    print(f"   ⚠ Found but empty: {len(present_empty)} ({len(present_empty)/len(all_expected)*100:.1f}%)")
    print(f"   ✗ Missing: {len(missing)} ({len(missing)/len(all_expected)*100:.1f}%)")
    
    # Detailed gaps
    if missing:
        print(f"\n🔴 MISSING ARTICLES ({len(missing)}):")
        for item in missing[:20]:  # Show first 20
            print(f"   • [{item['collection']}] {item['url']}")
        if len(missing) > 20:
            print(f"   ... and {len(missing)-20} more")
    
    if present_empty:
        print(f"\n⚠️  EMPTY/SHORT ARTICLES ({len(present_empty)}):")
        for item in present_empty[:10]:
            print(f"   • [{item['collection']}] {item['url']} ({item['body_length']} chars)")
        if len(present_empty) > 10:
            print(f"   ... and {len(present_empty)-10} more")
    
    # Save detailed report
    report = {
        'summary': {
            'expected_total': len(all_expected),
            'scraped_total': len(scraped_urls),
            'found_with_content': len(present_good),
            'found_but_empty': len(present_empty),
            'missing': len(missing),
            'coverage_percent': len(present_good) / len(all_expected) * 100
        },
        'collection_coverage': {
            name: {'found': found, 'total': total, 'percent': found/total*100}
            for name, (found, total) in collection_stats.items()
        },
        'missing_articles': missing,
        'empty_articles': present_empty
    }
    
    report_file = 'output/coverage_report.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Detailed report saved to: {report_file}")
    
    # Generate URLs to re-scrape
    if missing or present_empty:
        rescrape_urls = [item['url'] for item in missing]
        rescrape_urls.extend([item['url'] for item in present_empty])
        
        with open('output/rescrape_urls.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(rescrape_urls))
        
        print(f"📝 URLs to re-scrape saved to: output/rescrape_urls.txt")
    
    return report


def main():
    import sys
    import os
    
    print("="*70)
    print("🔍 PROPFIRM SCRAPER - COVERAGE VALIDATOR")
    print("="*70)
    
    start_url = sys.argv[1] if len(sys.argv) > 1 else "https://help.fundednext.com/en"
    scraped_file = sys.argv[2] if len(sys.argv) > 2 else "c:/Users/sossi/output/fundednext_full.json"
    
    # Try to find the scraped file
    if not os.path.exists(scraped_file):
        alt_paths = [
            "output/fundednext_full.json",
            "../output/fundednext_full.json", 
            "c:/Users/sossi/output/fundednext_full.json"
        ]
        for alt in alt_paths:
            if os.path.exists(alt):
                scraped_file = alt
                break
    
    print(f"\n🌐 Help Center: {start_url}")
    print(f"📄 Scraped Data: {scraped_file}\n")
    
    # Step 1: Discover all expected articles
    print("Phase 1: Discovering all articles from collections...")
    expected_articles = discover_all_articles(start_url)
    
    # Save expected articles
    with open('output/expected_articles.json', 'w', encoding='utf-8') as f:
        json.dump(expected_articles, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Expected articles saved to: output/expected_articles.json")
    
    # Step 2: Analyze coverage
    print("\n" + "="*70)
    print("Phase 2: Analyzing coverage...")
    report = analyze_coverage(scraped_file, expected_articles)
    
    if not report:
        print("\n❌ Coverage analysis failed - scraped file not found")
        return
    
    # Final grade
    coverage = report['summary']['coverage_percent']
    print("\n" + "="*70)
    print("🎓 COVERAGE GRADE")
    print("="*70)
    
    if coverage >= 95:
        grade = "A+ (Excellent)"
    elif coverage >= 90:
        grade = "A (Very Good)"
    elif coverage >= 80:
        grade = "B (Good)"
    elif coverage >= 70:
        grade = "C (Fair)"
    else:
        grade = "D (Needs Improvement)"
    
    print(f"Coverage: {coverage:.1f}%")
    print(f"Grade: {grade}")
    print("="*70)


if __name__ == "__main__":
    main()
