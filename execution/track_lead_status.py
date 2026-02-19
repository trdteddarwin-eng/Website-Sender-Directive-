#!/usr/bin/env python3
"""
Track lead processing status for deduplication and resume.

Maintains .tmp/processed_leads.json with status for each lead slug.
Check before processing a lead to skip duplicates.

Usage:
    # Mark a lead as completed
    python3 execution/track_lead_status.py \
        --slug acme-hvac \
        --status completed \
        --url "https://tedca-sites.netlify.app/acme-hvac/" \
        --draft_id "r1234567890"

    # Check if a lead is already processed
    python3 execution/track_lead_status.py \
        --slug acme-hvac \
        --check

    # List all processed leads
    python3 execution/track_lead_status.py --list

    # Mark follow-up drafted
    python3 execution/track_lead_status.py \
        --slug acme-hvac \
        --followup 2
"""

import os
import sys
import json
import argparse
from datetime import datetime

STATUS_FILE = ".tmp/processed_leads.json"


def load_status():
    """Load the processed leads status file."""
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_status(data):
    """Save the processed leads status file."""
    os.makedirs(os.path.dirname(STATUS_FILE) or ".", exist_ok=True)
    with open(STATUS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def is_processed(slug):
    """Check if a lead has already been processed."""
    data = load_status()
    lead = data.get(slug, {})
    return lead.get("status") == "completed"


def update_lead(slug, status=None, url=None, draft_id=None, notes=None, followup=None):
    """
    Update a lead's processing status.

    Args:
        slug: Lead slug identifier
        status: Processing status (started, research_done, site_built, completed, failed)
        url: Deployed spec site URL
        draft_id: Gmail draft ID
        notes: Pipeline notes
        followup: Follow-up touchpoint number completed (2, 3, 4)

    Returns:
        Updated lead status dict
    """
    data = load_status()

    if slug not in data:
        data[slug] = {
            "slug": slug,
            "status": "started",
            "created_at": datetime.now().isoformat(),
            "followups_drafted": [],
        }

    lead = data[slug]

    if status:
        lead["status"] = status
    if url:
        lead["spec_site_url"] = url
    if draft_id:
        lead["draft_id"] = draft_id
    if notes:
        lead["notes"] = notes
    if followup:
        if "followups_drafted" not in lead:
            lead["followups_drafted"] = []
        if followup not in lead["followups_drafted"]:
            lead["followups_drafted"].append(followup)

    lead["updated_at"] = datetime.now().isoformat()
    data[slug] = lead
    save_status(data)

    return lead


def list_leads():
    """List all tracked leads."""
    data = load_status()
    if not data:
        print("No leads tracked yet.")
        return

    print(f"{'Slug':<30} {'Status':<15} {'URL':<50} {'Follow-ups'}")
    print("-" * 120)
    for slug, lead in sorted(data.items()):
        status = lead.get("status", "unknown")
        url = lead.get("spec_site_url", "")[:50]
        followups = ", ".join(str(f) for f in lead.get("followups_drafted", []))
        print(f"{slug:<30} {status:<15} {url:<50} {followups}")

    total = len(data)
    completed = sum(1 for l in data.values() if l.get("status") == "completed")
    print(f"\n{completed}/{total} completed")


def get_next_unprocessed(leads_json_path):
    """
    Get the next unprocessed lead from a ranked leads JSON file.

    Args:
        leads_json_path: Path to the ranked leads JSON file

    Returns:
        dict with the next unprocessed lead, or None if all done
    """
    import re

    with open(leads_json_path, "r") as f:
        leads = json.load(f)

    data = load_status()

    for lead in leads:
        company = lead.get("company_name", "")
        slug = company.split(",")[0].strip()
        slug = re.sub(r"[^a-z0-9]+", "-", slug.lower()).strip("-")
        if slug not in data or data[slug].get("status") != "completed":
            return lead

    return None


def main():
    parser = argparse.ArgumentParser(description="Track lead processing status")
    parser.add_argument("--slug", help="Lead slug identifier")
    parser.add_argument("--status", help="Set status (started, research_done, site_built, completed, failed)")
    parser.add_argument("--url", help="Deployed spec site URL")
    parser.add_argument("--draft_id", help="Gmail draft ID")
    parser.add_argument("--notes", help="Pipeline notes")
    parser.add_argument("--followup", type=int, help="Follow-up touchpoint number (2, 3, 4)")
    parser.add_argument("--check", action="store_true", help="Check if lead is already processed")
    parser.add_argument("--list", action="store_true", help="List all tracked leads")
    parser.add_argument("--next", help="Get next unprocessed lead from JSON file")

    args = parser.parse_args()

    if args.list:
        list_leads()
        return

    if args.next:
        lead = get_next_unprocessed(args.next)
        if lead:
            print(json.dumps(lead, indent=2))
        else:
            print("All leads processed!")
        return

    if not args.slug:
        parser.error("--slug is required (or use --list / --next)")
        return

    if args.check:
        processed = is_processed(args.slug)
        print(f"{args.slug}: {'PROCESSED' if processed else 'NOT PROCESSED'}")
        sys.exit(0 if not processed else 1)

    if args.status or args.url or args.draft_id or args.notes or args.followup:
        result = update_lead(
            slug=args.slug,
            status=args.status,
            url=args.url,
            draft_id=args.draft_id,
            notes=args.notes,
            followup=args.followup,
        )
        print(f"Updated {args.slug}: {json.dumps(result, indent=2)}")
    else:
        # Just show current status
        data = load_status()
        if args.slug in data:
            print(json.dumps(data[args.slug], indent=2))
        else:
            print(f"{args.slug}: not tracked")


if __name__ == "__main__":
    main()
