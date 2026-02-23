#!/usr/bin/env python3
"""
Upwork Auto-Apply Pipeline — 6-Phase Automated Job Application System

Phase 1: Scrape + Filter (free) — Apify scrape, dedup, filter (<=4 connects, $500+ budget)
Phase 2: AI Score + Classify (~$0.003/job) — Sonnet scores + classifies (website/automation/other)
Phase 3: Build Deliverable (~$0.10-0.15/job) — Spec sites for website jobs, flowcharts for automation
Phase 4: Generate Cover Letter (~$0.12/job) — Opus generates cover letter with deliverable URL
Phase 5: Auto-Apply (connects cost) — Playwright submits each application
Phase 6: Report — Email summary + Supabase tracking

Usage:
    python pipeline.py                              # Full run
    python pipeline.py --dry-run                    # Phases 1-2 only (free)
    python pipeline.py --dry-run --with-deliverables # Phases 1-4 (builds but doesn't apply)
    python pipeline.py --limit 1 --headed           # Single apply, visible browser
    python pipeline.py --phase 3                    # Start from phase 3 (resume)
"""

import os
import sys
import json
import re
import time
import argparse
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# Load env from workspace root
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Add parent dir for execution/ imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'execution'))
# Add current dir for sibling imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# execution/ imports
from upwork_apify_scraper import scrape_upwork_jobs, filter_jobs, format_job

# sibling imports
from classifier import score_and_classify_batch
from site_generator import generate_site_for_job
from vercel_deployer import deploy_site
from flowchart_generator import generate_flowchart_for_job
from tracker import (
    record_application, update_application_status, check_already_applied,
    check_daily_budget, update_daily_stats, get_daily_stats
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(SCRIPT_DIR)
TMP_DIR = os.path.join(WORKSPACE_ROOT, ".tmp", "upwork_auto")
SEEN_JOBS_PATH = os.path.join(WORKSPACE_ROOT, ".tmp", "upwork_auto_seen.json")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _save_state(phase_num, data):
    """Save intermediate state to disk so pipeline can be resumed."""
    os.makedirs(TMP_DIR, exist_ok=True)
    path = os.path.join(TMP_DIR, f"phase_{phase_num}_output.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"  State saved: {path}")


def _load_state(phase_num):
    """Load state from a previous phase run. Returns None if missing."""
    path = os.path.join(TMP_DIR, f"phase_{phase_num}_output.json")
    if not os.path.exists(path):
        print(f"  No saved state found for phase {phase_num} at {path}")
        return None
    with open(path, "r") as f:
        data = json.load(f)
    print(f"  Loaded state from {path}")
    return data


def _load_seen_jobs():
    """Load the set of previously seen job IDs from disk."""
    if os.path.exists(SEEN_JOBS_PATH):
        with open(SEEN_JOBS_PATH, "r") as f:
            return set(json.load(f))
    return set()


def _save_seen_jobs(seen):
    """Save the set of seen job IDs to disk."""
    os.makedirs(os.path.dirname(SEEN_JOBS_PATH), exist_ok=True)
    with open(SEEN_JOBS_PATH, "w") as f:
        json.dump(sorted(seen), f, indent=2)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def load_config(config_path=None):
    """Load pipeline configuration from config.json."""
    path = config_path or os.path.join(SCRIPT_DIR, 'config.json')
    if not os.path.exists(path):
        print(f"Warning: Config not found at {path}, using defaults.")
        return {
            "keywords": ["automation", "ai agent"],
            "scraper": {"provider": "apify", "limit_per_keyword": 50, "days": 1},
            "filters": {
                "min_fixed_budget": 500, "min_hourly_rate": 25,
                "max_proposals": 15, "max_connects_cost": 4,
                "experience_levels": ["intermediate", "expert"],
            },
            "scoring": {"model": "claude-sonnet-4-5-20250929", "min_score": 8},
            "proposal": {"model": "claude-opus-4-5-20251101"},
            "deliverable": {"vercel_team": None},
            "auto_apply": {
                "enabled": True, "daily_application_limit": 10,
                "daily_connects_budget": 40, "default_hourly_rate": 75,
                "skip_boost": True, "delay_between_applies_sec": [45, 120],
            },
            "notifications": {"email_on_apply": True},
        }
    with open(path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Phase 1: Scrape + Filter
# ---------------------------------------------------------------------------

def phase1_scrape_and_filter(config):
    """Phase 1: Scrape from Apify, dedup against local file + Supabase, apply filters.

    Uses:
        scrape_upwork_jobs(limit, from_date, to_date) -> list[dict]
        filter_jobs(jobs, keyword, experience_levels, ...) -> list[dict]
        format_job(job) -> dict with id, title, description, url, budget, etc.
        check_already_applied(job_id) -> bool

    Returns: list of filtered job dicts
    """
    keywords = config["keywords"]
    scraper = config.get("scraper", {})
    filters = config.get("filters", {})
    limit = scraper.get("limit_per_keyword", 50) * len(keywords)  # total budget
    limit = min(limit, 200)  # cap at 200 to control cost
    days = scraper.get("days", 1)

    print("\n" + "=" * 60)
    print("PHASE 1: Scrape + Filter")
    print("=" * 60)

    from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    # Load seen-jobs file for cross-run dedup
    seen_jobs = _load_seen_jobs()
    print(f"  Seen-jobs store: {len(seen_jobs)} previously seen")

    # --- Single Apify run with server-side keyword + budget filtering ---
    # This sends ALL keywords in one call (~$0.15) instead of per-keyword ($0.15 each)
    print(f"\n  Scraping with server-side filters (1 run, ~$0.15)")
    try:
        raw_jobs = scrape_upwork_jobs(
            limit=limit,
            from_date=from_date,
            keywords=keywords,
            experience_levels=filters.get("experience_levels"),
            max_connects_cost=filters.get("max_connects_cost"),
        )
    except Exception as e:
        print(f"  Scrape failed: {e}")
        raw_jobs = []

    # Format all returned jobs (already keyword-filtered by Apify)
    all_jobs = [format_job(j) for j in raw_jobs]
    total_scraped = len(all_jobs)
    print(f"\n  Total jobs from Apify (pre-filtered): {total_scraped}")

    # --- Dedup by job ID within batch ---
    seen_ids = set()
    unique_jobs = []
    for job in all_jobs:
        jid = job.get('id')
        if jid and jid not in seen_ids:
            seen_ids.add(jid)
            unique_jobs.append(job)
    print(f"\n  Total unique jobs: {len(unique_jobs)} (from {total_scraped} raw)")

    # --- Dedup against seen-jobs file ---
    new_jobs = []
    for job in unique_jobs:
        jid = job.get('id')
        if jid and jid in seen_jobs:
            continue
        new_jobs.append(job)
        if jid:
            seen_jobs.add(jid)
    print(f"  After seen-file dedup: {len(new_jobs)}")

    # --- Dedup against Supabase (already-applied) ---
    not_applied = []
    for job in new_jobs:
        try:
            if check_already_applied(job['id']):
                continue
        except Exception as e:
            # Fail-open: if Supabase check fails, keep the job
            print(f"    Warning: Supabase check failed for {job['id']}: {e}")
        not_applied.append(job)
    print(f"  New (not already applied): {len(not_applied)}")

    # --- Apply deterministic filters ---
    max_connects = filters.get("max_connects_cost", 4)
    min_fixed = filters.get("min_fixed_budget", 0)
    min_hourly = filters.get("min_hourly_rate", 0)
    max_proposals = filters.get("max_proposals", 50)

    filtered = []
    for job in not_applied:
        # Connects filter
        if job.get('connects_cost', 0) > max_connects:
            continue

        # Budget filter
        budget_raw = job.get('budget_raw', {})
        fixed = budget_raw.get('fixedBudget')
        hourly = budget_raw.get('hourlyRate', {})

        if fixed:  # non-zero, non-None means fixed-price job
            if min_fixed and fixed < min_fixed:
                continue
        elif hourly and (hourly.get('min') or hourly.get('max')):
            h_max = hourly.get('max') or hourly.get('min') or 0
            if min_hourly and h_max < min_hourly:
                continue
        # Jobs with no budget info pass through (scored by AI later)

        # Experience level already filtered in filter_jobs above

        filtered.append(job)

    print(f"  After filters (max {max_connects} connects, min ${min_fixed} fixed, "
          f"min ${min_hourly}/hr): {len(filtered)}")

    # Save seen-jobs
    _save_seen_jobs(seen_jobs)

    # Update daily stats
    try:
        update_daily_stats(jobs_scraped=total_scraped, jobs_filtered=len(filtered))
    except Exception as e:
        print(f"  Warning: Failed to update daily stats: {e}")

    _save_state(1, {"jobs": filtered})
    return filtered


# ---------------------------------------------------------------------------
# Phase 2: AI Score + Classify
# ---------------------------------------------------------------------------

def phase2_score_and_classify(jobs, config):
    """Phase 2: AI scoring + classification with Sonnet.

    Uses:
        score_and_classify_batch(jobs, config) -> (qualified, rejected)
        - Reads config["scoring"]["model"], config["scoring"]["min_score"]
        - Adds relevance_score, job_type, relevance_notes, relevance_red_flags

    Returns: list of qualified jobs (score >= min_score)
    """
    print("\n" + "=" * 60)
    print("PHASE 2: AI Score + Classify")
    print("=" * 60)

    if not jobs:
        print("  No jobs to score.")
        return []

    min_score = config.get("scoring", {}).get("min_score", 8)
    print(f"  Scoring {len(jobs)} jobs (min_score={min_score})")
    print(f"  Estimated cost: ~${len(jobs) * 0.003:.3f}")

    # score_and_classify_batch(jobs, config) -> (qualified_list, rejected_list)
    qualified, rejected = score_and_classify_batch(jobs, config)

    print(f"\n  Qualified: {len(qualified)} | Rejected: {len(rejected)}")

    # Count by type
    types = {}
    for j in qualified:
        t = j.get('job_type', 'other')
        types[t] = types.get(t, 0) + 1
    print(f"  Types: {types}")

    # Print each qualified job
    for j in qualified:
        print(f"    [{j.get('relevance_score', '?')}/10] [{j.get('job_type', '?')}] "
              f"{j.get('title', 'N/A')[:55]}")

    try:
        update_daily_stats(jobs_scored=len(qualified))
    except Exception as e:
        print(f"  Warning: Failed to update daily stats: {e}")

    _save_state(2, {"qualified": qualified, "rejected": rejected})
    return qualified


# ---------------------------------------------------------------------------
# Phase 3: Build Deliverables
# ---------------------------------------------------------------------------

def phase3_build_deliverables(jobs, config):
    """Phase 3: Build spec sites for website jobs, flowcharts for automation jobs.

    Uses:
        generate_site_for_job(job_title, job_description, client_name=None,
                              palette_index=0, hero_style_index=0, output_path=None) -> path or None
        deploy_site(html_content, project_name, team_id=None) -> URL or None
        generate_flowchart_for_job(job_title, job_description,
                                   output_dir=".tmp/flowcharts", render=False)
            -> {props_path, video_path, flowchart_data, success}

    Modifies jobs in-place, adding 'deliverable_url' field.
    Returns: the jobs list (modified)
    """
    print("\n" + "=" * 60)
    print("PHASE 3: Build Deliverables")
    print("=" * 60)

    if not jobs:
        print("  No jobs to build deliverables for.")
        return []

    deliverable_cfg = config.get("deliverable", {})
    vercel_team = deliverable_cfg.get("vercel_team")

    sites_built = 0
    videos_made = 0

    for i, job in enumerate(jobs, 1):
        job_type = job.get('job_type', 'other')
        print(f"\n  [{i}/{len(jobs)}] {job_type.upper()}: {job['title'][:50]}")

        if job_type == 'website':
            try:
                # Build slug for output path
                slug = job['title'].lower()[:30].strip()
                for ch in " /\\:*?\"<>|'":
                    slug = slug.replace(ch, "-")
                slug = "-".join(filter(None, slug.split("-")))

                output_dir = os.path.join(TMP_DIR, "sites")
                output_path = os.path.join(output_dir, slug, "index.html")

                # generate_site_for_job returns the path to the HTML file, or None
                html_path = generate_site_for_job(
                    job_title=job['title'],
                    job_description=job.get('description', ''),
                    palette_index=i % 5,       # Rotate 5 palettes
                    hero_style_index=i % 4,    # Rotate 4 hero styles
                    output_path=output_path,
                )

                if html_path and os.path.exists(html_path):
                    with open(html_path) as f:
                        html_content = f.read()

                    project_name = f"spec-{slug}"[:50]

                    # deploy_site(html_content, project_name, team_id=None) -> URL or None
                    url = deploy_site(html_content, project_name, team_id=vercel_team)
                    if url:
                        job['deliverable_url'] = url
                        sites_built += 1
                        print(f"    Deployed: {url}")
                    else:
                        print(f"    Vercel deploy failed")
                        job['deliverable_url'] = None
                else:
                    print(f"    Site generation failed")
                    job['deliverable_url'] = None

            except Exception as e:
                print(f"    Error building site: {e}")
                job['deliverable_url'] = None

        elif job_type == 'automation':
            try:
                flowchart_dir = os.path.join(TMP_DIR, "flowcharts")

                # generate_flowchart_for_job(job_title, job_description,
                #     output_dir, render) -> {props_path, video_path, flowchart_data, success}
                result = generate_flowchart_for_job(
                    job_title=job['title'],
                    job_description=job.get('description', ''),
                    output_dir=flowchart_dir,
                    render=False,
                )

                if result['success']:
                    job['deliverable_url'] = result.get('video_path') or result.get('props_path', '')
                    videos_made += 1
                    print(f"    Flowchart generated: {result['props_path']}")
                else:
                    print(f"    Flowchart generation failed")
                    job['deliverable_url'] = None

            except Exception as e:
                print(f"    Error building flowchart: {e}")
                job['deliverable_url'] = None

        else:
            job['deliverable_url'] = None
            print(f"    No deliverable (type: other)")

    try:
        update_daily_stats(sites_built=sites_built, videos_made=videos_made)
    except Exception as e:
        print(f"  Warning: Failed to update daily stats: {e}")

    print(f"\n  Built: {sites_built} sites, {videos_made} flowcharts")
    _save_state(3, {"jobs": jobs})
    return jobs


# ---------------------------------------------------------------------------
# Phase 4: Generate Cover Letters
# ---------------------------------------------------------------------------

def phase4_generate_cover_letters(jobs, config):
    """Phase 4: Generate cover letters with Opus, including deliverable URLs.

    Also records each application in Supabase via tracker.record_application.
    Modifies jobs in-place, adding 'cover_letter' and 'apply_url' fields.
    Returns: the jobs list (modified)
    """
    import anthropic

    print("\n" + "=" * 60)
    print("PHASE 4: Generate Cover Letters")
    print("=" * 60)

    if not jobs:
        print("  No jobs to generate cover letters for.")
        return []

    proposal_config = config.get("proposal", {})
    model = proposal_config.get("model", "claude-opus-4-5-20251101")
    client = anthropic.Anthropic()

    print(f"  Generating {len(jobs)} cover letters with {model}")
    print(f"  Estimated cost: ~${len(jobs) * 0.12:.2f}")

    for i, job in enumerate(jobs, 1):
        print(f"  [{i}/{len(jobs)}] {job['title'][:50]}...")

        job_type = job.get('job_type', 'other')
        deliverable_url = job.get('deliverable_url')

        # Build prompt based on job type and deliverable
        if job_type == 'website' and deliverable_url:
            prompt = f"""Generate a short Upwork cover letter for this website job. Include the live demo URL.

JOB: {job['title']}
SKILLS: {', '.join(job.get('skills', [])[:5])}
BUDGET: {job.get('budget', 'Not specified')}

FORMAT (follow EXACTLY - under 35 words):
"Hi. I work with [2-4 word paraphrase of their need] daily & just built a mock for you: {deliverable_url}"

RULES:
- Under 35 words total
- No "I'm excited" or filler
- The URL must be included exactly as shown
- Paraphrase should be concise (e.g., "landing pages", "WordPress sites", "web design")

Return ONLY the cover letter text."""

        elif job_type == 'automation' and deliverable_url:
            prompt = f"""Generate a short Upwork cover letter for this automation job. Include the deliverable link.

JOB: {job['title']}
SKILLS: {', '.join(job.get('skills', [])[:5])}
BUDGET: {job.get('budget', 'Not specified')}

FORMAT (follow EXACTLY - under 35 words):
"Hi. I work with [2-4 word paraphrase] daily & mapped out how I'd build it: {deliverable_url}"

RULES:
- Under 35 words total
- No filler
- The URL must be included exactly as shown

Return ONLY the cover letter text."""

        else:
            prompt = f"""Generate a short Upwork cover letter for this job.

JOB: {job['title']}
SKILLS: {', '.join(job.get('skills', [])[:5])}
BUDGET: {job.get('budget', 'Not specified')}

FORMAT (under 35 words):
"Hi. I work with [2-4 word paraphrase] daily & just built a [2-5 word relevant thing]. Happy to walk you through my approach."

RULES:
- Under 35 words
- No filler

Return ONLY the cover letter text."""

        try:
            response = client.messages.create(
                model=model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )

            cover_letter = ""
            for block in response.content:
                if block.type == "text":
                    cover_letter = block.text.strip()
                    break

            # Strip wrapping quotes if present
            if cover_letter.startswith('"') and cover_letter.endswith('"'):
                cover_letter = cover_letter[1:-1]

            job['cover_letter'] = cover_letter
            print(f"    Letter: {cover_letter[:80]}...")

        except Exception as e:
            print(f"    Error: {e}")
            job['cover_letter'] = ""

        # Generate apply URL from the job URL
        match = re.search(r'~(\w+)', job.get('url', ''))
        if match:
            job['apply_url'] = f"https://www.upwork.com/nx/proposals/job/~{match.group(1)}/apply/"
        else:
            job['apply_url'] = job.get('url', '')

        # Record in Supabase tracker
        # record_application(job_id, job_title, job_url, job_budget, job_type,
        #     relevance_score, cover_letter, bid_amount=None, deliverable_url=None, connects_spent=0)
        try:
            record_application(
                job_id=job['id'],
                job_title=job['title'],
                job_url=job.get('url', ''),
                job_budget=job.get('budget', ''),
                job_type=job.get('job_type', 'other'),
                relevance_score=job.get('relevance_score', 0),
                cover_letter=job.get('cover_letter', ''),
                deliverable_url=deliverable_url,
                connects_spent=job.get('connects_cost', 0),
            )
        except Exception as e:
            print(f"    Tracker error: {e}")

    _save_state(4, {"jobs": jobs})
    return jobs


# ---------------------------------------------------------------------------
# Phase 5: Auto-Apply
# ---------------------------------------------------------------------------

def phase5_auto_apply(jobs, config, headed=False):
    """Phase 5: Playwright auto-apply on Upwork.

    Uses:
        applier.run_apply_batch(jobs, config, session_name, headed, screenshot_dir) -> list[dict]
            Each result: {job_id, success, connects_spent, error}
        check_daily_budget(daily_limit, daily_connects_budget) ->
            {can_apply, apps_today, connects_today, remaining_apps, remaining_connects}

    Returns: list of result dicts
    """
    print("\n" + "=" * 60)
    print("PHASE 5: Auto-Apply")
    print("=" * 60)

    auto_apply_config = config.get("auto_apply", {})

    if not auto_apply_config.get("enabled", False):
        print("  Auto-apply is DISABLED in config. Skipping.")
        return []

    # Check daily budget before starting
    daily_limit = auto_apply_config.get("daily_application_limit", 10)
    daily_budget = auto_apply_config.get("daily_connects_budget", 40)
    default_rate = auto_apply_config.get("default_hourly_rate", 75)

    try:
        budget_check = check_daily_budget(daily_limit, daily_budget)
        if not budget_check["can_apply"]:
            print(f"  Daily budget exhausted: {budget_check['apps_today']}/{daily_limit} apps, "
                  f"{budget_check['connects_today']}/{daily_budget} connects. Skipping.")
            return []
        print(f"  Budget remaining: {budget_check['remaining_apps']} apps, "
              f"{budget_check['remaining_connects']} connects")
    except Exception as e:
        print(f"  Warning: Could not check budget: {e}")

    # Prepare jobs for applier
    apply_jobs = []
    for job in jobs:
        if not job.get('cover_letter'):
            print(f"  Skipping {job['title'][:40]} -- no cover letter")
            continue

        apply_job = {
            'job_id': job['id'],
            'apply_url': job.get('apply_url', ''),
            'cover_letter': job['cover_letter'],
            'hourly_rate': default_rate,
            'connects_cost': job.get('connects_cost', 0),
        }

        # Use fixed bid for fixed-price jobs
        budget_raw = job.get('budget_raw', {})
        if budget_raw.get('fixedBudget'):
            apply_job['fixed_bid'] = budget_raw['fixedBudget']
            apply_job.pop('hourly_rate', None)

        apply_jobs.append(apply_job)

    if not apply_jobs:
        print("  No jobs ready for apply")
        return []

    # Limit to remaining budget
    try:
        remaining = budget_check['remaining_apps']
        if len(apply_jobs) > remaining:
            apply_jobs = apply_jobs[:remaining]
            print(f"  Limited to {remaining} jobs (daily budget)")
    except NameError:
        pass

    # Import and run applier
    # run_apply_batch(jobs, config, session_name="default", headed=False, screenshot_dir=None)
    from applier import run_apply_batch

    screenshot_dir = os.path.join(TMP_DIR, 'screenshots')
    os.makedirs(screenshot_dir, exist_ok=True)

    results = run_apply_batch(
        jobs=apply_jobs,
        config=config,
        session_name="default",
        headed=headed,
        screenshot_dir=screenshot_dir,
    )

    # Update stats
    applied = sum(1 for r in results if r.get('success'))
    connects = sum(r.get('connects_spent', 0) for r in results if r.get('success'))
    errors = sum(1 for r in results if not r.get('success'))

    try:
        update_daily_stats(jobs_applied=applied, connects_spent=connects, errors=errors)
    except Exception as e:
        print(f"  Warning: Failed to update daily stats: {e}")

    print(f"\n  Applied: {applied} | Failed: {errors} | Connects spent: {connects}")
    _save_state(5, {"results": results})
    return results


# ---------------------------------------------------------------------------
# Phase 6: Report
# ---------------------------------------------------------------------------

def phase6_report(jobs, apply_results, config):
    """Phase 6: Email summary + stats.

    Returns: summary dict
    """
    print("\n" + "=" * 60)
    print("PHASE 6: Report")
    print("=" * 60)

    # get_daily_stats(date_str=None) -> dict row from upwork_daily_stats
    try:
        stats = get_daily_stats()
    except Exception as e:
        print(f"  Warning: Could not fetch daily stats: {e}")
        stats = {}

    summary = {
        'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'jobs_scraped': stats.get('jobs_scraped', 0),
        'jobs_filtered': stats.get('jobs_filtered', 0),
        'jobs_scored': stats.get('jobs_scored', 0),
        'jobs_applied': stats.get('jobs_applied', 0),
        'sites_built': stats.get('sites_built', 0),
        'videos_made': stats.get('videos_made', 0),
        'connects_spent': stats.get('connects_spent', 0),
        'errors': stats.get('errors', 0),
        'qualified_jobs': [
            {
                'title': j['title'],
                'type': j.get('job_type', 'other'),
                'score': j.get('relevance_score', 0),
                'deliverable': j.get('deliverable_url', ''),
                'budget': j.get('budget', ''),
            }
            for j in jobs
        ],
        'apply_results': [
            {
                'job_id': r.get('job_id', ''),
                'success': r.get('success', False),
                'connects_spent': r.get('connects_spent', 0),
                'error': r.get('error'),
            }
            for r in apply_results
        ],
    }

    # Print summary
    print(f"\n  Pipeline Summary:")
    print(f"    Scraped:    {summary['jobs_scraped']}")
    print(f"    Filtered:   {summary['jobs_filtered']}")
    print(f"    Scored 8+:  {summary['jobs_scored']}")
    print(f"    Applied:    {summary['jobs_applied']}")
    print(f"    Sites:      {summary['sites_built']}")
    print(f"    Flowcharts: {summary['videos_made']}")
    print(f"    Connects:   {summary['connects_spent']}")
    print(f"    Errors:     {summary['errors']}")

    # Print qualified jobs detail
    if jobs:
        print(f"\n  Qualified Jobs:")
        for j in jobs[:20]:
            deliv = j.get('deliverable_url', '')
            print(f"    [{j.get('relevance_score', '?')}/10] [{j.get('job_type', '?'):10s}] "
                  f"{j['title'][:50]}")
            if deliv:
                print(f"             -> {deliv}")

    # Print apply errors if any
    error_results = [r for r in apply_results if r.get('error')]
    if error_results:
        print(f"\n  Apply Errors:")
        for r in error_results[:10]:
            print(f"    [{r.get('job_id', '?')}] {r.get('error', 'Unknown error')}")

    # Send email notification if configured
    if config.get('notifications', {}).get('email_on_apply') and summary['jobs_applied'] > 0:
        try:
            _send_summary_email(summary, config)
        except Exception as e:
            print(f"  Email notification failed: {e}")

    # Save summary to file
    summary_path = os.path.join(
        TMP_DIR,
        f"pipeline_summary_{datetime.now().strftime('%Y-%m-%d_%H%M')}.json"
    )
    os.makedirs(os.path.dirname(summary_path), exist_ok=True)
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"\n  Summary saved: {summary_path}")

    return summary


def _send_summary_email(summary, config):
    """Send email summary. Placeholder until email system is configured."""
    subject = (
        f"Upwork Auto-Apply: {summary['jobs_applied']} applied, "
        f"{summary['connects_spent']} connects"
    )
    print(f"\n  [EMAIL] Subject: {subject}")
    print("  (Actual email sending handled by Modal webhook deployment)")


# ---------------------------------------------------------------------------
# Main Orchestrator
# ---------------------------------------------------------------------------

def run(
    config=None,
    config_path=None,
    dry_run=False,
    with_deliverables=False,
    limit=None,
    headed=False,
    start_phase=1,
):
    """Run the full 6-phase pipeline.

    Args:
        config: Pre-loaded config dict (takes precedence over config_path)
        config_path: Path to config.json file
        dry_run: If True, run phases 1-2 only (free). With with_deliverables, run 1-4.
        with_deliverables: With dry_run, also run phases 3-4 (build but don't apply)
        limit: Max jobs to process
        headed: Run Playwright browser in visible mode
        start_phase: Start from this phase number (1-6) for resuming
    """
    if config is None:
        config = load_config(config_path)

    mode = "DRY RUN" if dry_run else ("WITH DELIVERABLES (no apply)" if with_deliverables else "FULL AUTO")

    print("=" * 60)
    print("UPWORK AUTO-APPLY PIPELINE")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Mode: {mode}")
    if with_deliverables:
        print("Deliverables: ENABLED (will build but not apply)")
    if headed:
        print("Browser: HEADED (visible)")
    if start_phase > 1:
        print(f"Resuming from phase: {start_phase}")
    if limit:
        print(f"Limit: {limit} jobs")
    print("=" * 60)

    jobs = []
    apply_results = []

    # ---- Phase 1 ----
    if start_phase <= 1:
        try:
            jobs = phase1_scrape_and_filter(config)
        except Exception as e:
            print(f"\n  PHASE 1 FAILED: {e}")
            try:
                update_daily_stats(errors=1)
            except Exception:
                pass
            return
        if not jobs:
            print("\nNo jobs after filtering. Pipeline complete.")
            return
    else:
        state = _load_state(1)
        if state:
            jobs = state.get("jobs", [])
        else:
            print("  ERROR: Cannot resume -- no saved state for Phase 1")
            return

    # Apply limit
    if limit and len(jobs) > limit:
        jobs = jobs[:limit]
        print(f"\nLimited to {limit} jobs")

    # ---- Phase 2 ----
    if start_phase <= 2:
        try:
            jobs = phase2_score_and_classify(jobs, config)
        except Exception as e:
            print(f"\n  PHASE 2 FAILED: {e}")
            try:
                update_daily_stats(errors=1)
            except Exception:
                pass
            return
        if not jobs:
            print("\nNo qualified jobs. Pipeline complete.")
            return
    else:
        state = _load_state(2)
        if state:
            jobs = state.get("qualified", [])
        else:
            print("  ERROR: Cannot resume -- no saved state for Phase 2")
            return

    # Apply limit after scoring
    if limit and len(jobs) > limit:
        jobs = jobs[:limit]

    if dry_run and not with_deliverables:
        print(f"\n{'=' * 60}")
        print("DRY RUN COMPLETE -- Phases 1-2 only")
        print(f"{'=' * 60}")
        print(f"  {len(jobs)} qualified jobs would proceed to deliverable + apply")
        for j in jobs:
            print(f"    [{j.get('relevance_score', '?')}/10] [{j.get('job_type', '?')}] "
                  f"{j['title'][:50]}")
        return

    # ---- Phase 3 ----
    if start_phase <= 3:
        try:
            jobs = phase3_build_deliverables(jobs, config)
        except Exception as e:
            print(f"\n  PHASE 3 FAILED: {e}")
            try:
                update_daily_stats(errors=1)
            except Exception:
                pass
            # Continue without deliverables -- cover letters will adapt
    else:
        state = _load_state(3)
        if state:
            jobs = state.get("jobs", [])
        else:
            print("  ERROR: Cannot resume -- no saved state for Phase 3")
            return

    # ---- Phase 4 ----
    if start_phase <= 4:
        try:
            jobs = phase4_generate_cover_letters(jobs, config)
        except Exception as e:
            print(f"\n  PHASE 4 FAILED: {e}")
            try:
                update_daily_stats(errors=1)
            except Exception:
                pass
            # Can't apply without cover letters
            phase6_report(jobs, [], config)
            return
    else:
        state = _load_state(4)
        if state:
            jobs = state.get("jobs", [])
        else:
            print("  ERROR: Cannot resume -- no saved state for Phase 4")
            return

    if dry_run:
        print(f"\n{'=' * 60}")
        print("DRY RUN COMPLETE -- Phases 1-4 (with deliverables)")
        print(f"{'=' * 60}")
        for j in jobs:
            print(f"  [{j.get('job_type', '?')}] {j['title'][:40]}")
            print(f"    Deliverable: {j.get('deliverable_url', 'none')}")
            print(f"    Letter: {j.get('cover_letter', '')[:80]}")
        return

    # ---- Phase 5 ----
    if start_phase <= 5:
        try:
            apply_results = phase5_auto_apply(jobs, config, headed=headed)
        except Exception as e:
            print(f"\n  PHASE 5 FAILED: {e}")
            try:
                update_daily_stats(errors=1)
            except Exception:
                pass
    else:
        state = _load_state(5)
        if state:
            apply_results = state.get("results", [])

    # ---- Phase 6 ----
    phase6_report(jobs, apply_results, config)

    print(f"\n{'=' * 60}")
    print("PIPELINE COMPLETE")
    print(f"{'=' * 60}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Upwork Auto-Apply Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pipeline.py                              # Full run
  python pipeline.py --dry-run                    # Phases 1-2 only (free)
  python pipeline.py --dry-run --with-deliverables # Phases 1-4 (no apply)
  python pipeline.py --limit 1 --headed           # Single apply, visible browser
  python pipeline.py --phase 3                    # Resume from phase 3
        """,
    )
    parser.add_argument("--config", "-c", help="Config file path")
    parser.add_argument("--dry-run", action="store_true", help="Phases 1-2 only (free)")
    parser.add_argument("--with-deliverables", action="store_true",
                        help="With --dry-run: run phases 1-4")
    parser.add_argument("--limit", "-l", type=int, help="Max jobs to process")
    parser.add_argument("--headed", action="store_true", help="Run browser in visible mode")
    parser.add_argument("--phase", type=int, default=1, choices=[1, 2, 3, 4, 5, 6],
                        help="Start from this phase (loads state from .tmp for prior phases)")

    args = parser.parse_args()

    run(
        config_path=args.config,
        dry_run=args.dry_run,
        with_deliverables=args.with_deliverables,
        limit=args.limit,
        headed=args.headed,
        start_phase=args.phase,
    )


if __name__ == "__main__":
    main()
