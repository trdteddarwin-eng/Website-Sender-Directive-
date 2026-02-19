"""Import leads from ranked JSON files into Google Sheets."""

import json
import re
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from services.supabase_client import upsert_lead


def slugify(company_name):
    """Convert company name to URL slug."""
    # Take part before comma (strip location suffix)
    name = company_name.split(",")[0].strip()
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug


def import_leads_from_file(filepath):
    """Import leads from a ranked JSON file into Google Sheets.

    Returns (imported_count, skipped_count, errors).
    """
    with open(filepath, "r") as f:
        leads = json.load(f)

    if not isinstance(leads, list):
        leads = [leads]

    imported = 0
    skipped = 0
    errors = []

    for lead in leads:
        try:
            company = lead.get("company_name", "")
            if not company:
                skipped += 1
                continue

            slug = slugify(company)
            if not slug:
                skipped += 1
                continue

            data = {
                "slug": slug,
                "first_name": lead.get("first_name", ""),
                "last_name": lead.get("last_name", ""),
                "email": lead.get("email", ""),
                "phone": lead.get("phone", ""),
                "company_name": company,
                "website": lead.get("website", ""),
                "city": lead.get("city", ""),
                "state": lead.get("state", ""),
                "industry": lead.get("industry", "HVAC"),
                "employee_count": lead.get("employee_count"),
                "lead_score": lead.get("lead_score", 0),
                "lead_tier": lead.get("lead_tier", "cold"),
                "score_breakdown": lead.get("score_breakdown", {}),
                "is_qualified_hvac": "yes" if (lead.get("is_qualified_hvac", "yes").lower() == "yes" if isinstance(lead.get("is_qualified_hvac"), str) else bool(lead.get("is_qualified_hvac", True))) else "no",
                "disqualification_reason": lead.get("disqualification_reason", ""),
            }

            upsert_lead(data)
            imported += 1

        except Exception as e:
            errors.append(f"{company}: {str(e)}")

    return imported, skipped, errors
