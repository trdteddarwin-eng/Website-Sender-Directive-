#!/usr/bin/env python3
"""
Generate a personalized outreach email for the spec site pipeline.

Uses Claude Haiku to personalize subject line and opening paragraph,
then builds a full HTML email with before/after screenshots embedded as CID images.

Usage:
    python3 execution/generate_outreach_email.py \
        --company_data .tmp/acme-hvac/research.json \
        --old_screenshot .tmp/acme-hvac/old-site.png \
        --new_screenshot .tmp/acme-hvac/new-site.png \
        --output_dir .tmp/acme-hvac/

Outputs:
    - {output_dir}/outreach-email.html  (email HTML with cid: image refs)
    - {output_dir}/email-meta.json      (subject, to, attachment manifest)
"""

import os
import sys
import json
import argparse
import requests as http_requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "anthropic/claude-3-5-haiku"


def generate_email(company_data, old_screenshot_path, new_screenshot_path, output_dir):
    """
    Generate a personalized outreach email.

    Args:
        company_data: dict with company info (from research.json)
        old_screenshot_path: path to old website screenshot
        new_screenshot_path: path to new website screenshot
        output_dir: directory to write output files

    Returns:
        dict with subject, html_path, meta_path, attachments
    """
    # OPENROUTER_API_KEY is optional — falls back to template if not set

    os.makedirs(output_dir, exist_ok=True)

    # Extract key fields from research data
    company_name = company_data.get("company_name", "your company")
    first_name = company_data.get("first_name", "there")
    website = company_data.get("website", "")
    city = company_data.get("city", "")
    state = company_data.get("state", "")
    services = company_data.get("services", [])
    pain_points = company_data.get("pain_points", [])
    roi_estimate = company_data.get("roi_estimate", "")
    icebreaker = company_data.get("icebreaker", "")
    reviews_data = company_data.get("reviews", {})
    average_rating = reviews_data.get("average_rating", None) if isinstance(reviews_data, dict) else None
    common_complaints = reviews_data.get("common_complaints", []) if isinstance(reviews_data, dict) else []

    # Format services as string
    if isinstance(services, list):
        services_str = ", ".join(services[:5]) if services else "HVAC services"
    else:
        services_str = str(services) if services else "HVAC services"

    # Format pain points
    pain_points_str = ", ".join(pain_points[:3]) if pain_points else "website issues"

    location = f"{city}, {state}" if city and state else city or state or ""

    # Ask Claude Haiku to generate the personalized content
    prompt = f"""You are writing a cold outreach email for Ted, a web designer who builds high-converting websites for HVAC contractors. He already built a new spec website for this company — no payment required, it's a free sample to show what's possible.

COMPANY INFO:
- Company: {company_name}
- Contact: {first_name}
- Location: {location}
- Website: {website}
- Services: {services_str}
- Google rating: {average_rating}/5 stars
- Common complaints from reviews: {', '.join(common_complaints) if common_complaints else 'N/A'}
- Pain points: {pain_points_str}
- ROI estimate: {roi_estimate}

TASK: Generate these 3 things as JSON:

1. "subject" — Email subject line. Pattern: "{{first_name}} — [specific observation about their current site] (we built you a new one)"
   - Must be personal, specific, attention-grabbing
   - Reference something concrete about their current website or business
   - Keep under 70 chars

2. "opening" — Opening 2-3 sentences after "Hey {{first_name}},"
   - Reference a SPECIFIC issue with their current website (not generic)
   - Include a real stat about online search behavior for HVAC customers
   - Connect to revenue they're losing

3. "differentiators" — 3 bullet points about what makes the new site different
   - Each should be specific to THIS company, not generic
   - Include at least one real stat (CTR, conversion rate, etc.)
   - Reference their specific services or market

OUTPUT FORMAT (valid JSON only):
{{
    "subject": "...",
    "opening": "...",
    "differentiators": ["...", "...", "..."]
}}"""

    personalized = None
    if OPENROUTER_API_KEY:
        try:
            resp = http_requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": MODEL,
                    "max_tokens": 1000,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=30,
            )
            resp.raise_for_status()
            response_text = resp.json()["choices"][0]["message"]["content"].strip()

            # Clean markdown code blocks
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                start = 1
                end = len(lines) - 1
                for i, line in enumerate(lines):
                    if i > 0 and line.strip() == "```":
                        end = i
                        break
                response_text = "\n".join(lines[start:end])

            personalized = json.loads(response_text)
        except Exception as e:
            print(f"Warning: OpenRouter API failed ({e}), using fallback template", file=sys.stderr)
            personalized = None

    if not personalized:
        # Fallback: generate template content without API
        personalized = {
            "subject": f"{first_name} — we built {company_name} a new website",
            "opening": f"Your current website at {website} could be converting more visitors into customers. 97% of consumers search online for local services before making a call — and first impressions matter.",
            "differentiators": [
                f"SEO built in from day one — structured data, schema markup, local SEO signals for {location}",
                f"Designed for lead generation — click-to-call, emergency CTA, mobile-first layout for {services_str}",
                "Customer-facing content — real services, real reviews, real conversion copy",
            ],
        }

    subject = personalized.get("subject", f"{first_name} — we built {company_name} a new website")
    opening = personalized.get("opening", f"Your current website at {website} could be converting more visitors into customers.")
    differentiators = personalized.get("differentiators", [
        "SEO built in from day one — structured data, schema markup, local SEO signals",
        "Designed for lead generation — click-to-call, emergency CTA, mobile-first",
        "Customer-facing content — real services, real reviews, real conversion copy",
    ])

    # Build the HTML email
    diff_html = ""
    for diff in differentiators:
        # Split on first — or - to get bold title and description
        if " — " in diff:
            title, desc = diff.split(" — ", 1)
            diff_html += f'      <li><strong>{title}</strong> — {desc}</li>\n'
        elif " - " in diff:
            title, desc = diff.split(" - ", 1)
            diff_html += f'      <li><strong>{title}</strong> — {desc}</li>\n'
        else:
            diff_html += f"      <li>{diff}</li>\n"

    # Determine if we have both screenshots for before/after
    has_old = old_screenshot_path and os.path.exists(old_screenshot_path)
    has_new = new_screenshot_path and os.path.exists(new_screenshot_path)

    # Check if old screenshot is usable (not maintenance/error/login page)
    if has_old:
        try:
            sys.path.insert(0, os.path.dirname(__file__))
            from screenshot_website import is_screenshot_usable
            if not is_screenshot_usable(old_screenshot_path):
                print(f"Old site screenshot unusable (maintenance/error page), skipping")
                has_old = False
        except ImportError:
            pass  # If can't import, assume usable

    # Build screenshot sections — inline styles for email client compatibility
    # width="600" + max-width:100% ensures proper sizing on both desktop and mobile
    img_style = 'display:block;width:100%;max-width:600px;height:auto;'

    screenshots_html = ""
    if has_old and has_new:
        screenshots_html = f"""
  <div class="screenshot-container">
    <img src="cid:old-site-screenshot" alt="{company_name} - Current Website" width="600" style="{img_style}" />
    <div class="screenshot-label">Current: {website}</div>
  </div>

  <div style="text-align: center; margin: 16px 0; font-size: 24px; color: #D4922A;">&#8595;</div>

  <div class="screenshot-container">
    <img src="cid:new-site-screenshot" alt="{company_name} - New Website Preview" width="600" style="{img_style}" />
    <div class="screenshot-label">Preview: {company_name} — New Website (SEO-optimized, mobile-first, conversion-focused)</div>
  </div>"""
    elif has_new:
        screenshots_html = f"""
  <div class="screenshot-container">
    <img src="cid:new-site-screenshot" alt="{company_name} - New Website Preview" width="600" style="{img_style}" />
    <div class="screenshot-label">Preview: {company_name} — New Website (SEO-optimized, mobile-first, conversion-focused)</div>
  </div>"""

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
    .screenshot-container {{
      margin: 24px 0;
      border-radius: 12px;
      overflow: hidden;
      border: 1px solid #e5e5e5;
      box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    }}
    .screenshot-container img {{
      width: 100%;
      display: block;
    }}
    .screenshot-label {{
      background: #f8f8f8;
      padding: 10px 16px;
      font-size: 12px;
      color: #888;
      text-align: center;
    }}
    .highlight {{
      color: #D4922A;
      font-weight: 600;
    }}
    .changes-section {{
      margin: 20px 0;
      padding: 16px 20px;
      background: #fafafa;
      border-left: 3px solid #D4922A;
      border-radius: 0 8px 8px 0;
    }}
    .changes-section .changes-title {{
      font-size: 14px;
      font-weight: 700;
      color: #0C2340;
      margin: 0 0 10px 0;
    }}
    .changes-section ul {{
      margin: 0;
      padding: 0 0 0 18px;
      font-size: 14px;
      color: #333;
    }}
    .changes-section li {{
      margin-bottom: 8px;
    }}
    .changes-section li:last-child {{
      margin-bottom: 0;
    }}
    .changes-section strong {{
      color: #0C2340;
    }}
    .stat {{
      display: inline-block;
      background: #f0f0f0;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 13px;
      font-weight: 600;
      color: #0C2340;
    }}
    .signature {{
      margin-top: 32px;
      padding-top: 16px;
      border-top: 1px solid #eee;
      color: #666;
      font-size: 14px;
    }}
  </style>
</head>
<body>
  <p>Hey {first_name},</p>

  <p>{opening}</p>

  <p>We built {company_name} a new website from scratch — SEO-optimized, mobile-first, designed to convert. Not a template. We researched your market, your reviews, and your competitors, and built something that puts you ahead.</p>
{screenshots_html}

  <div class="changes-section">
    <p class="changes-title">What makes this different from a generic contractor site:</p>
    <ul>
{diff_html}    </ul>
  </div>

  <p>The average HVAC job is <span class="highlight">$908</span>. Even one extra lead per week from a better website = <span class="highlight">$47K/year</span>. Worth a quick 10-minute call to walk through it?</p>

  <div class="signature">
    <p>Ted</p>
  </div>
  <img src="cid:tracking-pixel" alt="" width="1" height="1" style="display:none;" />
</body>
</html>"""

    # Write HTML file
    html_path = os.path.join(output_dir, "outreach-email.html")
    with open(html_path, "w") as f:
        f.write(html)
    print(f"Email HTML saved: {html_path}")

    # Build attachment manifest
    attachments = []
    if has_old:
        attachments.append({"path": old_screenshot_path, "content_id": "old-site-screenshot"})
    if has_new:
        attachments.append({"path": new_screenshot_path, "content_id": "new-site-screenshot"})

    # Write metadata
    meta = {
        "to": company_data.get("email", ""),
        "subject": subject,
        "html_file": html_path,
        "attachments": attachments,
        "company_name": company_name,
        "first_name": first_name,
    }

    meta_path = os.path.join(output_dir, "email-meta.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"Email meta saved: {meta_path}")

    return {
        "subject": subject,
        "html_path": html_path,
        "meta_path": meta_path,
        "attachments": attachments,
    }


def main():
    parser = argparse.ArgumentParser(description="Generate personalized outreach email for spec site pipeline")
    parser.add_argument("--company_data", required=True, help="Path to research.json with company data")
    parser.add_argument("--old_screenshot", help="Path to old website screenshot PNG")
    parser.add_argument("--new_screenshot", help="Path to new website screenshot PNG")
    parser.add_argument("--output_dir", required=True, help="Output directory for email files")

    args = parser.parse_args()

    # Load company data
    with open(args.company_data, "r") as f:
        company_data = json.load(f)

    result = generate_email(
        company_data=company_data,
        old_screenshot_path=args.old_screenshot,
        new_screenshot_path=args.new_screenshot,
        output_dir=args.output_dir,
    )

    if result:
        print(f"\nDone! Subject: {result['subject']}")
    else:
        print("Failed to generate email")
        sys.exit(1)


if __name__ == "__main__":
    main()
