#!/usr/bin/env python3
"""
Upwork Job Scraper using Apify

Uses upwork-vibe~upwork-job-scraper actor (FREE tier).
Server-side filter: jobCategories only (keywords/experience/budget ignored server-side).
All real filtering done locally via keyword_match() and filter_jobs().

Usage:
    python execution/upwork_apify_scraper.py --keywords "automation,ai agent,n8n" --limit 50
    python execution/upwork_apify_scraper.py --keywords "workflow" --limit 30 --experience intermediate,expert
    python execution/upwork_apify_scraper.py --keywords "api integration" --max-proposals 10 -o .tmp/upwork_jobs.json
"""

import os
import json
import time
import argparse
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

ACTOR_ID = "upwork-vibe~upwork-job-scraper"

# Default categories that match our keyword space
DEFAULT_JOB_CATEGORIES = [
    "All - Web, Mobile & Software Dev",
    "All - IT & Networking",
    "All - Data Science & Analytics",
    "AI & Machine Learning",
    "AI Apps & Integration",
]


def scrape_upwork_jobs(
    limit: int = 50,
    keywords: list = None,
    job_categories: list = None,
) -> list:
    """Scrape Upwork jobs using upwork-vibe actor (free tier).

    Only server-side filter that works: jobCategories.
    All keyword/budget/experience filtering must be done locally after.

    Args:
        limit: Max jobs to fetch
        keywords: Ignored server-side (kept for signature compat), used only locally
        job_categories: Upwork category names for server-side filtering
    """

    api_token = os.environ.get("APIFY_API_TOKEN")
    if not api_token:
        raise ValueError("APIFY_API_TOKEN not found in environment")

    run_url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs?token={api_token}"

    categories = job_categories or DEFAULT_JOB_CATEGORIES
    input_data = {
        "limit": limit,
        "jobCategories": categories,
    }

    print(f"Scraping Upwork jobs (actor: {ACTOR_ID})")
    print(f"  Limit: {limit} | Cost: FREE")
    print(f"  Categories: {', '.join(categories)}")
    if keywords:
        print(f"  Keywords (local filter only): {', '.join(keywords)}")

    # Start the actor run
    response = requests.post(run_url, json=input_data)
    if not response.ok:
        raise Exception(f"Failed to start actor: {response.text}")

    run_info = response.json()
    run_id = run_info.get('data', {}).get('id')
    dataset_id = run_info.get('data', {}).get('defaultDatasetId')

    print(f"  Run started: {run_id}")

    # Wait for completion
    status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={api_token}"

    for i in range(80):  # Max ~6.5 minutes wait
        time.sleep(5)
        status_resp = requests.get(status_url)
        if status_resp.ok:
            sdata = status_resp.json().get('data', {})
            status = sdata.get('status')

            if status == 'SUCCEEDED':
                cost = sdata.get('usageTotalUsd', 0)
                print(f"  Scraping completed! Cost: ${cost:.4f}")
                break
            elif status in ('FAILED', 'ABORTED', 'TIMED-OUT'):
                raise Exception(f"Actor run failed: {status}")
            print(f"  {status}...")
        else:
            print(f"  Error checking status: {status_resp.status_code}")

    # Get results
    dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={api_token}"
    results_resp = requests.get(dataset_url)

    if not results_resp.ok:
        raise Exception(f"Failed to fetch results: {results_resp.text}")

    jobs = results_resp.json()
    print(f"  Fetched {len(jobs)} raw jobs from Apify")
    return jobs


def format_job(job: dict) -> dict:
    """Normalize job data for pipeline use.

    Handles both flash_mage format (nested data.opening/buyer structure)
    and upwork-vibe format (flat structure with budget/client keys).
    """

    # Detect format: flash_mage has 'data' with 'opening' key
    if 'data' in job and isinstance(job.get('data'), dict) and 'opening' in job['data']:
        return _format_flash_mage(job)
    else:
        return _format_upwork_vibe(job)


def _format_flash_mage(job: dict) -> dict:
    """Format flash_mage~upwork actor output."""
    data = job.get('data', {})
    opening = data.get('opening', {})
    info = opening.get('info', {})
    buyer = data.get('buyer', {})
    buyer_extra = data.get('buyerExtra', {})
    buyer_loc = buyer.get('location', {})
    buyer_stats = buyer.get('stats', {})
    activity = opening.get('clientActivity', {})
    ext_budget = opening.get('extendedBudgetInfo', {})
    sands = opening.get('sandsData', {})

    # Budget
    job_type = info.get('type', '')  # HOURLY or FIXED
    fixed_amount = opening.get('budget', {}).get('amount', 0)
    h_min = ext_budget.get('hourlyBudgetMin', 0) or 0
    h_max = ext_budget.get('hourlyBudgetMax', 0) or 0

    if job_type == 'FIXED' and fixed_amount:
        budget_str = f"${fixed_amount} fixed"
    elif h_min or h_max:
        budget_str = f"${h_min}-${h_max}/hr"
    elif fixed_amount:
        budget_str = f"${fixed_amount} fixed"
    else:
        budget_str = "Not specified"

    # Skills from additionalSkills
    skills = []
    for s in sands.get('additionalSkills', []) or []:
        label = s.get('prefLabel', '')
        if label:
            skills.append(label)

    # Total spent — flash_mage uses totalCharges (can be null)
    total_charges = buyer_stats.get('totalCharges')
    total_spent = 0
    if total_charges and isinstance(total_charges, dict):
        total_spent = total_charges.get('amount', 0) or 0
    elif isinstance(total_charges, (int, float)):
        total_spent = total_charges

    return {
        'id': info.get('id', ''),
        'title': job.get('title', '') or info.get('title', ''),
        'description': opening.get('description', ''),
        'url': job.get('link', ''),
        'budget': budget_str,
        'budget_raw': {
            'fixedBudget': fixed_amount if job_type == 'FIXED' else 0,
            'hourlyRate': {'min': h_min if h_min else None, 'max': h_max if h_max else None},
        },
        'category': opening.get('category', {}).get('name', '') if isinstance(opening.get('category'), dict) else '',
        'experience_level': opening.get('contractorTier', ''),
        'skills': skills,
        'posted': opening.get('postedOn', '') or info.get('createdOn', ''),
        'connects_cost': 0,  # flash_mage does NOT return connects cost
        'proposals': activity.get('totalApplicants', 0),
        'total_hired_on_job': activity.get('totalHired', 0),
        'job_type_raw': job_type,
        'client': {
            'country': buyer_loc.get('country', ''),
            'city': buyer_loc.get('city', ''),
            'timezone': buyer_loc.get('countryTimezone', ''),
            'payment_verified': buyer_extra.get('isPaymentMethodVerified', False),
            'total_spent': total_spent,
            'total_hires': buyer_stats.get('totalJobsWithHires', 0) or 0,
            'hire_rate': 0,  # Not in flash_mage output
            'feedback_score': buyer_stats.get('score', 0) or 0,
        },
        'is_featured': False,
    }


def _format_upwork_vibe(job: dict) -> dict:
    """Format upwork-vibe actor output (legacy format)."""
    budget = job.get('budget', {})

    if isinstance(budget, dict):
        hourly = budget.get('hourlyRate', {})
        if isinstance(hourly, dict):
            h_min = hourly.get('min', 0)
            h_max = hourly.get('max', h_min)
        else:
            h_min = h_max = 0
        fixed = budget.get('fixedBudget')
    else:
        hourly = {}
        h_min = h_max = 0
        fixed = None

    if fixed:
        budget_str = f"${fixed} fixed"
    elif h_min or h_max:
        budget_str = f"${h_min}-${h_max}/hr"
    else:
        budget_str = "Not specified"

    client = job.get('client', {})
    if isinstance(client, dict):
        stats = client.get('stats', {})
    else:
        client = {}
        stats = {}

    return {
        'id': job.get('uid') or job.get('id', ''),
        'title': job.get('title', ''),
        'description': job.get('description', ''),
        'url': job.get('externalLink') or job.get('url', ''),
        'budget': budget_str,
        'budget_raw': budget if isinstance(budget, dict) else {},
        'category': job.get('category', ''),
        'experience_level': job.get('vendor', {}).get('experienceLevel', '') if isinstance(job.get('vendor'), dict) else '',
        'skills': job.get('skills', []),
        'posted': job.get('createdAt') or job.get('publishedOn', ''),
        'connects_cost': job.get('applicationCost') or job.get('connectsCost', 0),
        'proposals': 0,
        'client': {
            'country': client.get('countryCode', ''),
            'timezone': client.get('timezone', ''),
            'payment_verified': client.get('paymentMethodVerified', False),
            'total_spent': stats.get('totalSpent', 0),
            'total_hires': stats.get('totalHires', 0),
            'hire_rate': stats.get('hireRate', 0),
            'feedback_score': stats.get('feedbackRate', 0),
        },
        'is_featured': job.get('isFeatured', False),
    }


def keyword_match(job: dict, keywords: list) -> bool:
    """Check if a formatted job matches ANY of the given keywords.

    Searches title + description + skills. Case-insensitive.
    """
    text = (
        job.get('title', '') + ' ' +
        job.get('description', '') + ' ' +
        ' '.join(job.get('skills', []))
    ).lower()

    for kw in keywords:
        if kw.lower() in text:
            return True
    return False


def filter_jobs(
    jobs: list,
    keywords: list = None,
    min_hourly: float = None,
    max_hourly: float = None,
    min_fixed: float = None,
    max_fixed: float = None,
    experience_levels: list = None,
    max_proposals: int = None,
    verified_payment: bool = False,
    min_client_spent: float = None,
    min_client_hires: int = None,
) -> list:
    """Apply post-scrape filters to formatted jobs."""

    filtered = []

    for job in jobs:
        # Keyword filter (mandatory — server-side is unreliable)
        if keywords and not keyword_match(job, keywords):
            continue

        # Budget filters on normalized data
        budget_raw = job.get('budget_raw', {})
        if isinstance(budget_raw, dict):
            hourly = budget_raw.get('hourlyRate', {})
            if isinstance(hourly, dict):
                hourly_min = hourly.get('min') or 0
                hourly_max = hourly.get('max') or hourly_min
            else:
                hourly_min = hourly_max = 0
            fixed = budget_raw.get('fixedBudget', 0)
        else:
            hourly_min = hourly_max = 0
            fixed = 0

        if min_hourly or max_hourly:
            if hourly_max == 0 and fixed:
                pass  # Fixed-price job, skip hourly filter
            elif hourly_max == 0:
                continue
            else:
                if min_hourly and hourly_max < min_hourly:
                    continue
                if max_hourly and hourly_min > max_hourly:
                    continue

        if min_fixed:
            if fixed and fixed < min_fixed:
                continue

        # Experience level
        if experience_levels:
            job_level = job.get('experience_level', '').upper()
            level_match = any(
                lvl.upper() in job_level or job_level in lvl.upper()
                for lvl in experience_levels
            )
            if not level_match and job_level:
                continue

        # Proposals filter
        if max_proposals:
            proposals = job.get('proposals', 0)
            if proposals and proposals > max_proposals:
                continue

        # Client filters
        client = job.get('client', {})
        if verified_payment and not client.get('payment_verified'):
            continue
        if min_client_spent:
            if (client.get('total_spent', 0) or 0) < min_client_spent:
                continue
        if min_client_hires:
            if (client.get('total_hires', 0) or 0) < min_client_hires:
                continue

        filtered.append(job)

    return filtered


def main():
    parser = argparse.ArgumentParser(description="Scrape Upwork jobs via Apify (upwork-vibe actor)")

    parser.add_argument("--keywords", "-k", help="Comma-separated keywords to search")
    parser.add_argument("--limit", "-l", type=int, default=50, help="Max raw jobs to fetch from Apify")
    parser.add_argument("--experience", "-e", help="Experience levels (comma-separated: intermediate,expert)")
    parser.add_argument("--max-proposals", type=int, help="Max proposals per job")
    parser.add_argument("--min-budget", type=int, help="Min fixed budget")
    parser.add_argument("--min-hourly", type=float, help="Min hourly rate")
    parser.add_argument("--categories", "-c", help="Comma-separated Upwork job categories")
    parser.add_argument("--output", "-o", help="Output JSON file")

    args = parser.parse_args()

    keywords = args.keywords.split(',') if args.keywords else None
    experience = args.experience.split(',') if args.experience else None
    categories = args.categories.split(',') if args.categories else None

    # Scrape raw jobs
    raw_jobs = scrape_upwork_jobs(
        limit=args.limit,
        keywords=keywords,
        job_categories=categories,
    )

    # Format all jobs to normalized structure
    formatted_jobs = [format_job(job) for job in raw_jobs]

    # Apply local keyword + budget + experience filters
    filtered_jobs = filter_jobs(
        formatted_jobs,
        keywords=keywords,
        min_fixed=args.min_budget,
        min_hourly=args.min_hourly,
        experience_levels=experience,
        max_proposals=args.max_proposals,
    )

    print(f"\n=== {len(filtered_jobs)} matching jobs (from {len(formatted_jobs)} scraped) ===\n")

    for i, job in enumerate(filtered_jobs[:20], 1):
        print(f"{i}. {job['title'][:70]}")
        print(f"   Budget: {job['budget']} | Level: {job['experience_level']} | Proposals: {job['proposals']}")
        c = job['client']
        country = c.get('country', '') or c.get('city', '')
        print(f"   Client: {country} | Spent: ${c['total_spent']:,.0f} | Hires: {c['total_hires']} | Verified: {c['payment_verified']}")
        print(f"   Skills: {', '.join(job['skills'][:5])}")
        print(f"   URL: {job['url']}")
        print()

    if len(filtered_jobs) > 20:
        print(f"... and {len(filtered_jobs) - 20} more jobs")

    # Also show rejection stats
    rejected = len(formatted_jobs) - len(filtered_jobs)
    if rejected:
        print(f"  Filtered out: {rejected} jobs (no keyword match or budget/experience mismatch)")

    if args.output:
        os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
        with open(args.output, 'w') as f:
            json.dump(filtered_jobs, f, indent=2)
        print(f"\nSaved {len(filtered_jobs)} jobs to {args.output}")

    return filtered_jobs


if __name__ == "__main__":
    main()
