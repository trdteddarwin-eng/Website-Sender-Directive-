#!/usr/bin/env python3
"""
Map Apify lead output to standardized template format.

Transforms raw Apify leads-finder output into a consistent schema
for downstream enrichment and outreach workflows.

Usage:
    python3 execution/map_to_template.py --input .tmp/leads_20240115.json --output .tmp/leads_mapped.json
    python3 execution/map_to_template.py --input ".tmp/leads_*.json" --require_email --require_website
    python3 execution/map_to_template.py --input .tmp/leads.json --sheet_name "My Leads"
"""

import os
import sys
import json
import glob
import argparse
import re
from datetime import datetime
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ---------------------------------------------------------------------------
# Column Mapping Configuration
# ---------------------------------------------------------------------------

# Maps Apify field names to standard template columns
# Supports multiple source field names for flexibility (first match wins)
FIELD_MAPPING = {
    # Contact fields
    "first_name": ["contact_first_name", "first_name"],
    "last_name": ["contact_last_name", "last_name"],
    "full_name": ["contact_name", "full_name"],
    "email": ["contact_email", "email", "personal_email"],
    "job_title": ["contact_job_title", "job_title"],
    "linkedin_url": ["contact_linkedin_url", "linkedin"],
    "phone": ["contact_phone_numbers", "mobile_number", "company_phone"],

    # Company fields
    "company_name": ["company_name"],
    "website": ["company_domain", "company_website"],
    "company_linkedin": ["company_linkedin_url", "company_linkedin"],
    "industry": ["company_industry", "industry"],
    "employee_count": ["company_employee_count_range", "company_size"],
    "company_description": ["company_description"],

    # Location fields - handle nested company_location or flat fields
    "city": ["company_location.city", "company_city", "city"],
    "state": ["company_location.state", "company_state", "state"],
    "country": ["company_location.country", "company_country", "country"],
}

# Enrichment columns to add (empty, filled later by enrichment scripts)
ENRICHMENT_COLUMNS = [
    "casual_first_name",
    "casual_company_name",
    "casual_city_name",
    "icebreaker",
    "website_summary",
    "services_offered",
    "review_summary",
    "pain_points",
    "automation_opportunities",
    "roi_estimate",
    "roi_icebreaker",
]

# Email tracking columns (for send status)
TRACKING_COLUMNS = [
    "send_status",
    "send_timestamp",
    "sending_account",
    "send_step",
    "send_message_id",
    "send_error",
]

# All standard columns in order
STANDARD_COLUMNS = [
    "first_name",
    "last_name",
    "full_name",
    "email",
    "job_title",
    "linkedin_url",
    "phone",
    "company_name",
    "website",
    "company_linkedin",
    "industry",
    "employee_count",
    "company_description",
    "city",
    "state",
    "country",
] + ENRICHMENT_COLUMNS + TRACKING_COLUMNS


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def get_nested_value(obj: dict, key_path: str):
    """
    Get a value from a nested dictionary using dot notation.
    e.g., get_nested_value({"a": {"b": 1}}, "a.b") -> 1
    """
    keys = key_path.split(".")
    value = obj
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None
    return value


def extract_field(lead: dict, source_fields: list) -> str:
    """
    Extract a field value from the lead, trying multiple source field names.
    Returns the first non-empty value found, or empty string.
    """
    for field in source_fields:
        if "." in field:
            # Handle nested fields
            value = get_nested_value(lead, field)
        else:
            value = lead.get(field)

        if value is not None and value != "":
            # Handle lists (e.g., phone numbers might be a list)
            if isinstance(value, list):
                value = value[0] if value else ""
            return str(value) if value else ""

    return ""


def split_full_name(full_name: str) -> tuple:
    """
    Split a full name into first and last name.
    Returns (first_name, last_name).
    """
    if not full_name:
        return ("", "")

    parts = full_name.strip().split()
    if len(parts) == 0:
        return ("", "")
    elif len(parts) == 1:
        return (parts[0], "")
    else:
        return (parts[0], " ".join(parts[1:]))


def parse_employee_count(value) -> str:
    """
    Normalize employee count to a consistent format.
    Handles both numeric values and range strings.
    """
    if value is None or value == "":
        return ""

    if isinstance(value, (int, float)):
        return str(int(value))

    # Already a string, return as-is (e.g., "11-50")
    return str(value)


def normalize_website(url: str) -> str:
    """
    Normalize a website URL or domain to a consistent format.
    Ensures https:// prefix.
    """
    if not url:
        return ""

    url = url.strip()

    # If it's just a domain, add https://
    if not url.startswith("http://") and not url.startswith("https://"):
        url = f"https://{url}"

    return url


def map_lead(lead: dict) -> dict:
    """
    Map a single lead from Apify format to standard template format.
    """
    mapped = {}

    # Extract each field using the mapping
    for target_field, source_fields in FIELD_MAPPING.items():
        mapped[target_field] = extract_field(lead, source_fields)

    # Handle name splitting if we have full_name but missing first/last
    if mapped["full_name"] and (not mapped["first_name"] or not mapped["last_name"]):
        first, last = split_full_name(mapped["full_name"])
        if not mapped["first_name"]:
            mapped["first_name"] = first
        if not mapped["last_name"]:
            mapped["last_name"] = last

    # Construct full_name if we have parts but not the whole
    if not mapped["full_name"] and (mapped["first_name"] or mapped["last_name"]):
        mapped["full_name"] = f"{mapped['first_name']} {mapped['last_name']}".strip()

    # Normalize specific fields
    mapped["employee_count"] = parse_employee_count(mapped["employee_count"])
    mapped["website"] = normalize_website(mapped["website"])

    # Add empty enrichment columns
    for col in ENRICHMENT_COLUMNS:
        mapped[col] = ""

    # Add empty tracking columns
    for col in TRACKING_COLUMNS:
        mapped[col] = ""

    return mapped


def load_leads(input_path: str) -> list:
    """
    Load leads from a JSON file or glob pattern.
    Returns a list of lead dictionaries.
    """
    leads = []

    # Check if it's a glob pattern
    if "*" in input_path or "?" in input_path:
        files = glob.glob(input_path)
        if not files:
            print(f"Warning: No files match pattern '{input_path}'", file=sys.stderr)
            return []

        print(f"Found {len(files)} files matching pattern")
        for file_path in sorted(files):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        leads.extend(data)
                    else:
                        leads.append(data)
                print(f"  Loaded {len(data) if isinstance(data, list) else 1} leads from {file_path}")
            except Exception as e:
                print(f"  Error loading {file_path}: {e}", file=sys.stderr)
    else:
        # Single file
        try:
            with open(input_path, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    leads = data
                else:
                    leads = [data]
            print(f"Loaded {len(leads)} leads from {input_path}")
        except Exception as e:
            print(f"Error loading {input_path}: {e}", file=sys.stderr)
            return []

    return leads


def filter_leads(leads: list, require_email: bool = False, require_website: bool = False, max_employees: int = None) -> list:
    """
    Filter leads based on criteria.
    """
    filtered = []

    for lead in leads:
        # Check email requirement
        if require_email:
            email = extract_field(lead, FIELD_MAPPING["email"])
            if not email or not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
                continue

        # Check website requirement
        if require_website:
            website = extract_field(lead, FIELD_MAPPING["website"])
            if not website:
                continue

        # Check employee count
        if max_employees is not None:
            count_str = extract_field(lead, FIELD_MAPPING["employee_count"])
            if count_str:
                # Try to parse the count
                try:
                    # Handle ranges like "11-50" by taking the lower bound
                    if "-" in str(count_str):
                        count = int(str(count_str).split("-")[0])
                    else:
                        count = int(count_str)

                    if count > max_employees:
                        continue
                except (ValueError, TypeError):
                    pass  # If we can't parse, include the lead

        filtered.append(lead)

    return filtered


def upload_to_sheet(df: pd.DataFrame, sheet_name: str) -> str:
    """
    Upload DataFrame to Google Sheet.
    Returns the sheet URL.
    """
    import gspread
    from google.oauth2.service_account import Credentials
    from google.oauth2.credentials import Credentials as UserCredentials
    from google.auth.transport.requests import Request

    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = None

    # Try OAuth 2.0 Token first
    if os.path.exists('token.json'):
        creds = UserCredentials.from_authorized_user_file('token.json', SCOPES)

    # Refresh if expired
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception as e:
            print(f"Error refreshing token: {e}", file=sys.stderr)
            creds = None

    # Try service account
    if not creds:
        service_account_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "service_account.json")
        if os.path.exists(service_account_file):
            with open(service_account_file, 'r') as f:
                content = json.load(f)
            if "type" in content and content["type"] == "service_account":
                creds = Credentials.from_service_account_file(service_account_file, scopes=SCOPES)

    if not creds:
        print("Error: No valid Google credentials found", file=sys.stderr)
        return None

    client = gspread.authorize(creds)

    try:
        # Try to open existing sheet
        try:
            sh = client.open(sheet_name)
            print(f"Opened existing sheet: {sheet_name}")
        except gspread.SpreadsheetNotFound:
            sh = client.create(sheet_name)
            print(f"Created new sheet: {sheet_name}")

        worksheet = sh.get_worksheet(0)
        worksheet.clear()

        # Prepare data
        all_data = [df.columns.tolist()] + df.fillna("").values.tolist()

        # Resize if needed
        required_rows = len(all_data)
        required_cols = len(df.columns)
        if required_rows > worksheet.row_count or required_cols > worksheet.col_count:
            worksheet.resize(rows=max(required_rows, worksheet.row_count),
                           cols=max(required_cols, worksheet.col_count))

        # Upload
        worksheet.update(values=all_data, value_input_option='RAW')

        # Share with user if email provided
        user_email = os.getenv("USER_EMAIL")
        if user_email:
            try:
                sh.share(user_email, perm_type='user', role='writer')
                print(f"Shared sheet with {user_email}")
            except Exception:
                pass

        return sh.url

    except Exception as e:
        print(f"Error uploading to sheet: {e}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Map Apify lead output to standardized template format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic mapping
  python3 execution/map_to_template.py --input .tmp/leads_20240115.json

  # Filter and output to specific file
  python3 execution/map_to_template.py \\
    --input .tmp/leads_20240115.json \\
    --output .tmp/leads_mapped.json \\
    --require_email \\
    --require_website

  # Process multiple files with glob pattern
  python3 execution/map_to_template.py --input ".tmp/leads_*.json"

  # Upload to Google Sheet
  python3 execution/map_to_template.py \\
    --input .tmp/leads.json \\
    --sheet_name "Mapped Leads"
        """
    )

    parser.add_argument("--input", required=True,
                        help="JSON file or glob pattern (e.g., '.tmp/leads_*.json')")
    parser.add_argument("--output", default=".tmp/leads_mapped.json",
                        help="Output JSON file (default: .tmp/leads_mapped.json)")
    parser.add_argument("--sheet_name",
                        help="Optional Google Sheet name to create/update")
    parser.add_argument("--require_email", action="store_true",
                        help="Only include leads with valid email")
    parser.add_argument("--require_website", action="store_true",
                        help="Only include leads with website")
    parser.add_argument("--max_employees", type=int,
                        help="Filter by maximum employee count")

    args = parser.parse_args()

    # Load leads
    print(f"\n{'='*60}")
    print("MAP TO TEMPLATE")
    print(f"{'='*60}")
    print(f"\nInput: {args.input}")

    leads = load_leads(args.input)
    if not leads:
        print("No leads loaded. Exiting.")
        sys.exit(1)

    print(f"\nTotal leads loaded: {len(leads)}")

    # Filter leads
    if args.require_email or args.require_website or args.max_employees:
        print(f"\nApplying filters...")
        if args.require_email:
            print(f"  - Require email: Yes")
        if args.require_website:
            print(f"  - Require website: Yes")
        if args.max_employees:
            print(f"  - Max employees: {args.max_employees}")

        leads = filter_leads(leads, args.require_email, args.require_website, args.max_employees)
        print(f"  Leads after filtering: {len(leads)}")

    if not leads:
        print("No leads remaining after filtering. Exiting.")
        sys.exit(1)

    # Map leads to standard format
    print(f"\nMapping {len(leads)} leads to standard template...")
    mapped_leads = [map_lead(lead) for lead in leads]

    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame(mapped_leads)

    # Ensure all standard columns exist in the right order
    for col in STANDARD_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    df = df[STANDARD_COLUMNS]

    # Save to JSON
    os.makedirs(os.path.dirname(args.output) if os.path.dirname(args.output) else ".", exist_ok=True)

    output_data = df.to_dict(orient='records')
    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2)
    print(f"\nSaved mapped leads to: {args.output}")

    # Show sample of mapped data
    print(f"\nSample lead (first record):")
    if mapped_leads:
        sample = mapped_leads[0]
        for key in ["full_name", "email", "company_name", "website", "city", "state"]:
            if sample.get(key):
                print(f"  {key}: {sample[key]}")

    # Upload to Google Sheet if requested
    if args.sheet_name:
        print(f"\nUploading to Google Sheet: {args.sheet_name}")
        url = upload_to_sheet(df, args.sheet_name)
        if url:
            print(f"Sheet URL: {url}")
        else:
            print("Failed to upload to Google Sheet")
            sys.exit(1)

    # Summary
    print(f"\n{'='*60}")
    print("MAPPING COMPLETE")
    print(f"{'='*60}")
    print(f"Total leads mapped: {len(mapped_leads)}")
    print(f"Output file: {args.output}")

    # Count leads with key fields
    with_email = sum(1 for lead in mapped_leads if lead.get("email"))
    with_website = sum(1 for lead in mapped_leads if lead.get("website"))
    with_phone = sum(1 for lead in mapped_leads if lead.get("phone"))
    print(f"\nData quality:")
    print(f"  With email: {with_email}/{len(mapped_leads)} ({100*with_email/len(mapped_leads):.1f}%)")
    print(f"  With website: {with_website}/{len(mapped_leads)} ({100*with_website/len(mapped_leads):.1f}%)")
    print(f"  With phone: {with_phone}/{len(mapped_leads)} ({100*with_phone/len(mapped_leads):.1f}%)")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
