#!/usr/bin/env python3
"""
NY Dentist Pipeline — Google Maps Scraper → Google Sheet

Scrapes 100 dentists in New York from Google Maps via Apify,
deduplicates by placeId, and pushes results to a new Google Sheet.

Budget: ~$0.50-1.00 Apify credits (1 query × 100 results)

Usage:
    python3 execution/ny_dentist_pipeline.py
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

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SEARCH = {"query": "dentists in New York", "limit": 100}

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

HEADER_COLOR = {"red": 0.13, "green": 0.39, "blue": 0.76}

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


def create_sheet(client, title, rows):
    """Create a new Google Sheet and populate it."""
    sp = client.create(title)
    ws = sp.sheet1

    all_rows = [SHEET_COLUMNS] + rows
    ws.update(values=all_rows, range_name="A1")

    col_letter = chr(ord("A") + len(SHEET_COLUMNS) - 1)
    try:
        ws.format(f"A1:{col_letter}1", {
            "backgroundColor": HEADER_COLOR,
            "textFormat": {
                "bold": True,
                "foregroundColor": {"red": 1, "green": 1, "blue": 1},
            },
        })
        ws.freeze(rows=1)
        # Auto-resize columns for readability
        for i in range(len(SHEET_COLUMNS)):
            ws.columns_auto_resize(i, i + 1)
    except Exception as e:
        print(f"  Warning: formatting failed: {e}")

    print(f"  Created sheet '{title}': {len(rows)} rows")
    return sp.url


# ---------------------------------------------------------------------------
# Transform
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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("NY DENTIST PIPELINE (Google Maps → Google Sheet)")
    print("=" * 60)

    # --- Step 1: Scrape Google Maps ---
    query = SEARCH["query"]
    limit = SEARCH["limit"]
    print(f"\n[Scraping] '{query}' (limit: {limit})")

    results = scrape_google_maps(
        search_query=query,
        max_results=limit,
        language="en",
    )

    print(f"  Got {len(results)} results")

    if not results:
        sys.exit("No results returned. Check Apify token/credits.")

    # --- Step 2: Deduplicate by placeId ---
    seen = set()
    unique = []
    for item in results:
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
    with open(tmp_dir / "ny_dentists_gmaps_raw.json", "w") as f:
        json.dump(unique, f, indent=2)
    print(f"  Saved raw JSON to .tmp/ny_dentists_gmaps_raw.json")

    # Convert to rows
    all_rows = [item_to_row(item, query) for item in unique]

    # --- Step 3: Create Google Sheet ---
    print("\n[Creating Google Sheet] …")
    creds = get_google_credentials()
    client = gspread.authorize(creds)

    sheet_url = create_sheet(client, "NY Dentists - Google Maps", all_rows)

    # --- Summary ---
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    print(f"Total scraped:  {len(results)} raw / {len(unique)} unique")
    print(f"Sheet:          {sheet_url}")
    print("=" * 60)

    with open(tmp_dir / "ny_dentist_sheet_url.txt", "w") as f:
        f.write(f"NY Dentists - Google Maps: {sheet_url}\n")


if __name__ == "__main__":
    main()
