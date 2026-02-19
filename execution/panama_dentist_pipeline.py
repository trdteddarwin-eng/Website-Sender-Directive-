#!/usr/bin/env python3
"""
Panama Dentist Lead Pipeline — Google Maps Scraper → 3 Google Sheets

Uses compass/crawler-google-places via scrape_google_maps.py to find
dentist businesses in Panama, then filters into 3 quality-tiered sheets.

Cost budget: ~$2-3 Apify credits (5 queries × 30 results)

Usage:
    python3 execution/panama_dentist_pipeline.py
"""

import os
import sys
import json
import time
from pathlib import Path

import gspread
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from dotenv import load_dotenv

# Import the existing Google Maps scraper
sys.path.insert(0, str(Path(__file__).resolve().parent))
from scrape_google_maps import scrape_google_maps

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR / "drive-download-20260125T221337Z-3-001" / ".env")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# 5 queries × 30 results = ~150 raw results, ~$2-3 in credits
SEARCHES = [
    {"query": "dentista en Ciudad de Panamá", "limit": 30},
    {"query": "clínica dental en Ciudad de Panamá", "limit": 30},
    {"query": "dentista en David, Panamá", "limit": 30},
    {"query": "dentista en Santiago, Panamá", "limit": 25},
    {"query": "dentista en Colón, Panamá", "limit": 25},
]

# Column headers
SHEET_COLUMNS = [
    "Business Name",
    "Category",
    "Phone",
    "Website",
    "Address",
    "Rating",
    "Reviews",
    "Google Maps URL",
    "Place ID",
    "Search Query",
]

SHEET_COLORS = {
    "with_website": {"red": 0.2, "green": 0.66, "blue": 0.33},
    "no_website": {"red": 0.85, "green": 0.55, "blue": 0.1},
    "premium": {"red": 0.13, "green": 0.39, "blue": 0.76},
}

# Existing sheet IDs to update (from previous run)
EXISTING_SHEETS = {
    "with_website": "12VNE1wC39fYRYR8LzO0wuZEJLvuyDP7j-YAqoEHWbOY",
    "no_website": "1sZwvX5eBnxWK-b8yc8g8WEmUcLgDb-ht12cPsPuY1O4",
    "premium": "1maPaX4qCjPs3xeVT1ObcwSypjpP9iMnwtjE-H6NYjXA",
}

# ---------------------------------------------------------------------------
# Google Sheets helpers
# ---------------------------------------------------------------------------

def get_google_credentials() -> Credentials:
    token_paths = [
        BASE_DIR / "token.json",
        BASE_DIR / "drive-download-20260125T221337Z-3-001" / "token.json",
    ]
    creds = None
    for tp in token_paths:
        if tp.exists():
            with open(tp) as f:
                data = json.load(f)
            creds = Credentials.from_authorized_user_info(data, SCOPES)
            print(f"  Loaded credentials from {tp}")
            break

    if not creds:
        sys.exit("No token.json found.")

    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            for tp in token_paths:
                if tp.exists():
                    with open(tp, "w") as f:
                        f.write(creds.to_json())
                    break
        else:
            sys.exit("Credentials invalid and cannot be refreshed.")
    return creds


def update_sheet(client, sheet_id, name, rows, color):
    """Clear and repopulate an existing Google Sheet."""
    sp = client.open_by_key(sheet_id)
    ws = sp.sheet1
    ws.clear()

    all_rows = [SHEET_COLUMNS] + rows
    ws.update(values=all_rows, range_name="A1")

    col_letter = chr(ord("A") + len(SHEET_COLUMNS) - 1)
    try:
        ws.format(f"A1:{col_letter}1", {
            "backgroundColor": color,
            "textFormat": {
                "bold": True,
                "foregroundColor": {"red": 1, "green": 1, "blue": 1},
            },
        })
        ws.freeze(rows=1)
    except Exception as e:
        print(f"  Warning: formatting failed: {e}")

    print(f"  Updated '{name}': {len(rows)} leads")
    return sp.url


# ---------------------------------------------------------------------------
# Transform / Filter
# ---------------------------------------------------------------------------

def item_to_row(item: dict, query: str) -> list[str]:
    """Convert a Google Maps result to a spreadsheet row."""
    return [
        item.get("title") or "",
        item.get("categoryName") or "",
        item.get("phone") or "",
        item.get("website") or "",
        item.get("address") or "",
        str(item.get("totalScore") or ""),
        str(item.get("reviewsCount") or ""),
        item.get("url") or "",
        item.get("placeId") or "",
        query,
    ]


def has_phone(row):
    return bool(row[2].strip())

def has_website(row):
    w = row[3].strip()
    return bool(w) and w.lower() not in ("n/a", "none")

def get_rating(row):
    try:
        return float(row[5])
    except (ValueError, IndexError):
        return 0.0

def get_reviews(row):
    try:
        return int(row[6])
    except (ValueError, IndexError):
        return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("PANAMA DENTIST PIPELINE (Google Maps)")
    print("=" * 60)

    # --- Step 1: Scrape Google Maps ---
    all_items = []
    total_queries = len(SEARCHES)

    for i, s in enumerate(SEARCHES, 1):
        print(f"\n[Query {i}/{total_queries}] {s['query']} (limit: {s['limit']})")
        results = scrape_google_maps(
            search_query=s["query"],
            max_results=s["limit"],
            language="es",
        )
        for item in results:
            item["_search_query"] = s["query"]
        all_items.extend(results)
        print(f"  Got {len(results)} results")

        # Small delay between queries
        if i < total_queries:
            time.sleep(3)

    print(f"\n  Total raw results: {len(all_items)}")

    if not all_items:
        sys.exit("No results from any query. Check Apify token/credits.")

    # --- Step 2: Deduplicate by placeId ---
    seen = set()
    unique = []
    for item in all_items:
        pid = item.get("placeId")
        if pid and pid not in seen:
            seen.add(pid)
            unique.append(item)
        elif not pid:
            unique.append(item)

    print(f"  After dedup: {len(unique)} unique businesses")

    # Save raw data
    tmp_dir = BASE_DIR / ".tmp"
    tmp_dir.mkdir(exist_ok=True)
    with open(tmp_dir / "panama_dentists_gmaps_raw.json", "w") as f:
        json.dump(unique, f, indent=2)
    print(f"  Saved raw JSON to .tmp/panama_dentists_gmaps_raw.json")

    # Convert to rows
    all_rows = [item_to_row(item, item.get("_search_query", "")) for item in unique]

    # --- Step 3: Filter into 3 sheets ---
    # Sheet 1: Has website + has phone, rating >= 3.0
    sheet1 = [r for r in all_rows if has_website(r) and has_phone(r) and get_rating(r) >= 3.0]

    # Sheet 2: No website + has phone (website building prospects)
    sheet2 = [r for r in all_rows if not has_website(r) and has_phone(r)]

    # Sheet 3: Premium — rating >= 4.0 AND reviews >= 10 (established businesses)
    sheet3 = [r for r in all_rows if get_rating(r) >= 4.0 and get_reviews(r) >= 10 and has_phone(r)]

    print(f"\n  Sheet 1 (With Website, 3.0+ rating): {len(sheet1)} leads")
    print(f"  Sheet 2 (No Website, has phone):      {len(sheet2)} leads")
    print(f"  Sheet 3 (Premium, 4.0+ & 10+ reviews):{len(sheet3)} leads")

    # --- Step 4: Update Google Sheets ---
    print("\n[Updating Google Sheets] …")
    creds = get_google_credentials()
    client = gspread.authorize(creds)

    urls = {}
    sheets = [
        ("with_website", "Panama Dentists - With Website", sheet1),
        ("no_website", "Panama Dentists - No Website", sheet2),
        ("premium", "Panama Dentists - Premium Leads", sheet3),
    ]

    for key, name, rows in sheets:
        if not rows:
            print(f"  '{name}': 0 leads, skipping")
            urls[key] = "(no leads)"
            continue
        url = update_sheet(client, EXISTING_SHEETS[key], name, rows, SHEET_COLORS[key])
        urls[key] = url
        time.sleep(2)

    # --- Summary ---
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    print(f"Total scraped:  {len(all_items)} raw / {len(unique)} unique")
    print()
    for key, name, rows in sheets:
        print(f"  {name}: {len(rows)} leads")
        print(f"    {urls[key]}")
    print("=" * 60)

    with open(tmp_dir / "panama_dentist_sheet_urls.txt", "w") as f:
        for key, name, rows in sheets:
            f.write(f"{name}: {urls[key]}\n")


if __name__ == "__main__":
    main()
