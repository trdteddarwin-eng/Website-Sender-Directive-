#!/usr/bin/env python3
"""
Generate a complete spec site HTML via OpenRouter API.

Replaces the Designer agent's /frontend-design skill call.
Single API call → complete self-contained HTML file.

Usage:
    python3 execution/generate_spec_site.py \
        --research .tmp/acme-hvac/research.json \
        --palette_index 0 \
        --hero_style_index 0 \
        --output .tmp/acme-hvac/index.html

Prerequisites:
    - OPENROUTER_API_KEY in .env
"""

import os
import sys
import json
import argparse
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "anthropic/claude-sonnet-4"

PALETTES = [
    {"name": "Navy/Amber", "primary": "#0B1D3A", "accent": "#D4922A", "light": "#F5F0E8", "text_on_primary": "#FFFFFF"},
    {"name": "Forest/Gold", "primary": "#1B4332", "accent": "#D4A22A", "light": "#F0F5EC", "text_on_primary": "#FFFFFF"},
    {"name": "Charcoal/Red", "primary": "#2D2D2D", "accent": "#C0392B", "light": "#F5F0F0", "text_on_primary": "#FFFFFF"},
    {"name": "Deep Blue/Orange", "primary": "#1A365D", "accent": "#E07C24", "light": "#F0F3F8", "text_on_primary": "#FFFFFF"},
    {"name": "Dark Teal/Yellow", "primary": "#0D4F4F", "accent": "#E8B930", "light": "#F0F5F5", "text_on_primary": "#FFFFFF"},
]

HERO_STYLES = [
    "full-bleed: Gradient background filling entire viewport, centered text with bold CTA button below",
    "split-layout: Text content on left side, decorative gradient/shape on right side, side-by-side",
    "gradient-overlay: Subtle background pattern or decorative shapes with text overlaid on top",
    "diagonal-split: Angled/clipped sections creating dynamic diagonal division between content areas",
]


def generate_spec_site(research_data, palette_index, hero_style_index, output_path):
    """Generate a complete spec site HTML file via OpenRouter API.

    Args:
        research_data: dict from research.json
        palette_index: int (0-4) for color palette
        hero_style_index: int (0-3) for hero style
        output_path: path to write index.html

    Returns:
        True on success, False on failure
    """
    if not OPENROUTER_API_KEY:
        print("Error: OPENROUTER_API_KEY not set in .env", file=sys.stderr)
        return False

    palette = PALETTES[palette_index % len(PALETTES)]
    hero_style = HERO_STYLES[hero_style_index % len(HERO_STYLES)]

    # Extract research data
    company_name = research_data.get("company_name", "HVAC Company")
    phone = research_data.get("phone", "")
    website = research_data.get("website", "")
    city = research_data.get("city", "")
    state = research_data.get("state", "")
    services = research_data.get("services", [])
    if isinstance(services, list):
        services_str = "\n".join(f"- {s}" for s in services[:8])
    else:
        services_str = str(services)

    reviews = research_data.get("reviews", {})
    if isinstance(reviews, dict):
        avg_rating = reviews.get("average_rating", "")
        review_count = reviews.get("review_count", "")
        review_list = reviews.get("reviews", [])
    else:
        avg_rating = ""
        review_count = ""
        review_list = []

    reviews_str = ""
    for r in review_list[:5]:
        if isinstance(r, dict):
            name = r.get("author", r.get("name", "Customer"))
            text = r.get("text", r.get("review", ""))
            rating = r.get("rating", 5)
            reviews_str += f"- {name} ({rating}/5): \"{text}\"\n"
        elif isinstance(r, str):
            reviews_str += f"- {r}\n"

    pain_points = research_data.get("pain_points", [])
    pain_str = "\n".join(f"- {p}" for p in pain_points[:5]) if pain_points else "N/A"

    address = research_data.get("address", "")
    if not address and city and state:
        address = f"{city}, {state}"

    about = research_data.get("about", research_data.get("company_description", ""))
    years = research_data.get("years_in_business", "")

    prompt = f"""Build a COMPLETE, self-contained, production-quality HTML file for an HVAC contractor's website.
This is a spec/demo site to show the business owner what a modern site could look like.

COMPANY DATA:
- Company Name: {company_name}
- Phone: {phone}
- Address: {address}
- City/State: {city}, {state}
- Website: {website}
- Google Rating: {avg_rating}/5 ({review_count} reviews)
- Years in Business: {years}
- About: {about}

SERVICES:
{services_str}

REAL CUSTOMER REVIEWS (use verbatim):
{reviews_str}

DESIGN SPECIFICATIONS:
- Color Palette: {palette['name']}
  - Primary: {palette['primary']}
  - Accent: {palette['accent']}
  - Light Background: {palette['light']}
  - Text on Primary: {palette['text_on_primary']}
- Hero Style: {hero_style}

REQUIRED SECTIONS (in this order):
1. HEADER: Sticky nav with company name, navigation links, phone number with click-to-call
2. HERO: {hero_style} — headline about their core value prop, subheadline, prominent CTA button, phone number
3. TRUST BAR: Google rating stars, review count, years in business, "Licensed & Insured"
4. SERVICES: Grid/cards of their actual services (from data above), icons, brief descriptions
5. ABOUT: Company story, why choose them, team expertise
6. REVIEWS: Real customer reviews verbatim (from data above) with star ratings, reviewer names
7. EMERGENCY CTA: Bold section — "24/7 Emergency Service" with phone number, contrasting background
8. SERVICE AREA: Mention {city}, {state} and surrounding areas
9. FOOTER: Phone, address, hours, navigation links, copyright

CRITICAL RULES:
1. Phone number ({phone}) must appear in: header, hero, emergency CTA, and footer — all as click-to-call links (tel:)
2. ALL content must be customer-facing (written for the homeowner/facility manager, NOT the web designer)
3. Use ONLY the reviews provided above — do not fabricate quotes or reviewer names
4. Self-contained HTML: all CSS inline in <style> tags, Google Fonts via CDN link only
5. Mobile-responsive with CSS media queries
6. Working hamburger menu for mobile — include the JavaScript toggle code in a <script> tag
7. NO scroll-reveal animations (no opacity:0 with IntersectionObserver). Use CSS page-load animations only or skip animations.
8. Professional typography using Inter font from Google Fonts
9. Minimum 800 lines of HTML — this should be a FULL, detailed, polished site
10. Every CTA button should either call the phone or scroll to a contact section
11. Use semantic HTML (header, nav, main, section, footer)
12. Include meta viewport tag for mobile
13. If reviews data is empty, include a "Be Our First Reviewer" CTA instead

OUTPUT: Return ONLY the complete HTML file content. No markdown, no code fences, no explanation.
Start with <!DOCTYPE html> and end with </html>."""

    print(f"Generating spec site for {company_name}...")
    print(f"  Palette: {palette['name']} | Hero: {hero_style.split(':')[0]}")

    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "max_tokens": 16000,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=120,
        )
        resp.raise_for_status()
        html = resp.json()["choices"][0]["message"]["content"].strip()

        # Strip markdown code fences if present
        if html.startswith("```"):
            lines = html.split("\n")
            start = 1
            end = len(lines)
            for i in range(len(lines) - 1, 0, -1):
                if lines[i].strip() == "```":
                    end = i
                    break
            html = "\n".join(lines[start:end])

        # Ensure it starts with DOCTYPE
        if not html.lower().startswith("<!doctype"):
            # Find the DOCTYPE
            idx = html.lower().find("<!doctype")
            if idx >= 0:
                html = html[idx:]

        # Validate basic structure
        if "<html" not in html.lower() or "<body" not in html.lower():
            print("Error: Generated HTML is missing basic structure", file=sys.stderr)
            return False

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w") as f:
            f.write(html)

        size_kb = len(html) / 1024
        print(f"  Spec site generated: {output_path} ({size_kb:.1f} KB)")
        return True

    except requests.exceptions.Timeout:
        print("Error: OpenRouter API timed out (120s)", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Generate spec site HTML via OpenRouter API")
    parser.add_argument("--research", required=True, help="Path to research.json")
    parser.add_argument("--palette_index", type=int, default=0, help="Palette index (0-4)")
    parser.add_argument("--hero_style_index", type=int, default=0, help="Hero style index (0-3)")
    parser.add_argument("--output", required=True, help="Output path for index.html")

    args = parser.parse_args()

    with open(args.research, "r") as f:
        research_data = json.load(f)

    success = generate_spec_site(
        research_data=research_data,
        palette_index=args.palette_index,
        hero_style_index=args.hero_style_index,
        output_path=args.output,
    )

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
