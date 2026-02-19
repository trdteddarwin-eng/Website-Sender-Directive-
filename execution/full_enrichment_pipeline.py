#!/usr/bin/env python3
"""
Full Lead Enrichment Pipeline

Orchestrates the complete enrichment flow for a batch of leads:
1. Read leads from Google Sheet (with website URLs)
2. Scrape website content for each lead
3. Scrape Google reviews for each lead
4. Run AI analysis to identify pain points and ROI opportunities
5. Update sheet with enriched data

Uses concurrent processing for efficiency with rate limiting and resumability.

Usage:
    python3 execution/full_enrichment_pipeline.py \
        --sheet_url "SHEET_URL" \
        --max_reviews_per_lead 5 \
        --workers 3 \
        --skip_email_enrichment
"""

import os
import sys
import json
import argparse
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from dotenv import load_dotenv
import gspread
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# Add execution dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrape_website_content import scrape_website
from scrape_google_reviews import scrape_reviews
from analyze_lead_for_roi import analyze_lead

load_dotenv()

# Global lock for thread-safe sheet operations
sheet_lock = Lock()

# Output columns to write
OUTPUT_COLUMNS = [
    "website_summary",
    "services_offered",
    "review_summary",
    "pain_points",
    "automation_opportunities",
    "roi_estimate",
    "roi_icebreaker",
]

# Rate limiting settings
MIN_DELAY_BETWEEN_API_CALLS = 1.0  # seconds


def extract_sheet_id(url):
    """Extract the Google Sheet ID from a URL."""
    if '/d/' in url:
        return url.split('/d/')[1].split('/')[0]
    return url


def get_credentials():
    """Get OAuth2 credentials for Google Sheets API."""
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    creds = None

    if os.path.exists('token.json'):
        try:
            with open('token.json', 'r') as token:
                token_data = json.load(token)
                creds = Credentials.from_authorized_user_info(token_data, scopes)
        except Exception as e:
            print(f"Error loading token: {e}")

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            from google_auth_oauthlib.flow import InstalledAppFlow
            creds_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")
            flow = InstalledAppFlow.from_client_secrets_file(creds_file, scopes)
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds


def column_letter(n):
    """Convert 0-based column index to Excel-style letter (A, B, ..., Z, AA, etc.)."""
    result = ""
    while n >= 0:
        result = chr(65 + (n % 26)) + result
        n = n // 26 - 1
    return result


def read_leads_from_sheet(sheet_url, worksheet_name=None, start_row=None, end_row=None):
    """
    Read leads from a Google Sheet.

    Args:
        sheet_url: Google Sheets URL or ID
        worksheet_name: Name of the specific worksheet (default: first sheet)
        start_row: Starting row (1-indexed, excluding header)
        end_row: Ending row (inclusive)

    Returns:
        Tuple of (worksheet, headers, rows_data) where rows_data includes row numbers
    """
    creds = get_credentials()
    client = gspread.authorize(creds)

    sheet_id = extract_sheet_id(sheet_url)
    spreadsheet = client.open_by_key(sheet_id)

    if worksheet_name:
        worksheet = spreadsheet.worksheet(worksheet_name)
    else:
        worksheet = spreadsheet.sheet1

    # Get all data
    all_values = worksheet.get_all_values()
    if not all_values:
        return worksheet, [], []

    headers = all_values[0]
    data_rows = all_values[1:]

    # Apply row filtering
    rows_with_indices = []
    for i, row in enumerate(data_rows):
        row_num = i + 2  # 1-indexed, accounting for header
        if start_row and row_num < start_row:
            continue
        if end_row and row_num > end_row:
            continue
        rows_with_indices.append((row_num, row))

    return worksheet, headers, rows_with_indices


def is_row_enriched(row, headers):
    """Check if a row has already been enriched (has roi_icebreaker filled)."""
    try:
        icebreaker_idx = headers.index("roi_icebreaker")
        return len(row) > icebreaker_idx and row[icebreaker_idx].strip()
    except ValueError:
        return False


def get_column_value(row, headers, column_names):
    """Get value from row, trying multiple possible column names."""
    for col_name in column_names:
        try:
            idx = headers.index(col_name)
            if len(row) > idx:
                return row[idx].strip()
        except ValueError:
            continue
    return ""


def format_reviews_for_analysis(reviews_data):
    """Format reviews data into a string for AI analysis."""
    if not reviews_data:
        return ""

    reviews_list = reviews_data.get("reviews", [])
    if not reviews_list:
        return ""

    formatted = []
    for r in reviews_list[:10]:  # Limit to 10 reviews for context window
        rating = r.get("rating", r.get("stars", "N/A"))
        text = r.get("text", r.get("review", ""))
        if text:
            formatted.append(f"Rating: {rating}/5\n{text}")

    return "\n\n".join(formatted)


def enrich_single_lead(args):
    """
    Enrich a single lead with website content, reviews, and AI analysis.

    Args:
        args: Tuple of (row_num, row_data, headers, config)

    Returns:
        dict with enrichment results and row_num
    """
    row_num, row, headers, config = args

    company_name = get_column_value(row, headers, ["company_name", "business_name", "name"])
    website = get_column_value(row, headers, ["website", "company_domain", "domain", "url"])
    city = get_column_value(row, headers, ["city"])
    state = get_column_value(row, headers, ["state"])

    result = {
        "row_num": row_num,
        "company_name": company_name,
        "website_summary": "",
        "services_offered": "",
        "review_summary": "",
        "pain_points": "",
        "automation_opportunities": "",
        "roi_estimate": "",
        "roi_icebreaker": "",
        "error": None,
    }

    print(f"[Row {row_num}] Enriching: {company_name}")

    # Step 1: Scrape website content
    website_data = None
    if website:
        try:
            print(f"  [Row {row_num}] Scraping website: {website}")
            website_data = scrape_website(website, max_pages=config["max_pages_per_site"])
            time.sleep(MIN_DELAY_BETWEEN_API_CALLS)

            if website_data:
                result["website_summary"] = website_data.get("summary", "")[:5000]
                services = website_data.get("services", [])
                if isinstance(services, list):
                    result["services_offered"] = "; ".join(services)[:2000]
                else:
                    result["services_offered"] = str(services)[:2000]
                print(f"  [Row {row_num}] Website scraped: {website_data.get('pages_scraped', 0)} pages")
        except Exception as e:
            print(f"  [Row {row_num}] Website scrape error: {e}")
            result["error"] = f"Website error: {str(e)}"

    # Step 2: Scrape Google reviews
    reviews_data = None
    if company_name:
        try:
            # Build search query with location
            search_query = company_name
            if city:
                search_query += f" {city}"
            if state:
                search_query += f" {state}"

            print(f"  [Row {row_num}] Scraping reviews for: {search_query}")
            reviews_data = scrape_reviews(
                business_name=company_name,
                location=f"{city}, {state}" if city and state else city or state or "",
                max_reviews=config["max_reviews_per_lead"]
            )
            time.sleep(MIN_DELAY_BETWEEN_API_CALLS)

            if reviews_data:
                reviews_list = reviews_data.get("reviews", [])
                result["review_summary"] = f"{len(reviews_list)} reviews scraped. " + \
                    format_reviews_for_analysis(reviews_data)[:3000]
                print(f"  [Row {row_num}] Reviews scraped: {len(reviews_list)} reviews")
        except Exception as e:
            print(f"  [Row {row_num}] Reviews scrape error: {e}")
            if result["error"]:
                result["error"] += f"; Reviews error: {str(e)}"
            else:
                result["error"] = f"Reviews error: {str(e)}"

    # Step 3: Run AI analysis
    if website_data or reviews_data:
        try:
            print(f"  [Row {row_num}] Running AI analysis...")
            analysis = analyze_lead(
                company_name=company_name,
                website_summary=result["website_summary"],
                services=result["services_offered"],
                reviews=format_reviews_for_analysis(reviews_data) if reviews_data else ""
            )
            time.sleep(MIN_DELAY_BETWEEN_API_CALLS)

            if analysis:
                # Format pain points as string
                pain_points = analysis.get("pain_points", [])
                if isinstance(pain_points, list):
                    result["pain_points"] = "; ".join(pain_points)
                else:
                    result["pain_points"] = str(pain_points)

                # Format automation opportunities as string
                opportunities = analysis.get("automation_opportunities", [])
                if isinstance(opportunities, list):
                    result["automation_opportunities"] = "; ".join(opportunities)
                else:
                    result["automation_opportunities"] = str(opportunities)

                result["roi_estimate"] = analysis.get("roi_estimate", "")
                result["roi_icebreaker"] = analysis.get("icebreaker", "")
                print(f"  [Row {row_num}] AI analysis complete")

        except Exception as e:
            print(f"  [Row {row_num}] AI analysis error: {e}")
            if result["error"]:
                result["error"] += f"; AI error: {str(e)}"
            else:
                result["error"] = f"AI error: {str(e)}"

    return result


def ensure_output_columns(worksheet, headers):
    """Ensure all output columns exist in the sheet, add if missing."""
    current_cols = len(headers)
    new_headers = list(headers)
    columns_added = []

    for col_name in OUTPUT_COLUMNS:
        if col_name not in new_headers:
            new_headers.append(col_name)
            columns_added.append(col_name)

    if columns_added:
        # Resize sheet if needed
        new_col_count = len(new_headers)
        if new_col_count > worksheet.col_count:
            worksheet.resize(cols=new_col_count)

        # Add new column headers
        updates = []
        for col_name in columns_added:
            col_idx = new_headers.index(col_name)
            updates.append({
                'range': f'{column_letter(col_idx)}1',
                'values': [[col_name]]
            })
        worksheet.batch_update(updates)
        print(f"Added columns: {', '.join(columns_added)}")

    return new_headers


def update_row_in_sheet(worksheet, headers, row_num, result, dry_run=False):
    """Update a single row with enrichment results."""
    updates = []

    for col_name in OUTPUT_COLUMNS:
        try:
            col_idx = headers.index(col_name)
            value = result.get(col_name, "")
            if value:
                cell = f'{column_letter(col_idx)}{row_num}'
                updates.append({
                    'range': cell,
                    'values': [[str(value)[:50000]]]  # Google Sheets cell limit
                })
        except ValueError:
            continue

    if updates and not dry_run:
        with sheet_lock:
            worksheet.batch_update(updates)

    return len(updates)


def save_intermediate_results(results, timestamp):
    """Save intermediate results to .tmp/ for recovery."""
    os.makedirs(".tmp", exist_ok=True)
    filepath = f".tmp/enrichment_progress_{timestamp}.json"

    # Convert results to serializable format
    serializable = []
    for r in results:
        serializable.append({
            "row_num": r["row_num"],
            "company_name": r["company_name"],
            "enriched": bool(r.get("roi_icebreaker")),
            "error": r.get("error"),
        })

    with open(filepath, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": serializable,
            "total": len(results),
            "enriched": sum(1 for r in results if r.get("roi_icebreaker")),
            "errors": sum(1 for r in results if r.get("error")),
        }, f, indent=2)

    return filepath


def run_enrichment_pipeline(
    sheet_url,
    max_reviews_per_lead=5,
    max_pages_per_site=5,
    skip_email_enrichment=False,
    start_row=None,
    end_row=None,
    workers=3,
    dry_run=False,
    worksheet_name=None,
):
    """
    Run the full enrichment pipeline.

    Args:
        sheet_url: Google Sheet URL with leads
        max_reviews_per_lead: Max reviews to scrape per lead
        max_pages_per_site: Max pages to scrape per website
        skip_email_enrichment: Whether to skip email enrichment (not used yet)
        start_row: Starting row (1-indexed, excluding header)
        end_row: Ending row (inclusive)
        workers: Number of parallel workers
        dry_run: Preview without writing to sheet

    Returns:
        dict with pipeline results
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    results = {
        "started_at": datetime.now().isoformat(),
        "sheet_url": sheet_url,
        "total_leads": 0,
        "leads_processed": 0,
        "leads_enriched": 0,
        "leads_skipped": 0,
        "errors": [],
        "dry_run": dry_run,
    }

    print(f"\n{'='*60}")
    print("FULL ENRICHMENT PIPELINE")
    print(f"{'='*60}")
    print(f"Sheet: {sheet_url}")
    print(f"Workers: {workers}")
    print(f"Max reviews per lead: {max_reviews_per_lead}")
    print(f"Max pages per site: {max_pages_per_site}")
    if dry_run:
        print("MODE: DRY RUN (no changes will be made)")
    print(f"{'='*60}\n")

    # Step 1: Read leads from sheet
    print("STEP 1: Reading leads from Google Sheet...")
    try:
        worksheet, headers, rows = read_leads_from_sheet(
            sheet_url,
            worksheet_name=worksheet_name,
            start_row=start_row,
            end_row=end_row
        )
    except Exception as e:
        print(f"Error reading sheet: {e}")
        results["errors"].append(f"Sheet read error: {str(e)}")
        return results

    if not rows:
        print("No leads found in sheet")
        return results

    results["total_leads"] = len(rows)
    print(f"Found {len(rows)} leads")

    # Step 2: Ensure output columns exist
    print("\nSTEP 2: Ensuring output columns exist...")
    if not dry_run:
        headers = ensure_output_columns(worksheet, headers)

    # Step 3: Filter out already-enriched rows
    print("\nSTEP 3: Checking for already-enriched leads...")
    leads_to_process = []
    for row_num, row in rows:
        if is_row_enriched(row, headers):
            results["leads_skipped"] += 1
        else:
            leads_to_process.append((row_num, row))

    print(f"  Already enriched (skipping): {results['leads_skipped']}")
    print(f"  To process: {len(leads_to_process)}")

    if not leads_to_process:
        print("\nAll leads already enriched. Nothing to do.")
        results["completed_at"] = datetime.now().isoformat()
        return results

    # Step 4: Enrich leads in parallel
    print(f"\nSTEP 4: Enriching {len(leads_to_process)} leads ({workers} workers)...")
    print(f"{'='*60}\n")

    config = {
        "max_reviews_per_lead": max_reviews_per_lead,
        "max_pages_per_site": max_pages_per_site,
        "skip_email_enrichment": skip_email_enrichment,
    }

    tasks = [(row_num, row, headers, config) for row_num, row in leads_to_process]
    all_results = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_task = {
            executor.submit(enrich_single_lead, task): task
            for task in tasks
        }

        for future in as_completed(future_to_task):
            task = future_to_task[future]
            row_num = task[0]

            try:
                result = future.result()
                all_results.append(result)
                results["leads_processed"] += 1

                # Update sheet immediately (thread-safe)
                if result.get("roi_icebreaker"):
                    cells_updated = update_row_in_sheet(
                        worksheet, headers, row_num, result, dry_run
                    )
                    if cells_updated > 0:
                        results["leads_enriched"] += 1
                        print(f"  [Row {row_num}] Updated sheet with {cells_updated} values")

                if result.get("error"):
                    results["errors"].append(f"Row {row_num}: {result['error']}")

                # Save intermediate results periodically
                if results["leads_processed"] % 5 == 0:
                    save_intermediate_results(all_results, timestamp)
                    print(f"\n  Progress: {results['leads_processed']}/{len(leads_to_process)} processed\n")

            except Exception as e:
                print(f"  [Row {row_num}] Fatal error: {e}")
                results["errors"].append(f"Row {row_num}: {str(e)}")

    # Save final results
    final_backup_path = save_intermediate_results(all_results, timestamp)

    # Save detailed results
    os.makedirs(".tmp", exist_ok=True)
    detailed_path = f".tmp/enrichment_detailed_{timestamp}.json"
    with open(detailed_path, "w") as f:
        json.dump(all_results, f, indent=2)

    results["completed_at"] = datetime.now().isoformat()
    results["backup_file"] = final_backup_path
    results["detailed_file"] = detailed_path

    # Print summary
    print(f"\n{'='*60}")
    print("PIPELINE COMPLETE")
    print(f"{'='*60}")
    print(f"Total leads: {results['total_leads']}")
    print(f"Processed: {results['leads_processed']}")
    print(f"Enriched: {results['leads_enriched']}")
    print(f"Skipped (already enriched): {results['leads_skipped']}")
    print(f"Errors: {len(results['errors'])}")
    if dry_run:
        print("\n[DRY RUN] No changes were made to the sheet")
    print(f"\nBackup saved to: {final_backup_path}")
    print(f"Detailed results: {detailed_path}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Full Lead Enrichment Pipeline - Scrape, analyze, and enrich leads"
    )

    parser.add_argument(
        "--sheet_url",
        required=True,
        help="Google Sheet URL with leads"
    )
    parser.add_argument(
        "--worksheet",
        help="Name of the worksheet (default: first sheet)"
    )
    parser.add_argument(
        "--max_reviews_per_lead",
        type=int,
        default=5,
        help="Maximum reviews to scrape per lead (default: 5)"
    )
    parser.add_argument(
        "--max_pages_per_site",
        type=int,
        default=5,
        help="Maximum pages to scrape per website (default: 5)"
    )
    parser.add_argument(
        "--skip_email_enrichment",
        action="store_true",
        help="Skip email enrichment step"
    )
    parser.add_argument(
        "--start_row",
        type=int,
        help="Starting row (1-indexed, excluding header)"
    )
    parser.add_argument(
        "--end_row",
        type=int,
        help="Ending row (inclusive)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=3,
        help="Number of parallel workers (default: 3)"
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Preview without writing to sheet"
    )

    args = parser.parse_args()

    results = run_enrichment_pipeline(
        sheet_url=args.sheet_url,
        worksheet_name=args.worksheet,
        max_reviews_per_lead=args.max_reviews_per_lead,
        max_pages_per_site=args.max_pages_per_site,
        skip_email_enrichment=args.skip_email_enrichment,
        start_row=args.start_row,
        end_row=args.end_row,
        workers=args.workers,
        dry_run=args.dry_run,
    )

    # Exit with error if all leads failed
    if results["leads_processed"] > 0 and results["leads_enriched"] == 0:
        print("\nWarning: No leads were successfully enriched")
        sys.exit(1)

    if results["errors"] and len(results["errors"]) == results["leads_processed"]:
        print("\nError: All leads failed to process")
        sys.exit(1)


if __name__ == "__main__":
    main()
