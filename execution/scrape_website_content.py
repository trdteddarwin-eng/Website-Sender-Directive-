#!/usr/bin/env python3
"""
Scrape website content using Playwright headless Chromium.
Extracts services, about page, team info, and contact details.

Replaces the old Apify-based scraper — runs locally, zero cost.

Usage:
    python3 execution/scrape_website_content.py \
        --url "https://example-hvac.com" \
        --max_pages 5 \
        --output .tmp/acme-hvac/website_data.json
"""

import os
import sys
import json
import re
import argparse
from datetime import datetime
from urllib.parse import urljoin, urlparse


def scrape_website(url, max_pages=5, timeout=30000):
    """
    Scrape a website using Playwright headless Chromium.

    Args:
        url: Website URL to scrape
        max_pages: Maximum pages to crawl (default 5)
        timeout: Page load timeout in ms (default 30000)

    Returns:
        dict with extracted content or None on error
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Error: playwright not installed. Run: pip install playwright && python3 -m playwright install chromium", file=sys.stderr)
        return None

    pages = []
    visited = set()
    to_visit = [url]
    base_domain = urlparse(url).netloc

    print(f"Scraping website: {url} (max {max_pages} pages)...")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1440, "height": 900},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )

            while to_visit and len(pages) < max_pages:
                current_url = to_visit.pop(0)
                normalized = current_url.rstrip("/").lower()
                if normalized in visited:
                    continue
                visited.add(normalized)

                try:
                    page = context.new_page()
                    response = page.goto(current_url, wait_until="domcontentloaded", timeout=timeout)

                    if not response or response.status >= 400:
                        print(f"  Skipped (HTTP {response.status if response else 'no response'}): {current_url}")
                        page.close()
                        continue

                    # Wait for content to settle
                    page.wait_for_timeout(2000)

                    # Extract page title
                    title = page.title() or ""

                    # Extract main text content (strip nav, footer, scripts, styles)
                    text = page.evaluate("""() => {
                        // Remove noise elements
                        const remove = document.querySelectorAll('nav, footer, script, style, noscript, svg, iframe, .cookie-banner, #cookie-notice');
                        remove.forEach(el => el.remove());
                        return document.body ? document.body.innerText.substring(0, 5000) : '';
                    }""")

                    if text.strip():
                        pages.append({
                            "url": current_url,
                            "title": title,
                            "text": text[:5000],
                        })
                        print(f"  Scraped ({len(pages)}/{max_pages}): {title or current_url}")

                    # Collect internal links for crawling
                    if len(pages) < max_pages:
                        links = page.evaluate("""(baseDomain) => {
                            const links = [];
                            document.querySelectorAll('a[href]').forEach(a => {
                                try {
                                    const url = new URL(a.href, window.location.origin);
                                    if (url.hostname === baseDomain && url.protocol.startsWith('http')) {
                                        links.push(url.href.split('#')[0]);
                                    }
                                } catch(e) {}
                            });
                            return [...new Set(links)];
                        }""", base_domain)

                        # Prioritize service/about/contact pages
                        priority_keywords = ["service", "about", "contact", "team", "our-work", "what-we-do"]
                        priority_links = []
                        other_links = []
                        for link in links:
                            link_lower = link.lower()
                            if link_lower.rstrip("/") not in visited:
                                if any(kw in link_lower for kw in priority_keywords):
                                    priority_links.append(link)
                                else:
                                    other_links.append(link)
                        to_visit.extend(priority_links + other_links[:10])

                    page.close()

                except Exception as e:
                    print(f"  Error on {current_url}: {e}", file=sys.stderr)
                    try:
                        page.close()
                    except Exception:
                        pass
                    continue

            browser.close()

    except Exception as e:
        print(f"Browser error: {e}", file=sys.stderr)
        return None

    if not pages:
        print("Warning: No pages scraped — site may be down or blocking")
        return {
            "url": url,
            "pages_scraped": 0,
            "raw_pages": [],
            "summary": "",
            "services": [],
            "about": "",
            "contact_info": "",
            "error": str(e) if 'e' in dir() else "No pages loaded",
        }

    return process_website_content(pages, url)


def process_website_content(pages, original_url):
    """
    Process scraped pages to extract structured business info.
    """
    result = {
        "url": original_url,
        "pages_scraped": len(pages),
        "raw_pages": pages,
        "summary": "",
        "services": [],
        "about": "",
        "contact_info": "",
    }

    # Combine all text for summary
    all_text = "\n\n".join([
        f"[{p['title']}]\n{p['text']}" for p in pages
    ])
    result["summary"] = all_text[:10000]

    # Try to identify services and about content from page titles/URLs
    for page in pages:
        title_lower = page.get("title", "").lower()
        url_lower = page.get("url", "").lower()

        if any(kw in title_lower or kw in url_lower for kw in ["service", "what we do", "our work"]):
            result["services"].append(page.get("text", "")[:2000])

        if any(kw in title_lower or kw in url_lower for kw in ["about", "our story", "who we are", "team"]):
            result["about"] = page.get("text", "")[:2000]

        if any(kw in title_lower or kw in url_lower for kw in ["contact", "get in touch", "reach us"]):
            result["contact_info"] = page.get("text", "")[:1000]

    return result


def save_result(result, output_path=None):
    """Save result to JSON file."""
    if not result:
        return None

    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs(".tmp", exist_ok=True)
        output_path = f".tmp/website_data_{timestamp}.json"

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Saved to: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Scrape website content using Playwright")
    parser.add_argument("--url", required=True, help="Website URL to scrape")
    parser.add_argument("--max_pages", type=int, default=5, help="Max pages to crawl (default: 5)")
    parser.add_argument("--output", help="Output JSON file path")
    parser.add_argument("--timeout", type=int, default=30000, help="Page load timeout in ms (default: 30000)")

    args = parser.parse_args()

    result = scrape_website(args.url, args.max_pages, args.timeout)

    if result:
        save_result(result, args.output)
        print(f"Success! Scraped {result['pages_scraped']} pages from {args.url}")
    else:
        print("Failed to scrape website.")
        sys.exit(1)


if __name__ == "__main__":
    main()
