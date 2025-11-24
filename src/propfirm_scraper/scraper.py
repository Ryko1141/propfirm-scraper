"""
Main web scraper with Cloudflare bypass capabilities.
Uses Playwright with stealth mode to scrape prop firm help centers.
"""

import json
import time
from collections import deque
from pathlib import Path
from urllib.parse import urljoin, urlparse

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
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

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

    with output_path.open('w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(results)} pages to {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Crawl a prop firm help center and save page content.")
    parser.add_argument("start_url", help="Starting URL (e.g., help center homepage)")
    parser.add_argument("--max-pages", type=int, default=200, dest="max_pages", help="Maximum number of pages to scrape")
    parser.add_argument("--output", default="output/scraped_pages.json", help="Path to save scraped data")

    args = parser.parse_args()
    crawl_site(args.start_url, max_pages=args.max_pages, output_file=args.output)
