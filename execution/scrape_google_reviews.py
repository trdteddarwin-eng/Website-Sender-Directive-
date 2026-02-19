#!/usr/bin/env python3
"""
Scrape Google Maps reviews using Playwright headless Chromium.
Extracts rating, reviews, address, and categories — zero cost.

Replaces the old Apify-based scraper.

Usage:
    python3 execution/scrape_google_reviews.py \
        --business_name "ABC Plumbing" \
        --location "Austin, TX" \
        --max_reviews 5 \
        --output .tmp/reviews.json

    # Or with a direct Google Maps URL:
    python3 execution/scrape_google_reviews.py \
        --url "https://www.google.com/maps/place/ABC+Plumbing" \
        --max_reviews 10 \
        --output .tmp/reviews.json
"""

import os
import sys
import json
import re
import argparse
import time
from datetime import datetime
from collections import Counter
from typing import Union


def scrape_reviews(
    business_name: str = None,
    location: str = None,
    url: str = None,
    max_reviews: int = 5,
    timeout: int = 30000,
) -> dict:
    """
    Scrape Google Maps reviews using Playwright.

    Args:
        business_name: Name of the business to search for
        location: Location (e.g., "Austin, TX")
        url: Direct Google Maps URL (alternative to business_name + location)
        max_reviews: Maximum number of reviews to scrape (default: 5)
        timeout: Page load timeout in ms

    Returns:
        Dictionary with business info, reviews, and analysis
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Error: playwright not installed. Run: pip install playwright && python3 -m playwright install chromium", file=sys.stderr)
        return None

    # Build search URL
    if url:
        start_url = url
    elif business_name and location:
        search_query = f"{business_name} {location}".replace(" ", "+")
        start_url = f"https://www.google.com/maps/search/{search_query}"
    else:
        print("Error: Must provide either --url or both --business_name and --location", file=sys.stderr)
        return None

    print(f"Scraping Google reviews...")
    print(f"  URL: {start_url}")
    print(f"  Max reviews: {max_reviews}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1440, "height": 900},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="en-US",
            )
            page = context.new_page()

            page.goto(start_url, wait_until="domcontentloaded", timeout=timeout)
            page.wait_for_timeout(3000)

            # Handle Google consent dialog
            try:
                consent_btn = page.locator('button:has-text("Accept all")')
                if consent_btn.count() > 0:
                    consent_btn.first.click()
                    page.wait_for_timeout(2000)
            except Exception:
                pass

            # If this was a search, click the first result
            try:
                first_result = page.locator('[role="feed"] a[href*="/maps/place/"]')
                if first_result.count() > 0:
                    first_result.first.click()
                    page.wait_for_timeout(3000)
            except Exception:
                pass

            # Extract business info from the place panel
            biz_info = page.evaluate("""() => {
                const info = {
                    name: '',
                    address: '',
                    rating: null,
                    total_reviews: 0,
                    categories: [],
                    phone: '',
                    website: '',
                    hours: '',
                };

                // Business name
                const nameEl = document.querySelector('h1');
                if (nameEl) info.name = nameEl.textContent.trim();

                // Rating
                const ratingEl = document.querySelector('[role="img"][aria-label*="star"]');
                if (ratingEl) {
                    const match = ratingEl.getAttribute('aria-label').match(/([\d.]+)/);
                    if (match) info.rating = parseFloat(match[1]);
                }

                // Total reviews count
                const reviewCountEls = document.querySelectorAll('button[aria-label*="review"]');
                reviewCountEls.forEach(el => {
                    const match = el.textContent.match(/([\d,]+)\s*review/i);
                    if (match) info.total_reviews = parseInt(match[1].replace(',', ''));
                });
                // Fallback: look in aria-labels
                if (!info.total_reviews) {
                    const allEls = document.querySelectorAll('[aria-label*="review"]');
                    allEls.forEach(el => {
                        const match = (el.getAttribute('aria-label') || '').match(/([\d,]+)\s*review/i);
                        if (match) info.total_reviews = parseInt(match[1].replace(',', ''));
                    });
                }

                // Address
                const addressEls = document.querySelectorAll('[data-item-id="address"] .fontBodyMedium, button[data-item-id="address"]');
                addressEls.forEach(el => {
                    const text = el.textContent.trim();
                    if (text && text.length > 5) info.address = text;
                });

                // Categories
                const catEls = document.querySelectorAll('button[jsaction*="category"]');
                catEls.forEach(el => {
                    const text = el.textContent.trim();
                    if (text) info.categories.push(text);
                });

                // Phone
                const phoneEls = document.querySelectorAll('[data-item-id*="phone"] .fontBodyMedium, button[data-item-id*="phone"]');
                phoneEls.forEach(el => {
                    const text = el.textContent.trim();
                    if (text && /[\d\-\(\)\+]/.test(text)) info.phone = text;
                });

                // Website
                const webEls = document.querySelectorAll('[data-item-id="authority"] .fontBodyMedium, a[data-item-id="authority"]');
                webEls.forEach(el => {
                    const text = (el.getAttribute('href') || el.textContent).trim();
                    if (text && text.includes('.')) info.website = text;
                });

                return info;
            }""")

            print(f"  Business: {biz_info.get('name', 'Unknown')}")
            print(f"  Rating: {biz_info.get('rating', 'N/A')}")
            print(f"  Total reviews: {biz_info.get('total_reviews', 0)}")

            # Click the reviews tab/button to open reviews
            reviews = []
            try:
                # Try clicking "Reviews" tab
                reviews_tab = page.locator('button[role="tab"]:has-text("Reviews"), button[aria-label*="Review"]')
                if reviews_tab.count() > 0:
                    reviews_tab.first.click()
                    page.wait_for_timeout(2000)

                # Scroll the reviews panel to load more
                reviews_panel = page.locator('[role="feed"], .m6QErb.DxyBCb')
                if reviews_panel.count() > 0:
                    panel = reviews_panel.first
                    for _ in range(min(max_reviews // 3 + 1, 10)):
                        panel.evaluate("el => el.scrollTop = el.scrollHeight")
                        page.wait_for_timeout(1500)

                # Expand "More" buttons on reviews
                try:
                    more_buttons = page.locator('button.w8nwRe, button:has-text("More")')
                    for i in range(min(more_buttons.count(), max_reviews)):
                        try:
                            more_buttons.nth(i).click()
                            page.wait_for_timeout(300)
                        except Exception:
                            pass
                except Exception:
                    pass

                # Extract reviews
                reviews = page.evaluate("""(maxReviews) => {
                    const reviews = [];
                    const reviewEls = document.querySelectorAll('[data-review-id], .jftiEf');

                    for (let i = 0; i < Math.min(reviewEls.length, maxReviews); i++) {
                        const el = reviewEls[i];
                        const review = {
                            text: '',
                            rating: null,
                            reviewer: 'Anonymous',
                            date: '',
                        };

                        // Reviewer name
                        const nameEl = el.querySelector('.d4r55, button[aria-label]');
                        if (nameEl) {
                            review.reviewer = (nameEl.getAttribute('aria-label') || nameEl.textContent || '').trim();
                        }

                        // Rating
                        const starEl = el.querySelector('[role="img"][aria-label*="star"]');
                        if (starEl) {
                            const match = starEl.getAttribute('aria-label').match(/(\\d)/);
                            if (match) review.rating = parseInt(match[1]);
                        }

                        // Date
                        const dateEl = el.querySelector('.rsqaWe');
                        if (dateEl) review.date = dateEl.textContent.trim();

                        // Review text
                        const textEl = el.querySelector('.wiI7pd, .MyEned');
                        if (textEl) review.text = textEl.textContent.trim();

                        if (review.text || review.rating) {
                            reviews.push(review);
                        }
                    }
                    return reviews;
                }""", max_reviews)

            except Exception as e:
                print(f"  Warning: Could not load reviews: {e}", file=sys.stderr)

            browser.close()

    except Exception as e:
        print(f"Browser error: {e}", file=sys.stderr)
        return {
            "business_name": business_name or "Unknown",
            "location": location or "",
            "reviews_found": 0,
            "average_rating": None,
            "reviews": [],
            "common_complaints": [],
            "address": "",
            "categories": [],
            "phone": "",
            "website": "",
            "error": str(e),
        }

    # Build result
    ratings = [r["rating"] for r in reviews if r.get("rating") is not None]
    average_rating = biz_info.get("rating") or (round(sum(ratings) / len(ratings), 1) if ratings else None)
    common_complaints = extract_complaints(reviews)

    result = {
        "business_name": biz_info.get("name") or business_name or "Unknown",
        "location": biz_info.get("address") or location or "",
        "address": biz_info.get("address", ""),
        "categories": biz_info.get("categories", []),
        "phone": biz_info.get("phone", ""),
        "website": biz_info.get("website", ""),
        "reviews_found": len(reviews),
        "total_reviews": biz_info.get("total_reviews", len(reviews)),
        "average_rating": average_rating,
        "reviews": reviews,
        "common_complaints": common_complaints,
    }

    print(f"  Extracted {len(reviews)} reviews. Average rating: {average_rating}")
    return result


def extract_complaints(reviews: list) -> list:
    """
    Extract common complaints from lower-rated reviews (1-3 stars).
    """
    complaint_keywords = [
        "slow", "late", "expensive", "rude", "unprofessional", "dirty",
        "wait", "waited", "waiting", "delay", "delayed",
        "price", "overpriced", "costly", "overcharged",
        "poor", "bad", "terrible", "awful", "worst",
        "response", "communication", "return call", "never called",
        "scheduling", "appointment", "canceled", "cancelled",
        "quality", "shoddy", "cheap", "broken",
        "customer service", "attitude", "disrespectful",
        "mess", "messy", "clean", "cleanup",
        "no-show", "no show", "didn't show", "stood up",
    ]

    complaint_counts = Counter()
    for review in reviews:
        rating = review.get("rating")
        text = (review.get("text") or "").lower()
        if rating is not None and rating <= 3 and text:
            for keyword in complaint_keywords:
                if keyword in text:
                    complaint_counts[keyword] += 1

    return [keyword for keyword, count in complaint_counts.most_common(5)]


def save_results(results: Union[dict, list], output_path: str) -> str:
    """Save results to a JSON file."""
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Results saved to {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Scrape Google Maps reviews using Playwright",
        epilog="Either provide --url OR both --business_name and --location"
    )
    parser.add_argument("--business_name", help="Name of the business to search for")
    parser.add_argument("--location", help="Location of the business (e.g., 'Austin, TX')")
    parser.add_argument("--url", help="Direct Google Maps URL")
    parser.add_argument("--max_reviews", type=int, default=5, help="Maximum reviews to scrape (default: 5)")
    parser.add_argument("--output", required=True, help="Output JSON file path")
    parser.add_argument("--timeout", type=int, default=30000, help="Page load timeout in ms (default: 30000)")

    args = parser.parse_args()

    if not args.url and not (args.business_name and args.location):
        parser.error("Must provide either --url OR both --business_name and --location")

    results = scrape_reviews(
        business_name=args.business_name,
        location=args.location,
        url=args.url,
        max_reviews=args.max_reviews,
        timeout=args.timeout,
    )

    if results:
        save_results(results, args.output)
        print(f"\nSummary:")
        print(f"  Business: {results['business_name']}")
        print(f"  Location: {results['location']}")
        print(f"  Reviews found: {results['reviews_found']}")
        print(f"  Average rating: {results['average_rating']}")
        if results['common_complaints']:
            print(f"  Common complaints: {', '.join(results['common_complaints'])}")
    else:
        print("Failed to scrape reviews.")
        sys.exit(1)


if __name__ == "__main__":
    main()
