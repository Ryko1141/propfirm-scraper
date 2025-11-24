"""
Main web scraper with Cloudflare bypass capabilities.
Uses Playwright with stealth mode to scrape prop firm help centers.
"""

import json
import time
from urllib.parse import urljoin, urlparse
from collections import deque
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth


def scrape_page(page):
    """Extract title and full HTML content from page."""
    title = page.title()
    try:
        # Try to get main content wrapper
        main_content = page.locator("main, article, [role='main'], .content, #content").first
        body = main_content.inner_text()
    except:
        # Fallback to body text
        body = page.locator("body").inner_text()
    
    return title, body


def crawl_site(start_url, max_pages=200, output_file="output/scraped_pages.json"):
    """
    Crawl prop firm website starting from given URL.
    
    Args:
        start_url: Starting URL (e.g., help center homepage)
        max_pages: Maximum number of pages to scrape (default: 200)
        output_file: Path to save scraped data
    
    Returns:
        List of dictionaries containing url, title, and body
    """
    USER_PROFILE = "acg_profile"
    
    parsed = urlparse(start_url)
    domain = parsed.netloc
    
    visited = set()
    queue = deque([start_url])
    results = []
    
    with sync_playwright() as pw:
        # Launch persistent browser with stealth
        browser = pw.chromium.launch_persistent_context(
            USER_PROFILE,
            headless=False,  # Show browser for Cloudflare solving
            channel="chrome",  # Use real Chrome
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            )
        )
        
        page = browser.new_page()
        stealth = Stealth()
        stealth.apply_stealth_sync(page)
        
        while queue and len(results) < max_pages:
            url = queue.popleft()
            
            if url in visited:
                continue
            visited.add(url)
            
            print(f"[{len(results)+1}/{max_pages}] Loading {url}")
            
            try:
                page.goto(url, timeout=30000, wait_until="domcontentloaded")
                page.wait_for_timeout(2000)
            except Exception as e:
                print(f"[WARN] Could not load page: {e}")
                continue
            
            title, body = scrape_page(page)
            
            # Detect Cloudflare block
            if "Just a moment" in title or "Verifying you are human" in body:
                print(f"[BLOCKED] Cloudflare challenge - solve manually in browser")
                continue
            
            results.append({
                "url": url,
                "title": title,
                "body": body
            })
            
            # Find new links
            links = page.locator("a[href]").all()
            for link in links:
                href = link.get_attribute("href")
                if not href:
                    continue
                
                full = urljoin(url, href)
                parsed_link = urlparse(full)
                
                # Same domain only
                if parsed_link.netloc != domain:
                    continue
                
                # Ignore file extensions
                if any(full.lower().endswith(ext) for ext in
                       [".png", ".jpg", ".jpeg", ".svg", ".css", ".js", ".pdf", ".ico"]):
                    continue
                
                if full not in visited:
                    queue.append(full)
            
            time.sleep(1)
        
        browser.close()
    
    # Save results
    print(f"\n💾 Saving {len(results)} pages to {output_file}...")
    import os
    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Scraping complete! Saved to {output_file}")
    return results


def main():
    """Main entry point for scraper."""
    import sys
    
    print("=== PropFirm Scraper (Cloudflare-Proof) ===\n")
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        start_url = sys.argv[1]
        max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else 200
        output_file = sys.argv[3] if len(sys.argv) > 3 else "output/scraped_pages.json"
    else:
        start_url = input("Enter prop firm help center URL: ").strip()
        
        if not start_url.startswith("http"):
            print("❌ Invalid URL. Must start with http:// or https://")
            return
        
        max_pages = input("Max pages to scrape (default 200): ").strip()
        max_pages = int(max_pages) if max_pages.isdigit() else 200
        output_file = "output/scraped_pages.json"
    
    print(f"\n🚀 Starting scrape of {start_url}")
    print(f"📄 Will scrape up to {max_pages} pages\n")
    
    data = crawl_site(start_url, max_pages=max_pages, output_file=output_file)
    
    print(f"\n📋 Preview of first 3 pages:")
    for page in data[:3]:
        print(f"  • {page['title']}")
        print(f"    {page['url']}")


if __name__ == "__main__":
    main()
