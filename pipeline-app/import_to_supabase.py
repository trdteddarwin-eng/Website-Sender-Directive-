"""One-time migration script: Import leads from Google Sheets + JSON files into Supabase."""

import os
import sys
import json
import re
import uuid
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from config import (
    GOOGLE_SHEET_ID, GOOGLE_TOKEN_PATH, GOOGLE_CREDS_PATH,
    LOCAL_DATA_DIR, SUPABASE_URL, SUPABASE_KEY,
)

from supabase import create_client


def _slugify(company_name):
    if not company_name:
        return ""
    name = str(company_name).split(",")[0].strip()
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _make_id(slug):
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"lead.{slug}"))


def get_sheets_client():
    """Authenticate with Google Sheets."""
    import gspread
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = None
    if os.path.exists(GOOGLE_TOKEN_PATH):
        with open(GOOGLE_TOKEN_PATH, "r") as f:
            token_data = json.load(f)
        creds = Credentials.from_authorized_user_info(token_data, scopes)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(GOOGLE_TOKEN_PATH, "w") as f:
                f.write(creds.to_json())
        else:
            print("ERROR: Google OAuth token not found. Run OAuth flow first.")
            return None
    client = gspread.authorize(creds)
    return client


def row_to_lead(row):
    """Convert a Google Sheet row dict into Supabase lead format."""
    company = row.get("company_name", "")
    slug = _slugify(company)
    if not slug:
        return None

    iq = row.get("is_qualified_hvac", "")
    if isinstance(iq, str):
        is_qualified = iq.lower() in ("yes", "true", "1")
    else:
        is_qualified = bool(iq)

    score = row.get("lead_score", 0)
    try:
        score = int(score)
    except (ValueError, TypeError):
        score = 0

    send_status = str(row.get("send_status", "")).lower().strip()
    status_map = {
        "": "pending", "pending": "pending", "sent": "emailing",
        "emailing": "emailing", "completed": "completed", "failed": "failed",
        "researching": "researching", "designing": "designing",
        "reviewing": "reviewing", "deploying": "deploying",
    }
    pipeline_status = status_map.get(send_status, send_status or "pending")

    employee_count = row.get("employee_count", None)
    try:
        employee_count = int(employee_count) if employee_count else None
    except (ValueError, TypeError):
        employee_count = None

    raw_data = {k: v for k, v in row.items()}

    lead = {
        "id": _make_id(slug),
        "slug": slug,
        "first_name": str(row.get("first_name", "")),
        "last_name": str(row.get("last_name", "")),
        "full_name": str(row.get("full_name", "")),
        "email": str(row.get("email", "")),
        "phone": str(row.get("phone", "")),
        "company_name": company,
        "company_description": str(row.get("company_description", "")),
        "website": str(row.get("website", "")),
        "city": str(row.get("city", "")),
        "state": str(row.get("state", "")),
        "industry": str(row.get("industry", "HVAC")) or "HVAC",
        "employee_count": employee_count,
        "lead_score": score,
        "lead_tier": str(row.get("lead_tier", "")).lower().strip() or "cold",
        "score_breakdown": json.dumps({}),
        "is_qualified": is_qualified,
        "disqualification_reason": str(row.get("disqualification_reason", "")),
        "pipeline_status": pipeline_status,
        "send_step": str(row.get("send_step", "")),
        "raw_data": json.dumps(raw_data),
    }
    return lead


def import_leads_from_sheets(sb):
    """Import all leads from Google Sheets into Supabase."""
    print("\n=== Importing Leads from Google Sheets ===")
    client = get_sheets_client()
    if not client:
        print("Skipping Google Sheets import (no auth)")
        return 0

    spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
    ws = spreadsheet.sheet1
    records = ws.get_all_records()
    print(f"Found {len(records)} rows in Google Sheet")

    leads = []
    skipped = 0
    for row in records:
        lead = row_to_lead(row)
        if lead:
            leads.append(lead)
        else:
            skipped += 1

    print(f"Parsed {len(leads)} leads ({skipped} skipped)")

    # Upsert in batches of 50
    batch_size = 50
    total_upserted = 0
    for i in range(0, len(leads), batch_size):
        batch = leads[i:i + batch_size]
        try:
            sb.table("leads").upsert(batch, on_conflict="slug").execute()
            total_upserted += len(batch)
            print(f"  Upserted batch {i // batch_size + 1}: {len(batch)} leads ({total_upserted}/{len(leads)})")
        except Exception as e:
            print(f"  ERROR on batch {i // batch_size + 1}: {e}")
            # Try one by one
            for lead in batch:
                try:
                    sb.table("leads").upsert(lead, on_conflict="slug").execute()
                    total_upserted += 1
                except Exception as e2:
                    print(f"    SKIP {lead['slug']}: {e2}")

    print(f"Leads imported: {total_upserted}")
    return total_upserted


def import_json_table(sb, table_name, json_path, strip_id=False):
    """Import a JSON file into a Supabase table."""
    if not os.path.exists(json_path):
        print(f"  {table_name}: No file at {json_path}, skipping")
        return 0

    with open(json_path, "r") as f:
        try:
            rows = json.load(f)
        except json.JSONDecodeError:
            print(f"  {table_name}: Invalid JSON, skipping")
            return 0

    if not isinstance(rows, list):
        rows = [rows]

    if not rows:
        print(f"  {table_name}: Empty file, skipping")
        return 0

    print(f"  {table_name}: {len(rows)} records to import")

    # Clean up rows
    for row in rows:
        if strip_id and "id" in row:
            del row["id"]

        # Serialize any nested dicts/lists that should be JSONB
        for key, val in list(row.items()):
            if isinstance(val, (dict, list)):
                row[key] = json.dumps(val)

    # Insert in batches
    batch_size = 50
    total = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        try:
            sb.table(table_name).upsert(batch).execute()
            total += len(batch)
        except Exception as e:
            print(f"    ERROR batch {i // batch_size + 1}: {e}")
            for row in batch:
                try:
                    sb.table(table_name).insert(row).execute()
                    total += 1
                except Exception as e2:
                    rid = row.get("id", row.get("slug", "?"))
                    print(f"      SKIP {rid}: {e2}")

    print(f"  {table_name}: {total} imported")
    return total


def main():
    print("=" * 60)
    print("TedCA Pipeline — Supabase Migration")
    print("=" * 60)

    if not SUPABASE_URL or not SUPABASE_KEY or "YOUR_" in SUPABASE_URL:
        print("\nERROR: Set SUPABASE_URL and SUPABASE_KEY in .env first!")
        print("  1. Create a project at https://supabase.com")
        print("  2. Run schema.sql in the SQL Editor")
        print("  3. Copy the Project URL and service_role key to .env")
        sys.exit(1)

    sb = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Test connection
    try:
        sb.table("leads").select("id").limit(1).execute()
        print("\nSupabase connection OK")
    except Exception as e:
        print(f"\nERROR: Cannot connect to Supabase: {e}")
        print("Make sure you've run schema.sql in the Supabase SQL Editor.")
        sys.exit(1)

    # 1. Import leads from Google Sheets
    lead_count = import_leads_from_sheets(sb)

    # 2. Import JSON operational tables
    print("\n=== Importing Operational Data from JSON ===")

    # Order matters (foreign keys): pipeline_runs, spec_sites, emails,
    # email_sequences, replies, auto_replies, activity_log
    json_tables = [
        ("pipeline_runs", "pipeline_runs.json", False),
        ("spec_sites", "spec_sites.json", False),
        ("emails", "emails.json", False),
        ("email_sequences", "email_sequences.json", False),
        ("replies", "replies.json", False),
        ("auto_replies", "auto_replies.json", False),
        ("activity_log", "activity_log.json", True),  # strip_id=True (BIGSERIAL)
    ]

    for table_name, filename, strip_id in json_tables:
        json_path = os.path.join(LOCAL_DATA_DIR, filename)
        import_json_table(sb, table_name, json_path, strip_id=strip_id)

    # Summary
    print("\n" + "=" * 60)
    print("Migration Complete!")
    print("=" * 60)

    # Verify counts
    for table in ["leads", "pipeline_runs", "spec_sites", "emails",
                   "email_sequences", "replies", "auto_replies", "activity_log"]:
        try:
            result = sb.table(table).select("*", count="exact").limit(0).execute()
            count = result.count or 0
            print(f"  {table}: {count} rows")
        except Exception as e:
            print(f"  {table}: ERROR - {e}")


if __name__ == "__main__":
    main()
