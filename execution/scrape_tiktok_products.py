#!/usr/bin/env python3
"""
Scrape trending TikTok Shop products using Apify's salmanrajz/trending-products-scraper actor.
"""

import os
import sys
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv
from apify_client import ApifyClient

# Load environment variables
load_dotenv()

def scrape_products(category, max_items=20):
    """
    Run the Apify actor to scrape trending TikTok Shop products.
    Returns a list of product dicts or None on failure.
    """
    api_token = os.getenv("APIFY_API_TOKEN")
    if not api_token:
        print("Error: APIFY_API_TOKEN not found in .env", file=sys.stderr)
        return None

    client = ApifyClient(api_token)

    # Prepare the actor input
    run_input = {
        "category": category,
        "maxItems": int(max_items),
    }

    print(f"Starting TikTok product scrape for category '{category}' (Limit: {max_items})...")
    print(f"Debug: run_input = {json.dumps(run_input, indent=2)}")

    try:
        # Run the actor and wait for it to finish
        run = client.actor("salmanrajz/trending-products-scraper").call(run_input=run_input)
    except Exception as e:
        print(f"Error running actor: {e}", file=sys.stderr)
        return None

    if not run:
        print("Error: Actor run failed to start", file=sys.stderr)
        return None

    print(f"Scrape finished. Fetching results from dataset {run['defaultDatasetId']}...")

    # Fetch results from the actor's default dataset
    results = []
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        results.append(item)

    return results

def save_results(results, prefix="tiktok_products"):
    """
    Save results to a JSON file in .tmp/.
    Returns the filepath or None if no results.
    """
    if not results:
        print("No results to save.")
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = ".tmp"
    os.makedirs(output_dir, exist_ok=True)

    filename = f"{output_dir}/{prefix}_{timestamp}.json"

    with open(filename, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Results saved to {filename}")
    return filename

def main():
    parser = argparse.ArgumentParser(description="Scrape trending TikTok Shop products using Apify")
    parser.add_argument("--category", required=True, help="Product category to search (e.g., 'beauty', 'electronics')")
    parser.add_argument("--max_items", type=int, default=20, help="Maximum number of products to fetch")
    parser.add_argument("--output_prefix", default="tiktok_products", help="Prefix for the output file")

    args = parser.parse_args()

    results = scrape_products(args.category, args.max_items)

    if results:
        print(f"Found {len(results)} products.")
        save_results(results, prefix=args.output_prefix)
    else:
        print("No products found or error occurred.")
        sys.exit(1)

if __name__ == "__main__":
    main()
