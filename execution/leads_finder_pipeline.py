#!/usr/bin/env python3
"""
Leads Finder Pipeline — Apify code_crafter/leads-finder → Google Sheets

Pulls landscaping business leads from North New Jersey using Apify,
then distributes them across 5 Google Sheets (100 leads each).

Usage:
    python3 execution/leads_finder_pipeline.py
"""

import os
import sys
import json
import time
from pathlib import Path

import requests
import gspread
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / "drive-download-20260125T221337Z-3-001" / ".env"
load_dotenv(ENV_PATH)

APIFY_TOKEN = os.getenv("APIFY_API_TOKEN")
if not APIFY_TOKEN:
    sys.exit("APIFY_API_TOKEN not found in .env")

ACTOR_ID = "code_crafter~leads-finder"
APIFY_BASE = "https://api.apify.com/v2"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

TOTAL_LEADS = 500
BATCH_SIZE = 100
NUM_SHEETS = 5

SHEET_COLUMNS = [
    "Company Name",
    "Email",
    "Phone",
    "Location",
    "Website",
    "Has Website",
    "Rating",
    "Industry",
]

ACTOR_INPUT = {
    "fetch_count": TOTAL_LEADS,
    "file_name": "Landscaping Leads NJ",
    "company_keywords": ["landscaping", "lawn care", "landscape"],
    "contact_location": ["new jersey, us"],
    "email_status": ["validated"],
}

# ---------------------------------------------------------------------------
# Google Sheets helpers
# ---------------------------------------------------------------------------

def get_google_credentials() -> Credentials:
    """Load Google OAuth2 credentials from token.json, refreshing if needed."""
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
        sys.exit("No token.json found. Run OAuth flow first.")

    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Persist refreshed token
            for tp in token_paths:
                if tp.exists():
                    with open(tp, "w") as f:
                        f.write(creds.to_json())
                    break
        else:
            sys.exit("Credentials invalid and cannot be refreshed.")

    return creds


def create_sheet(client: gspread.Client, name: str, rows: list[list[str]]) -> str:
    """Create a Google Sheet, populate it, and return its URL."""
    spreadsheet = client.create(name)
    worksheet = spreadsheet.sheet1

    # Header + data in one batch
    all_rows = [SHEET_COLUMNS] + rows
    worksheet.update(values=all_rows, range_name="A1")

    # Format header
    try:
        worksheet.format("A1:H1", {
            "textFormat": {"bold": True},
            "backgroundColor": {"red": 0.2, "green": 0.66, "blue": 0.33},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
        })
        worksheet.freeze(rows=1)
        # Auto-resize isn't directly available, but set reasonable column widths
    except Exception:
        pass  # formatting is optional

    # Make publicly readable
    try:
        spreadsheet.share(None, perm_type="anyone", role="reader")
    except Exception:
        pass

    return spreadsheet.url


# ---------------------------------------------------------------------------
# Apify helpers
# ---------------------------------------------------------------------------

def start_actor_run(actor_input: dict) -> dict:
    """Start an Apify actor run and return the run metadata."""
    url = f"{APIFY_BASE}/acts/{ACTOR_ID}/runs"
    headers = {"Authorization": f"Bearer {APIFY_TOKEN}", "Content-Type": "application/json"}
    resp = requests.post(url, headers=headers, json=actor_input)
    resp.raise_for_status()
    return resp.json()["data"]


def wait_for_run(run_id: str, poll_interval: int = 15, timeout: int = 600) -> dict:
    """Poll until the run finishes or timeout is reached."""
    url = f"{APIFY_BASE}/acts/{ACTOR_ID}/runs/{run_id}"
    headers = {"Authorization": f"Bearer {APIFY_TOKEN}"}

    elapsed = 0
    while elapsed < timeout:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()["data"]
        status = data.get("status")
        print(f"  Run status: {status}  ({elapsed}s elapsed)")
        if status in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
            return data
        time.sleep(poll_interval)
        elapsed += poll_interval

    sys.exit(f"Actor run timed out after {timeout}s")


def fetch_dataset_items(dataset_id: str) -> list[dict]:
    """Download all items from the run's default dataset."""
    url = f"{APIFY_BASE}/datasets/{dataset_id}/items"
    headers = {"Authorization": f"Bearer {APIFY_TOKEN}"}
    resp = requests.get(url, headers=headers, params={"format": "json"})
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Transform helpers
# ---------------------------------------------------------------------------

def lead_to_row(item: dict) -> list[str]:
    """Convert one Apify dataset item into a spreadsheet row."""
    company = item.get("company_name") or ""
    email = item.get("email") or ""
    phone = item.get("company_phone") or ""

    # Build location from city / state / country
    parts = [p for p in [item.get("city"), item.get("state"), item.get("country")] if p]
    location = ", ".join(parts) if parts else ""

    website = item.get("company_website") or item.get("company_domain") or "N/A"
    has_website = "Yes" if website and website != "N/A" else "No"

    # The actor doesn't return a star rating; leave blank or use a placeholder
    rating = ""

    industry = item.get("industry") or ""

    return [company, email, phone, location, website, has_website, rating, industry]


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("LEADS FINDER PIPELINE")
    print("=" * 60)

    # --- Step 1: Run the Apify actor ---
    print("\n[1/3] Starting Apify actor run …")
    print(f"  Actor:  {ACTOR_ID}")
    print(f"  Leads:  {TOTAL_LEADS}")
    print(f"  Input:  {json.dumps(ACTOR_INPUT, indent=2)}")

    run_meta = start_actor_run(ACTOR_INPUT)
    run_id = run_meta["id"]
    dataset_id = run_meta["defaultDatasetId"]
    print(f"  Run ID:     {run_id}")
    print(f"  Dataset ID: {dataset_id}")

    # --- Step 2: Wait for completion ---
    print("\n[2/3] Waiting for actor to finish …")
    final = wait_for_run(run_id)

    if final["status"] != "SUCCEEDED":
        sys.exit(f"Actor run failed with status: {final['status']}")

    print("  Actor run SUCCEEDED.")

    # --- Step 3: Fetch results ---
    print("\n  Fetching dataset items …")
    items = fetch_dataset_items(dataset_id)
    print(f"  Received {len(items)} leads from Apify")

    if not items:
        sys.exit("No leads returned. Check actor input filters.")

    # Convert to rows
    rows = [lead_to_row(item) for item in items]

    # Trim or pad to exactly TOTAL_LEADS
    rows = rows[:TOTAL_LEADS]
    actual_total = len(rows)
    print(f"  Using {actual_total} leads (requested {TOTAL_LEADS})")

    # Save intermediate JSON
    tmp_dir = BASE_DIR / ".tmp"
    tmp_dir.mkdir(exist_ok=True)
    with open(tmp_dir / "leads_finder_raw.json", "w") as f:
        json.dump(items[:TOTAL_LEADS], f, indent=2)
    print(f"  Saved raw JSON to .tmp/leads_finder_raw.json")

    # --- Step 4: Distribute across 5 Google Sheets ---
    print("\n[3/3] Creating 5 Google Sheets (100 leads each) …")
    creds = get_google_credentials()
    client = gspread.authorize(creds)

    sheet_urls = []
    for i in range(NUM_SHEETS):
        start = i * BATCH_SIZE
        end = start + BATCH_SIZE
        batch_rows = rows[start:end]

        if not batch_rows:
            print(f"  Batch {i + 1}: no leads remaining, skipping")
            continue

        sheet_name = f"Landscaping Leads NJ - Batch {i + 1}"
        print(f"  Creating '{sheet_name}' ({len(batch_rows)} leads) …")
        url = create_sheet(client, sheet_name, batch_rows)
        sheet_urls.append(url)
        print(f"    → {url}")

        # Small delay to avoid Google API rate limits
        if i < NUM_SHEETS - 1:
            time.sleep(2)

    # --- Summary ---
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    print(f"Total leads fetched:  {actual_total}")
    print(f"Sheets created:       {len(sheet_urls)}")
    for idx, url in enumerate(sheet_urls, 1):
        print(f"  Batch {idx}: {url}")
    print("=" * 60)

    # Persist sheet URLs for reference
    with open(tmp_dir / "leads_finder_sheet_urls.txt", "w") as f:
        for url in sheet_urls:
            f.write(url + "\n")


if __name__ == "__main__":
    main()
