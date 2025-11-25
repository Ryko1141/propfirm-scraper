"""
Re-scrape missing articles from coverage gap analysis.
Reads rescrape_urls.txt and scrapes only those specific URLs.
"""

import json
import time
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth


def scrape_missing_articles(url_file, existing_file, output_file):
    """Scrape missing URLs and merge with existing data."""
    
    # Load missing URLs
    with open(url_file, 'r', encoding='utf-8') as f:
        missing_urls = [line.strip() for line in f if line.strip()]
    
    print("="*70)
    print("🔄 RE-SCRAPING MISSING ARTICLES")
    print("="*70)
    print(f"\n📋 Missing URLs: {len(missing_urls)}")
    print(f"📄 Existing data: {existing_file}")
    print(f"💾 Output: {output_file}\n")
    
    # Load existing data
    try:
        with open(existing_file, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        print(f"✓ Loaded {len(existing_data)} existing pages")
    except:
        existing_data = []
        print("⚠ No existing data found, starting fresh")
    
    # Create URL set for deduplication
    existing_urls = {page['url'] for page in existing_data}
    
    # Scrape missing articles
    USER_PROFILE = "acg_profile"
    new_articles = []
    failed = []
    
    with sync_playwright() as pw:
        browser = pw.chromium.launch_persistent_context(
            USER_PROFILE,
            headless=False,
            channel="chrome"
        )
        
        page = browser.new_page()
        stealth = Stealth()
        stealth.apply_stealth_sync(page)
        
        print(f"\n🔍 Scraping {len(missing_urls)} missing articles...\n")
        
        for i, url in enumerate(missing_urls, 1):
            print(f"[{i}/{len(missing_urls)}] {url}")
            
            try:
                # Navigate to page
                page.goto(url, timeout=30000, wait_until="domcontentloaded")
                page.wait_for_timeout(2000)
                
                # Extract content
                title = page.title()
                
                # Get main content
                try:
                    main_content = page.locator("main, article, [role='main'], .content, #content").first
                    body = main_content.inner_text()
                except:
                    body = page.locator("body").inner_text()
                
                # Check for Cloudflare block
                if "Just a moment" in title or "Verifying you are human" in body:
                    print(f"   ⚠ Cloudflare blocked - solve captcha manually")
                    page.wait_for_timeout(10000)  # Wait for manual solve
                    
                    # Retry
                    title = page.title()
                    try:
                        main_content = page.locator("main, article, [role='main']").first
                        body = main_content.inner_text()
                    except:
                        body = page.locator("body").inner_text()
                
                if len(body) > 100:
                    new_articles.append({
                        'url': url,
                        'title': title,
                        'body': body
                    })
                    print(f"   ✓ Scraped ({len(body)} chars)")
                else:
                    failed.append(url)
                    print(f"   ✗ Empty content")
                
            except Exception as e:
                failed.append(url)
                print(f"   ✗ Error: {e}")
            
            # Rate limiting
            time.sleep(1.5)
            
            # Save progress every 20 pages
            if i % 20 == 0:
                print(f"\n   💾 Saving progress ({len(new_articles)} new articles)...\n")
                merged = existing_data + new_articles
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(merged, f, indent=2, ensure_ascii=False)
        
        browser.close()
    
    # Final merge and save
    print("\n" + "="*70)
    print("📊 RE-SCRAPE RESULTS")
    print("="*70)
    print(f"✓ Successfully scraped: {len(new_articles)}")
    print(f"✗ Failed: {len(failed)}")
    print(f"📄 Total pages: {len(existing_data) + len(new_articles)}")
    
    merged_data = existing_data + new_articles
    
    # Remove duplicates based on URL
    seen_urls = set()
    deduplicated = []
    for page in merged_data:
        if page['url'] not in seen_urls:
            seen_urls.add(page['url'])
            deduplicated.append(page)
    
    if len(deduplicated) < len(merged_data):
        print(f"⚠ Removed {len(merged_data) - len(deduplicated)} duplicates")
    
    print(f"\n💾 Saving {len(deduplicated)} total pages to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(deduplicated, f, indent=2, ensure_ascii=False)
    
    if failed:
        print(f"\n⚠ {len(failed)} URLs failed:")
        with open('output/failed_urls.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(failed))
        print(f"   Failed URLs saved to: output/failed_urls.txt")
    
    print("="*70)
    print("✅ RE-SCRAPE COMPLETE")
    print("="*70)
    
    return deduplicated


if __name__ == "__main__":
    import sys
    
    url_file = sys.argv[1] if len(sys.argv) > 1 else "output/rescrape_urls.txt"
    existing_file = sys.argv[2] if len(sys.argv) > 2 else "c:/Users/sossi/output/fundednext_full.json"
    output_file = sys.argv[3] if len(sys.argv) > 3 else "c:/Users/sossi/output/fundednext_complete.json"
    
    scrape_missing_articles(url_file, existing_file, output_file)
