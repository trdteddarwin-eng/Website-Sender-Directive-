#!/usr/bin/env python3
"""
Combine website data + reviews data + AI analysis + lead data into a single research.json.

Usage:
    python3 execution/combine_research.py \
        --lead_json '{"first_name":"Clint","company_name":"United Mechanical",...}' \
        --website .tmp/united-mechanical/website_data.json \
        --reviews .tmp/united-mechanical/reviews_data.json \
        --analysis .tmp/united-mechanical/analysis.json \
        --output .tmp/united-mechanical/research.json
"""

import os
import sys
import json
import argparse


def load_json_safe(path):
    """Load JSON file, return empty dict if missing or invalid."""
    if not path or not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load {path}: {e}", file=sys.stderr)
        return {}


def combine_research(lead_data, website_path, reviews_path, analysis_path, output_path):
    """
    Merge all data sources into a single research.json.

    Args:
        lead_data: dict with lead info (from ranked JSON)
        website_path: path to website_data.json
        reviews_path: path to reviews_data.json
        analysis_path: path to analysis.json
        output_path: where to write research.json

    Returns:
        dict with combined research data
    """
    website = load_json_safe(website_path)
    reviews = load_json_safe(reviews_path)
    analysis = load_json_safe(analysis_path)

    # Determine website status
    pages_scraped = website.get("pages_scraped", 0)
    if pages_scraped > 0:
        website_status = "live"
    elif website.get("error"):
        website_status = f"down - {website['error'][:50]}"
    else:
        website_status = "down - no pages loaded"

    # Extract services from multiple sources
    services = []
    # From website scrape
    ws_services = website.get("services", [])
    if isinstance(ws_services, list):
        for s in ws_services:
            if isinstance(s, str) and s.strip():
                services.append(s.strip())
    # From lead data
    if not services:
        desc = lead_data.get("company_description", "")
        categories = reviews.get("categories", [])
        if categories:
            services = categories
        elif desc:
            services = [desc[:200]]

    # Extract reviews data
    reviews_list = reviews.get("reviews", [])
    average_rating = reviews.get("average_rating")
    total_reviews = reviews.get("total_reviews", reviews.get("reviews_found", 0))

    # Build the combined research object
    research = {
        # Lead identity
        "company_name": lead_data.get("company_name", "").split(",")[0].strip(),
        "first_name": lead_data.get("first_name", ""),
        "last_name": lead_data.get("last_name", ""),
        "email": lead_data.get("email", ""),
        "website": lead_data.get("website", website.get("url", "")),
        "phone": reviews.get("phone") or lead_data.get("phone", ""),
        "city": lead_data.get("city", ""),
        "state": lead_data.get("state", ""),
        "employee_count": lead_data.get("employee_count"),
        # Google data
        "address": reviews.get("address") or reviews.get("location", ""),
        "google_rating": average_rating,
        "google_reviews_count": total_reviews,
        "categories": reviews.get("categories", []),
        # Content
        "services": services,
        "about": website.get("about") or lead_data.get("company_description", ""),
        "website_summary": website.get("summary", ""),
        "website_status": website_status,
        # Reviews
        "reviews": {
            "average_rating": average_rating,
            "reviews_found": len(reviews_list),
            "total_reviews": total_reviews,
            "reviews": reviews_list[:10],
            "common_complaints": reviews.get("common_complaints", []),
        },
        # Analysis
        "pain_points": analysis.get("pain_points", []),
        "automation_opportunities": analysis.get("automation_opportunities", []),
        "roi_estimate": analysis.get("roi_estimate", ""),
        "icebreaker": analysis.get("icebreaker", ""),
        # Pipeline metadata
        "lead_score": lead_data.get("lead_score"),
        "lead_tier": lead_data.get("lead_tier"),
    }

    # Write output
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(research, f, indent=2)

    print(f"Research combined: {output_path}")
    print(f"  Company: {research['company_name']}")
    print(f"  Rating: {research['google_rating']}")
    print(f"  Services: {len(research['services'])}")
    print(f"  Reviews: {research['reviews']['reviews_found']}")
    print(f"  Website: {research['website_status']}")

    return research


def main():
    parser = argparse.ArgumentParser(description="Combine research data into research.json")
    parser.add_argument("--lead_json", required=True, help="Lead data as JSON string")
    parser.add_argument("--website", help="Path to website_data.json")
    parser.add_argument("--reviews", help="Path to reviews_data.json")
    parser.add_argument("--analysis", help="Path to analysis.json")
    parser.add_argument("--output", required=True, help="Output research.json path")

    args = parser.parse_args()

    try:
        lead_data = json.loads(args.lead_json)
    except json.JSONDecodeError as e:
        print(f"Error parsing lead_json: {e}", file=sys.stderr)
        sys.exit(1)

    result = combine_research(
        lead_data=lead_data,
        website_path=args.website,
        reviews_path=args.reviews,
        analysis_path=args.analysis,
        output_path=args.output,
    )

    if result:
        print("Done.")
    else:
        print("Failed to combine research.")
        sys.exit(1)


if __name__ == "__main__":
    main()
