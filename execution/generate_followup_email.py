#!/usr/bin/env python3
"""
Generate follow-up email drafts for the spec site pipeline.

Creates Gmail drafts for a 4-touch outreach sequence:
- Touch 1 (Day 0): Main spec site pitch (handled by generate_outreach_email.py)
- Touch 2 (Day 3): Short bump with spec site link
- Touch 3 (Day 7): Pain point angle from research
- Touch 4 (Day 14): Break-up email

Usage:
    python3 execution/generate_followup_email.py \
        --research .tmp/acme-hvac/research.json \
        --touchpoint 2 \
        --spec_url "https://tedca-sites.netlify.app/acme-hvac/" \
        --output_dir .tmp/acme-hvac/

    # Generate all follow-ups at once:
    python3 execution/generate_followup_email.py \
        --research .tmp/acme-hvac/research.json \
        --all \
        --spec_url "https://tedca-sites.netlify.app/acme-hvac/" \
        --output_dir .tmp/acme-hvac/
"""

import os
import sys
import json
import argparse
from datetime import datetime


def generate_followup(research_data, touchpoint, spec_url, output_dir):
    """
    Generate a follow-up email HTML + metadata.

    Args:
        research_data: dict from research.json
        touchpoint: int (2, 3, or 4)
        spec_url: Live spec site URL
        output_dir: Directory to write output files

    Returns:
        dict with html_path, meta_path, subject, touchpoint
    """
    os.makedirs(output_dir, exist_ok=True)

    first_name = research_data.get("first_name", "there")
    company_name = research_data.get("company_name", "your company")
    email = research_data.get("email", "")
    services = research_data.get("services", [])
    pain_points = research_data.get("pain_points", [])
    city = research_data.get("city", "")
    state = research_data.get("state", "")
    location = f"{city}, {state}" if city and state else city or state or ""

    services_str = ", ".join(services[:3]) if isinstance(services, list) and services else "your services"

    if touchpoint == 2:
        subject = f"Re: {first_name} — quick follow-up on {company_name}'s new site"
        body = f"""<p>Hey {first_name},</p>

<p>Just bumping this to the top of your inbox. I built {company_name} a custom website — no charge, no catch. Just wanted to show you what's possible.</p>

<p><a href="{spec_url}" style="color: #D4922A; font-weight: 600;">Click here to see it →</a></p>

<p>It's built specifically for {services_str} in {location} — not a template. Real SEO, real mobile optimization, real lead generation.</p>

<p>Worth a quick 10-minute call to walk through it?</p>

<div style="margin-top: 32px; padding-top: 16px; border-top: 1px solid #eee; color: #666; font-size: 14px;">
    <p>Ted</p>
</div>"""

    elif touchpoint == 3:
        pain_point = pain_points[0] if pain_points else "missed calls and slow response times"
        subject = f"{first_name} — {pain_point} is costing {company_name} real money"
        body = f"""<p>Hey {first_name},</p>

<p>I've been looking at {company_name}'s online presence and noticed something that's probably costing you jobs: <strong>{pain_point}</strong>.</p>

<p>Here's the math: the average HVAC service call is $908. If you're losing even 2-3 calls a month because customers can't find you or your site doesn't convert — that's $2,700-$3,000/month walking out the door.</p>

<p>I already built you a site that fixes this. <a href="{spec_url}" style="color: #D4922A; font-weight: 600;">Take a look →</a></p>

<p>It's got click-to-call everywhere, mobile-first design, and local SEO built in for {location}. The kind of site that turns searchers into callers.</p>

<p>Happy to walk you through it — 10 minutes, no pressure.</p>

<div style="margin-top: 32px; padding-top: 16px; border-top: 1px solid #eee; color: #666; font-size: 14px;">
    <p>Ted</p>
</div>"""

    elif touchpoint == 4:
        subject = f"Closing the loop — {company_name}'s website"
        body = f"""<p>Hey {first_name},</p>

<p>I know you're busy running {company_name}, so I'll keep this short.</p>

<p>I built a custom website for your business a couple weeks ago and wanted to share it one last time before I archive it: <a href="{spec_url}" style="color: #D4922A; font-weight: 600;">{spec_url}</a></p>

<p>If the timing's not right, no worries at all. But if you ever want to upgrade {company_name}'s online presence, the offer stands.</p>

<p>Either way, best of luck with the business.</p>

<div style="margin-top: 32px; padding-top: 16px; border-top: 1px solid #eee; color: #666; font-size: 14px;">
    <p>Ted</p>
</div>"""

    else:
        print(f"Error: Invalid touchpoint {touchpoint}. Must be 2, 3, or 4.", file=sys.stderr)
        return None

    # Wrap in email HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      line-height: 1.6;
      color: #1a1a1a;
      max-width: 600px;
      margin: 0 auto;
      padding: 20px;
      font-size: 15px;
    }}
    p {{
      margin: 0 0 16px 0;
    }}
    a {{
      color: #D4922A;
    }}
  </style>
</head>
<body>
{body}
</body>
</html>"""

    # Write files
    html_filename = f"followup-touch{touchpoint}.html"
    meta_filename = f"followup-touch{touchpoint}-meta.json"

    html_path = os.path.join(output_dir, html_filename)
    meta_path = os.path.join(output_dir, meta_filename)

    with open(html_path, "w") as f:
        f.write(html)

    meta = {
        "to": email,
        "subject": subject,
        "html_file": html_path,
        "touchpoint": touchpoint,
        "company_name": company_name,
        "first_name": first_name,
        "spec_url": spec_url,
        "attachments": [],
    }

    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"Touch {touchpoint} generated:")
    print(f"  HTML: {html_path}")
    print(f"  Meta: {meta_path}")
    print(f"  Subject: {subject}")

    return {
        "html_path": html_path,
        "meta_path": meta_path,
        "subject": subject,
        "touchpoint": touchpoint,
    }


def main():
    parser = argparse.ArgumentParser(description="Generate follow-up emails for spec site pipeline")
    parser.add_argument("--research", required=True, help="Path to research.json")
    parser.add_argument("--touchpoint", type=int, choices=[2, 3, 4], help="Which follow-up (2=Day 3, 3=Day 7, 4=Day 14)")
    parser.add_argument("--all", action="store_true", help="Generate all follow-ups (2, 3, 4)")
    parser.add_argument("--spec_url", required=True, help="Live spec site URL")
    parser.add_argument("--output_dir", required=True, help="Output directory")

    args = parser.parse_args()

    with open(args.research, "r") as f:
        research_data = json.load(f)

    if args.all:
        for tp in [2, 3, 4]:
            generate_followup(research_data, tp, args.spec_url, args.output_dir)
        print("\nAll follow-ups generated!")
    elif args.touchpoint:
        generate_followup(research_data, args.touchpoint, args.spec_url, args.output_dir)
    else:
        parser.error("Must specify --touchpoint or --all")


if __name__ == "__main__":
    main()
