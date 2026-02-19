#!/usr/bin/env python3
"""
Generate one-line icebreakers for each lead using Claude.

Reads leads from a Google Sheet, generates personalized icebreakers
from company name + city + industry, writes back to 'icebreaker' column.

Uses batches of 50 with parallel workers (same pattern as casualize_batch.py).
"""

import os
import sys
import json
import argparse
import time
import concurrent.futures
import gspread
import anthropic
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
BATCH_SIZE = 50
MAX_WORKERS = 5
MAX_RETRIES = 3


def get_sheet_id_from_url(url):
    """Extract spreadsheet ID from URL."""
    parsed = urlparse(url)
    if "docs.google.com" in parsed.netloc:
        path_parts = parsed.path.split("/")
        if "d" in path_parts:
            return path_parts[path_parts.index("d") + 1]
    return url


def column_letter(n):
    """Convert 0-based column index to Excel-style letter."""
    result = ""
    while n >= 0:
        result = chr(65 + (n % 26)) + result
        n = n // 26 - 1
    return result


def generate_batch(records, client, batch_num, total_batches, industry, retry_count=0):
    """
    Generate icebreakers for a batch of leads using Claude Haiku.
    Returns list of dicts with {id, icebreaker}.
    """
    if not records:
        return []

    records_list = []
    for i, record in enumerate(records):
        records_list.append({
            "id": i + 1,
            "company_name": record["company_name"],
            "city": record["city"],
            "first_name": record.get("first_name", ""),
        })

    records_json = json.dumps(records_list)

    prompt = f"""Generate a one-line icebreaker for each lead. These are {industry} businesses.

Rules:
- 1 sentence max, casual and conversational
- Reference something specific: their city, their trade, or a common challenge in their industry
- NO generic compliments ("great company", "love your work")
- NO questions — make it a statement or observation
- Sound like a real person, not a bot
- Vary the style across records — don't repeat the same pattern

Examples of GOOD icebreakers:
- "Saw you guys are based in Phoenix — brutal summers probably keep your HVAC crews slammed."
- "Running a plumbing shop in Chicago means you're no stranger to frozen pipe season."
- "Landscaping in Austin is a whole different game with that Texas heat."

Examples of BAD icebreakers:
- "I love what you're doing at ABC Plumbing!" (generic)
- "How's business going?" (question)
- "Your company looks amazing!" (empty flattery)

Input: {records_json}

Return ONLY a valid JSON array with objects containing "id" and "icebreaker" fields. No markdown, no explanations."""

    try:
        message = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=6000,
            messages=[{"role": "user", "content": prompt}]
        )
        response_text = message.content[0].text.strip()

        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            lines = response_text.split('\n')
            response_text = '\n'.join(lines[1:-1])

        results = json.loads(response_text)

        # Pad if needed
        if len(results) != len(records):
            print(f"  Warning: Batch {batch_num}/{total_batches}: Got {len(results)} results for {len(records)} inputs")
            while len(results) < len(records):
                idx = len(results)
                results.append({
                    "id": idx + 1,
                    "icebreaker": ""
                })

        print(f"  Batch {batch_num}/{total_batches} complete ({len(records)} records)")
        return results

    except anthropic.RateLimitError:
        if retry_count < MAX_RETRIES:
            wait_time = (2 ** retry_count) * 2
            print(f"  Batch {batch_num}/{total_batches} rate limited, retrying in {wait_time}s...")
            time.sleep(wait_time)
            return generate_batch(records, client, batch_num, total_batches, industry, retry_count + 1)
        else:
            print(f"  Batch {batch_num}/{total_batches} failed after {MAX_RETRIES} retries")
            return [{"id": i + 1, "icebreaker": ""} for i in range(len(records))]

    except Exception as e:
        print(f"  Batch {batch_num}/{total_batches} error: {str(e)[:100]}")
        return [{"id": i + 1, "icebreaker": ""} for i in range(len(records))]


def main():
    parser = argparse.ArgumentParser(description="Generate icebreakers for leads using Claude")
    parser.add_argument("--sheet_url", required=True, help="Google Sheet URL with leads")
    parser.add_argument("--industry", default="local services",
                        help="Industry context for icebreakers (default: local services)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing icebreakers")
    parser.add_argument("--workers", type=int, default=MAX_WORKERS,
                        help=f"Number of parallel workers (default: {MAX_WORKERS})")
    args = parser.parse_args()

    if not ANTHROPIC_API_KEY:
        print("Error: ANTHROPIC_API_KEY not set in .env")
        sys.exit(1)

    start_time = time.time()

    # Connect to sheet
    print("Connecting to Google Sheet...")
    try:
        gc = gspread.oauth()
        sheet_id = get_sheet_id_from_url(args.sheet_url)
        spreadsheet = gc.open_by_key(sheet_id)
        worksheet = spreadsheet.sheet1
    except Exception as e:
        print(f"Error connecting to sheet: {e}")
        sys.exit(1)

    # Read data
    print("Reading sheet data...")
    rows = worksheet.get_all_values()
    if not rows:
        print("Sheet is empty")
        sys.exit(0)

    headers = rows[0]

    # Find required columns
    try:
        company_name_idx = headers.index("company_name")
        city_idx = headers.index("city")
    except ValueError as e:
        print(f"Error: Missing required column: {e}")
        print(f"Available columns: {headers}")
        sys.exit(1)

    email_idx = headers.index("email") if "email" in headers else None
    first_name_idx = headers.index("first_name") if "first_name" in headers else None

    # Find or create icebreaker column
    if "icebreaker" in headers:
        icebreaker_idx = headers.index("icebreaker")
    else:
        icebreaker_idx = len(headers)
        headers.append("icebreaker")
        current_cols = worksheet.col_count
        if icebreaker_idx + 1 > current_cols:
            worksheet.resize(cols=icebreaker_idx + 1)
        worksheet.batch_update([{
            'range': f'{column_letter(icebreaker_idx)}1',
            'values': [["icebreaker"]]
        }])
        print("Created 'icebreaker' column")

    # Collect rows to process
    print(f"\nScanning {len(rows) - 1} rows...")
    rows_to_process = []

    for i in range(1, len(rows)):
        row = rows[i]

        # Skip rows without email
        if email_idx is not None and (len(row) <= email_idx or not row[email_idx].strip()):
            continue

        company_name = row[company_name_idx].strip() if len(row) > company_name_idx else ""
        city = row[city_idx].strip() if len(row) > city_idx else ""
        first_name = row[first_name_idx].strip() if first_name_idx and len(row) > first_name_idx else ""

        if not company_name or not city:
            continue

        # Check if already has icebreaker
        if not args.overwrite:
            existing = row[icebreaker_idx].strip() if len(row) > icebreaker_idx else ""
            if existing:
                continue

        rows_to_process.append({
            'row_num': i,
            'company_name': company_name,
            'city': city,
            'first_name': first_name,
        })

    total_to_process = len(rows_to_process)
    print(f"Found {total_to_process} leads needing icebreakers")

    if total_to_process == 0:
        print("Nothing to process!")
        sys.exit(0)

    # Split into batches
    batches = []
    for batch_start in range(0, total_to_process, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, total_to_process)
        batches.append(rows_to_process[batch_start:batch_end])

    total_batches = len(batches)
    print(f"\nProcessing {total_batches} batches of up to {BATCH_SIZE} records using {args.workers} workers...")

    # Process in parallel
    all_results = []
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_to_batch = {
            executor.submit(generate_batch, batch, client, i + 1, total_batches, args.industry): (i, batch)
            for i, batch in enumerate(batches)
        }

        for future in concurrent.futures.as_completed(future_to_batch):
            batch_idx, batch = future_to_batch[future]
            try:
                results = future.result()
                all_results.append((batch_idx, batch, results))
            except Exception as e:
                print(f"  Batch {batch_idx + 1} failed: {e}")
                results = [{"id": i + 1, "icebreaker": ""} for i in range(len(batch))]
                all_results.append((batch_idx, batch, results))

    # Sort by original batch order
    all_results.sort(key=lambda x: x[0])

    # Prepare updates
    print(f"\nPreparing updates...")
    updates = []
    processed = 0

    for batch_idx, batch, results in all_results:
        for i, item in enumerate(batch):
            result = results[i] if i < len(results) else {"icebreaker": ""}
            icebreaker = result.get("icebreaker", "")

            row_num = item['row_num'] + 1  # 1-indexed for sheet
            updates.append({
                'range': f'{column_letter(icebreaker_idx)}{row_num}',
                'values': [[icebreaker]]
            })
        processed += len(batch)

    # Batch update sheet
    print(f"Updating {len(updates)} cells in Google Sheet...")
    if updates:
        chunk_size = 1000
        for i in range(0, len(updates), chunk_size):
            chunk = updates[i:i + chunk_size]
            worksheet.batch_update(chunk)
            if len(updates) > chunk_size:
                print(f"  Updated {min(i + chunk_size, len(updates))}/{len(updates)} cells...")

    elapsed = time.time() - start_time
    print(f"\nDone! Generated icebreakers for {processed} leads in {elapsed:.1f}s ({processed / max(elapsed, 0.1):.1f} leads/sec)")


if __name__ == "__main__":
    main()
