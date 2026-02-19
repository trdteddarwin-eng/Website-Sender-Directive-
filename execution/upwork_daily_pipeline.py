#!/usr/bin/env python3
"""
Upwork Daily Pipeline — Automated Job Application System

Scrape → Deduplicate → Filter → Score (Sonnet) → Proposals (Opus) → Google Sheet

Usage:
    python execution/upwork_daily_pipeline.py                        # Full run
    python execution/upwork_daily_pipeline.py --dry-run              # Test without Opus costs
    python execution/upwork_daily_pipeline.py --limit 10 --workers 1 # Small test run
    python execution/upwork_daily_pipeline.py --reset-seen           # Clear dedup store
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

load_dotenv()

# Add execution directory to path for sibling imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from upwork_brightdata_scraper import scrape_keywords
from upwork_proposal_generator import (
    process_job,
    create_new_spreadsheet,
)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "upwork_pipeline_config.json")


def load_config(config_path: str = None) -> dict:
    """Load pipeline config from JSON file."""
    path = config_path or CONFIG_PATH
    with open(path) as f:
        return json.load(f)


def load_seen_jobs(path: str) -> dict:
    """Load dedup store. Returns {job_id: timestamp_iso}."""
    if os.path.exists(path):
        try:
            with open(path) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_seen_jobs(path: str, seen: dict):
    """Save dedup store to disk."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(seen, f, indent=2)


def prune_seen_jobs(seen: dict, max_age_days: int = 30) -> dict:
    """Remove entries older than max_age_days."""
    cutoff = datetime.now(timezone.utc).isoformat()
    pruned = {}
    for job_id, ts in seen.items():
        try:
            age = (
                datetime.now(timezone.utc)
                - datetime.fromisoformat(ts.replace("Z", "+00:00"))
            ).days
            if age <= max_age_days:
                pruned[job_id] = ts
        except (ValueError, TypeError):
            pruned[job_id] = ts  # Keep if can't parse
    removed = len(seen) - len(pruned)
    if removed > 0:
        print(f"  Pruned {removed} entries older than {max_age_days} days from dedup store")
    return pruned


def apply_deterministic_filters(jobs: list[dict], filters: dict) -> list[dict]:
    """Phase 1: Apply deterministic filters to job list.

    Filters:
    - verified_payment: only clients with verified payment
    - min_client_spent: minimum $ spent by client
    - min_fixed_budget: minimum fixed-price budget
    - min_hourly_rate: minimum hourly rate
    - max_proposals: skip jobs with too many proposals
    - experience_levels: only specific experience levels
    """
    filtered = []
    reasons = {
        "payment": 0,
        "client_spent": 0,
        "budget": 0,
        "experience": 0,
        "proposals": 0,
    }

    verified_payment = filters.get("verified_payment", False)
    min_client_spent = filters.get("min_client_spent", 0)
    min_fixed_budget = filters.get("min_fixed_budget", 0)
    min_hourly_rate = filters.get("min_hourly_rate", 0)
    max_proposals = filters.get("max_proposals", 999)
    experience_levels = [
        e.lower() for e in filters.get("experience_levels", [])
    ]

    for job in jobs:
        client = job.get("client", {})

        # Verified payment
        if verified_payment and not client.get("payment_verified"):
            reasons["payment"] += 1
            continue

        # Min client spend
        if min_client_spent and (client.get("total_spent", 0) or 0) < min_client_spent:
            reasons["client_spent"] += 1
            continue

        # Experience level
        if experience_levels:
            job_level = (job.get("experience_level") or "").lower()
            if not any(lvl in job_level or job_level in lvl for lvl in experience_levels):
                reasons["experience"] += 1
                continue

        # Budget threshold
        budget_raw = job.get("budget_raw", {})
        hourly = budget_raw.get("hourlyRate", {})
        fixed = budget_raw.get("fixedBudget")

        if fixed is not None:
            if min_fixed_budget and fixed < min_fixed_budget:
                reasons["budget"] += 1
                continue
        elif hourly:
            h_max = hourly.get("max") or hourly.get("min") or 0
            if min_hourly_rate and h_max < min_hourly_rate:
                reasons["budget"] += 1
                continue
        # Jobs with no budget info pass through (we don't filter on missing data)

        # Proposal count
        proposals = job.get("proposals_count", 0) or 0
        if proposals >= max_proposals:
            reasons["proposals"] += 1
            continue

        filtered.append(job)

    print(f"  Filter results: {len(filtered)}/{len(jobs)} passed")
    for reason, count in reasons.items():
        if count > 0:
            print(f"    Filtered out {count} by {reason}")

    return filtered


def score_relevance(jobs: list[dict], config: dict) -> list[dict]:
    """Phase 2: Score job relevance using Sonnet 4.5.

    Returns jobs with 'relevance_score' and 'relevance_notes' fields added.
    Only returns jobs scoring >= min_score.
    """
    import anthropic

    qual_config = config.get("qualification", {})
    model = qual_config.get("model", "claude-sonnet-4-5-20250929")
    min_score = qual_config.get("min_score", 7)
    skills_profile = qual_config.get(
        "skills_profile",
        "AI/automation, n8n workflows, voice AI agents, API integrations, Claude/GPT apps",
    )

    client = anthropic.Anthropic()
    scored = []

    print(f"\n--- Phase 2: AI Relevance Scoring ({model}) ---")
    print(f"  Scoring {len(jobs)} jobs (min score: {min_score})...")

    for i, job in enumerate(jobs, 1):
        try:
            prompt = f"""Score this Upwork job's relevance to our skills profile on a scale of 1-10.

SKILLS PROFILE: {skills_profile}

JOB:
Title: {job['title']}
Description: {job.get('description', '')[:800]}
Skills: {', '.join(job.get('skills', [])[:10])}
Budget: {job['budget']}
Experience: {job.get('experience_level', '')}

SCORING CRITERIA:
- 9-10: Perfect match — job directly asks for our exact skills (AI agents, n8n, workflow automation, voice AI, API integrations)
- 7-8: Strong match — job is clearly in our domain with good overlap
- 5-6: Partial match — some relevant skills but job is primarily about something else
- 3-4: Weak match — tangentially related to our skills
- 1-2: No match — completely outside our expertise

Also flag any red flags: vague descriptions, unrealistic expectations, scope mismatch, suspiciously low budget for complexity.

Respond in this exact JSON format:
{{"score": 8, "notes": "Strong match - needs n8n workflow + AI integration", "red_flags": ""}}

Return ONLY the JSON."""

            response = client.messages.create(
                model=model,
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}],
            )

            result_text = response.content[0].text.strip()
            result = json.loads(result_text)
            score = result.get("score", 0)
            notes = result.get("notes", "")
            red_flags = result.get("red_flags", "")

            job["relevance_score"] = score
            job["relevance_notes"] = notes
            job["relevance_red_flags"] = red_flags

            status = "PASS" if score >= min_score else "skip"
            print(f"  [{i}/{len(jobs)}] {status} ({score}/10) {job['title'][:50]}")

            if score >= min_score:
                scored.append(job)

        except Exception as e:
            print(f"  [{i}/{len(jobs)}] Error scoring: {str(e)[:50]}")
            # On error, include the job (fail open for scoring)
            job["relevance_score"] = None
            job["relevance_notes"] = f"Scoring error: {str(e)[:50]}"
            job["relevance_red_flags"] = ""
            scored.append(job)

    print(f"  {len(scored)}/{len(jobs)} jobs scored {min_score}+ (qualified)")
    return scored


def write_pipeline_sheet(sheet_id: str, jobs: list[dict], sheets_service):
    """Write pipeline results to Google Sheet with relevance score column."""
    headers = [
        "Title", "URL", "Budget", "Experience", "Skills", "Category",
        "Client Country", "Client Spent", "Client Hires", "Connects",
        "Relevance Score", "Relevance Notes",
        "Contact Name", "Contact Confidence", "Apply Link",
        "Cover Letter", "Proposal Doc",
    ]

    rows = [headers]
    for job in jobs:
        skills = job.get("skills", [])
        if isinstance(skills, list):
            skills = ", ".join(skills[:5])

        client = job.get("client", {})

        rows.append([
            job.get("title", ""),
            job.get("url", ""),
            job.get("budget", ""),
            job.get("experience_level", ""),
            skills,
            job.get("category", ""),
            client.get("country", "") if isinstance(client, dict) else "",
            f"${client.get('total_spent', 0):,.0f}" if isinstance(client, dict) else "",
            client.get("total_hires", 0) if isinstance(client, dict) else "",
            job.get("connects_cost", ""),
            job.get("relevance_score", ""),
            job.get("relevance_notes", ""),
            job.get("contact_name", "") or "",
            job.get("contact_confidence", "") or "",
            job.get("apply_link", ""),
            job.get("cover_letter", ""),
            job.get("proposal_doc", ""),
        ])

    col_letter = chr(ord("A") + len(headers) - 1)
    sheets_service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=f"Jobs!A1:{col_letter}{len(rows)}",
        valueInputOption="RAW",
        body={"values": rows},
    ).execute()

    print(f"  Wrote {len(jobs)} jobs to sheet")


def init_google_services():
    """Initialize Google Sheets/Drive/Docs services."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    with open("token.json", "r") as f:
        token_data = json.load(f)
    available_scopes = token_data.get("scopes", [])

    creds = Credentials.from_authorized_user_file("token.json", available_scopes)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    sheets_service = build("sheets", "v4", credentials=creds)
    drive_service = build("drive", "v3", credentials=creds)

    has_docs_scope = "https://www.googleapis.com/auth/documents" in available_scopes
    docs_service = build("docs", "v1", credentials=creds) if has_docs_scope else None
    if not has_docs_scope:
        print("Note: documents scope not available — will skip Google Doc creation")

    return sheets_service, drive_service, docs_service


def run_pipeline(
    config: dict,
    dry_run: bool = False,
    limit: int = None,
    workers: int = None,
):
    """Run the full 3-phase pipeline."""

    keywords = config["keywords"]
    days = config.get("days", 1)
    filters = config.get("filters", {})
    seen_path = config.get("seen_jobs_path", ".tmp/upwork_seen_jobs.json")
    worker_count = workers or config.get("workers", 3)

    print("=" * 60)
    print("UPWORK DAILY PIPELINE")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Keywords: {len(keywords)} | Days: {days} | Workers: {worker_count}")
    if dry_run:
        print("MODE: DRY RUN (no Opus costs)")
    print("=" * 60)

    # ---- Phase 1: Scrape + Deterministic Filters ----
    print(f"\n--- Phase 1: Scrape + Filter (free) ---")

    # Load dedup store
    seen_jobs = load_seen_jobs(seen_path)
    seen_jobs = prune_seen_jobs(seen_jobs, max_age_days=30)
    print(f"  Dedup store: {len(seen_jobs)} previously seen jobs")

    # Scrape
    all_jobs = scrape_keywords(keywords, days=days)
    if not all_jobs:
        print("\nNo jobs found. Exiting.")
        return

    # Deduplicate against seen store
    new_jobs = []
    for job in all_jobs:
        job_id = job.get("id", "")
        if job_id and job_id in seen_jobs:
            continue
        new_jobs.append(job)

    print(f"  {len(new_jobs)} new jobs ({len(all_jobs) - len(new_jobs)} already seen)")

    if not new_jobs:
        print("\nNo new jobs today. Exiting.")
        save_seen_jobs(seen_path, seen_jobs)
        return

    # Apply deterministic filters
    filtered_jobs = apply_deterministic_filters(new_jobs, filters)

    if not filtered_jobs:
        print("\nNo jobs passed filters. Exiting.")
        # Still mark scraped jobs as seen
        for job in new_jobs:
            if job.get("id"):
                seen_jobs[job["id"]] = datetime.now(timezone.utc).isoformat()
        save_seen_jobs(seen_path, seen_jobs)
        return

    # Apply limit
    if limit and len(filtered_jobs) > limit:
        filtered_jobs = filtered_jobs[:limit]
        print(f"  Limited to {limit} jobs")

    # ---- Phase 2: AI Relevance Scoring ----
    if dry_run:
        print(f"\n--- Phase 2: SKIPPED (dry run) ---")
        print(f"  {len(filtered_jobs)} jobs would be scored by Sonnet")
        qualified_jobs = filtered_jobs
    else:
        qualified_jobs = score_relevance(filtered_jobs, config)
        if not qualified_jobs:
            print("\nNo jobs qualified after AI scoring. Exiting.")
            for job in new_jobs:
                if job.get("id"):
                    seen_jobs[job["id"]] = datetime.now(timezone.utc).isoformat()
            save_seen_jobs(seen_path, seen_jobs)
            return

    # Save qualified jobs
    date_str = datetime.now().strftime("%Y-%m-%d")
    qualified_path = f".tmp/upwork_jobs_{date_str}.json"
    os.makedirs(".tmp", exist_ok=True)
    with open(qualified_path, "w") as f:
        json.dump(qualified_jobs, f, indent=2)
    print(f"\n  Saved {len(qualified_jobs)} qualified jobs to {qualified_path}")

    # ---- Phase 3: Proposal Generation ----
    if dry_run:
        print(f"\n--- Phase 3: SKIPPED (dry run) ---")
        print(f"  {len(qualified_jobs)} jobs would get proposals via Opus")
        print(f"\n--- Summary ---")
        print(f"  {len(all_jobs)} scraped → {len(new_jobs)} new → {len(filtered_jobs)} filtered → {len(qualified_jobs)} qualified")
        print(f"  Qualified jobs saved to: {qualified_path}")

        # Mark as seen
        for job in new_jobs:
            if job.get("id"):
                seen_jobs[job["id"]] = datetime.now(timezone.utc).isoformat()
        save_seen_jobs(seen_path, seen_jobs)
        return

    print(f"\n--- Phase 3: Proposal Generation (Opus 4.5, {worker_count} workers) ---")

    import anthropic as anthropic_mod

    anthropic_client = anthropic_mod.Anthropic()
    sheets_service, drive_service, docs_service = init_google_services()

    # Process jobs in parallel
    processed_jobs = [None] * len(qualified_jobs)
    completed = 0

    def process_with_index(idx_job):
        idx, job = idx_job
        try:
            return idx, process_job(job, anthropic_client, drive_service, docs_service), None
        except Exception as e:
            from upwork_proposal_generator import create_apply_link
            return idx, {
                **job,
                "apply_link": create_apply_link(job.get("url", "")),
                "cover_letter": "",
                "proposal_doc": "",
            }, str(e)

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = {
            executor.submit(process_with_index, (i, job)): i
            for i, job in enumerate(qualified_jobs)
        }

        for future in as_completed(futures):
            idx, result, error = future.result()
            processed_jobs[idx] = result
            completed += 1

            if error:
                print(
                    f"  [{completed}/{len(qualified_jobs)}] FAIL {qualified_jobs[idx]['title'][:40]}... {error[:50]}"
                )
            else:
                print(
                    f"  [{completed}/{len(qualified_jobs)}] OK {result['title'][:50]}..."
                )

    # Create Google Sheet
    sheet_title = f"Upwork Proposals - {date_str}"
    sheet_id = create_new_spreadsheet(sheet_title, sheets_service)
    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
    print(f"\n  Created sheet: {sheet_url}")

    # Write to sheet
    write_pipeline_sheet(sheet_id, processed_jobs, sheets_service)

    # Update dedup store
    for job in new_jobs:
        if job.get("id"):
            seen_jobs[job["id"]] = datetime.now(timezone.utc).isoformat()
    save_seen_jobs(seen_path, seen_jobs)

    # Save processed output
    output_path = f".tmp/upwork_processed_{date_str}.json"
    with open(output_path, "w") as f:
        json.dump(processed_jobs, f, indent=2, default=str)

    # Summary
    print(f"\n{'=' * 60}")
    print(f"PIPELINE COMPLETE")
    print(f"{'=' * 60}")
    print(f"  {len(all_jobs)} scraped → {len(new_jobs)} new → {len(filtered_jobs)} filtered → {len(qualified_jobs)} qualified → {len(processed_jobs)} proposals")
    print(f"  Sheet: {sheet_url}")
    print(f"  Output: {output_path}")
    print(f"  Dedup store: {len(seen_jobs)} total seen jobs")


def main():
    parser = argparse.ArgumentParser(description="Upwork Daily Pipeline")
    parser.add_argument(
        "--config", "-c", help="Config file path (default: execution/upwork_pipeline_config.json)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Scrape and filter only, no Opus/proposals"
    )
    parser.add_argument(
        "--limit", "-l", type=int, help="Max jobs to process through proposal generation"
    )
    parser.add_argument(
        "--workers", "-w", type=int, help="Override parallel workers count"
    )
    parser.add_argument(
        "--reset-seen", action="store_true", help="Clear the dedup store before running"
    )

    args = parser.parse_args()

    config = load_config(args.config)

    if args.reset_seen:
        seen_path = config.get("seen_jobs_path", ".tmp/upwork_seen_jobs.json")
        if os.path.exists(seen_path):
            os.remove(seen_path)
            print(f"Cleared dedup store: {seen_path}")
        else:
            print(f"No dedup store found at {seen_path}")

    run_pipeline(
        config,
        dry_run=args.dry_run,
        limit=args.limit,
        workers=args.workers,
    )


if __name__ == "__main__":
    main()
