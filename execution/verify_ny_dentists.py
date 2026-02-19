#!/usr/bin/env python3
"""
Verify & Qualify NY Dentist Leads

Reads raw scraped data, filters by qualification criteria,
checks website status, and updates the existing Google Sheet.

Qualification:
  - Must have phone AND website
  - Not permanently or temporarily closed
  - Not an unclaimed listing

Usage:
    python3 execution/verify_ny_dentists.py
"""

import json
import sys
import concurrent.futures
from pathlib import Path
from urllib.parse import urlparse

import requests
import gspread
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

RAW_JSON = BASE_DIR / ".tmp" / "ny_dentists_gmaps_raw.json"
SHEET_ID = "1lsd2lQVBHo80XYofCNhdXit1C-AAJ0hoV9zfhZ35UIA"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

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
    "Website Status",
]

HEADER_COLOR = {"red": 0.13, "green": 0.39, "blue": 0.76}

# ---------------------------------------------------------------------------
# Google Sheets auth (reused from ny_dentist_pipeline.py)
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


# ---------------------------------------------------------------------------
# Website verification
# ---------------------------------------------------------------------------

def check_website(url: str) -> str:
    """Check if a website is live. Returns 'Live', 'Redirect', or 'Down'."""
    if not url:
        return "Down"

    # Ensure URL has a scheme
    parsed = urlparse(url)
    if not parsed.scheme:
        url = "https://" + url

    try:
        resp = requests.head(url, timeout=10, allow_redirects=False)
        if resp.status_code < 300:
            return "Live"
        elif resp.status_code < 400:
            return "Redirect"
        else:
            # Try GET as fallback — some servers reject HEAD
            resp = requests.get(url, timeout=10, allow_redirects=True)
            if resp.status_code < 400:
                return "Live"
            return "Down"
    except requests.RequestException:
        # Try GET as last resort
        try:
            resp = requests.get(url, timeout=10, allow_redirects=True)
            if resp.status_code < 400:
                return "Live"
            return "Down"
        except requests.RequestException:
            return "Down"


def check_websites_parallel(leads: list[dict]) -> list[str]:
    """Check all websites in parallel (max 10 threads)."""
    urls = [lead.get("website", "") for lead in leads]
    statuses = ["Down"] * len(urls)

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_idx = {
            executor.submit(check_website, url): i
            for i, url in enumerate(urls)
        }
        for future in concurrent.futures.as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                statuses[idx] = future.result()
            except Exception:
                statuses[idx] = "Down"

    return statuses


# ---------------------------------------------------------------------------
# Qualification filter
# ---------------------------------------------------------------------------

def qualifies(item: dict) -> bool:
    """Check if a lead meets qualification criteria."""
    # Must have phone AND website
    if not item.get("phone") and not item.get("phoneUnformatted"):
        return False
    if not item.get("website"):
        return False
    # Not closed
    if item.get("permanentlyClosed"):
        return False
    if item.get("temporarilyClosed"):
        return False
    # Not unclaimed
    if item.get("claimThisBusiness"):
        return False
    return True


# ---------------------------------------------------------------------------
# Transform
# ---------------------------------------------------------------------------

def item_to_row(item: dict, website_status: str) -> list[str]:
    """Convert a qualified lead to a spreadsheet row."""
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
        website_status,
    ]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("VERIFY & QUALIFY NY DENTIST LEADS")
    print("=" * 60)

    # --- Step 1: Load raw data ---
    if not RAW_JSON.exists():
        sys.exit(f"Raw data not found at {RAW_JSON}")

    with open(RAW_JSON) as f:
        raw_leads = json.load(f)
    print(f"\n[Load] {len(raw_leads)} raw leads from {RAW_JSON.name}")

    # --- Step 2: Filter by qualification criteria ---
    qualified = [item for item in raw_leads if qualifies(item)]
    dropped = len(raw_leads) - len(qualified)
    print(f"[Filter] {len(qualified)} qualified, {dropped} dropped")
    print(f"  - Require: phone + website, not closed, not unclaimed")

    if not qualified:
        sys.exit("No qualified leads found.")

    # --- Step 3: Check website status ---
    print(f"\n[Verify] Checking {len(qualified)} websites...")
    statuses = check_websites_parallel(qualified)

    live = statuses.count("Live")
    redirect = statuses.count("Redirect")
    down = statuses.count("Down")
    print(f"  Live: {live} | Redirect: {redirect} | Down: {down}")

    # --- Step 4: Build rows ---
    rows = [
        item_to_row(lead, status)
        for lead, status in zip(qualified, statuses)
    ]

    # --- Step 5: Update Google Sheet ---
    print(f"\n[Sheet] Updating spreadsheet {SHEET_ID}...")
    creds = get_google_credentials()
    client = gspread.authorize(creds)

    sp = client.open_by_key(SHEET_ID)
    ws = sp.sheet1

    # Clear existing data and write fresh
    ws.clear()
    all_data = [SHEET_COLUMNS] + rows
    ws.update(values=all_data, range_name="A1")

    # Format header
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
        for i in range(len(SHEET_COLUMNS)):
            ws.columns_auto_resize(i, i + 1)
    except Exception as e:
        print(f"  Warning: formatting failed: {e}")

    sheet_url = sp.url
    print(f"  Updated: {len(rows)} verified leads written")

    # --- Summary ---
    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)
    print(f"Raw leads:       {len(raw_leads)}")
    print(f"Qualified:       {len(qualified)}")
    print(f"Dropped:         {dropped}")
    print(f"Website Live:    {live}")
    print(f"Website Redirect:{redirect}")
    print(f"Website Down:    {down}")
    print(f"Sheet:           {sheet_url}")
    print("=" * 60)


if __name__ == "__main__":
    main()
