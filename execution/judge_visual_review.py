#!/usr/bin/env python3
"""
Judge Visual Review — sends spec site screenshot to Kimi K2.5 via OpenRouter
for multimodal design evaluation.

Usage:
    python3 execution/judge_visual_review.py \
        --screenshot .tmp/acme-hvac/new-site.png \
        --research .tmp/acme-hvac/research.json \
        --output .tmp/acme-hvac/visual-review.json

Prerequisites:
    - OPENROUTER_API_KEY in .env
"""

import os
import sys
import json
import base64
import argparse
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "moonshotai/kimi-k2.5"


def encode_image(image_path):
    """Base64-encode an image file for the API."""
    with open(image_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    ext = os.path.splitext(image_path)[1].lower()
    mime = {"png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}.get(ext, "image/png")
    return f"data:{mime};base64,{data}"


def run_visual_review(screenshot_path, research_data, output_path):
    """Send screenshot to Kimi K2.5 for visual design review.

    Returns dict with:
        - visual_score (0-100)
        - strengths (list)
        - issues (list)
        - overall_impression (str)
        - recommendation (str: "pass" | "needs_revision" | "fail")
    """
    if not OPENROUTER_API_KEY:
        print("Error: OPENROUTER_API_KEY not set", file=sys.stderr)
        return None

    if not os.path.exists(screenshot_path):
        print(f"Error: Screenshot not found: {screenshot_path}", file=sys.stderr)
        return None

    company_name = research_data.get("company_name", "Unknown")
    phone = research_data.get("phone", "")
    city = research_data.get("city", "")
    services = research_data.get("services", [])
    services_str = ", ".join(services[:5]) if isinstance(services, list) else str(services)

    image_data = encode_image(screenshot_path)

    prompt = f"""You are a senior web designer reviewing a spec site screenshot for a client pitch.

CONTEXT:
- Company: {company_name}
- Location: {city}
- Phone: {phone}
- Key services: {services_str}
- Purpose: This spec site is shown to business owners to win their website redesign project

REVIEW THIS SCREENSHOT and evaluate the design quality. Score each category 0-10:

1. **Visual Hierarchy** — Is the most important info (phone, CTA, headline) prominent?
2. **Color & Contrast** — Do colors work together? Is text readable?
3. **Typography** — Professional, consistent font sizing and spacing?
4. **Layout & Spacing** — Well-organized sections? Good whitespace?
5. **Trust Signals** — Reviews, ratings, credentials visible?
6. **Mobile Readiness** — Does it look like it would work on mobile?
7. **Call-to-Action** — Are CTAs visible, compelling, and well-placed?
8. **Brand Consistency** — Does it feel like one cohesive site?
9. **Content Completeness** — Are all sections (hero, services, reviews, footer) present?
10. **Overall Polish** — Would a business owner be impressed seeing this?

RESPOND IN EXACT JSON FORMAT (no markdown, no code fences):
{{
    "scores": {{
        "visual_hierarchy": <0-10>,
        "color_contrast": <0-10>,
        "typography": <0-10>,
        "layout_spacing": <0-10>,
        "trust_signals": <0-10>,
        "mobile_readiness": <0-10>,
        "cta_quality": <0-10>,
        "brand_consistency": <0-10>,
        "content_completeness": <0-10>,
        "overall_polish": <0-10>
    }},
    "visual_score": <total out of 100>,
    "strengths": ["top 3 things done well"],
    "issues": ["top 3 things that need improvement, or empty if none"],
    "overall_impression": "1-2 sentence summary",
    "recommendation": "pass" or "needs_revision" or "fail"
}}"""

    print(f"Running visual review for {company_name}...")

    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": image_data}},
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
                "max_tokens": 1500,
            },
            timeout=90,
        )
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"].strip()

        # Strip code fences if model wraps them anyway
        if raw.startswith("```"):
            lines = raw.split("\n")
            start = 1
            end = len(lines)
            for i in range(len(lines) - 1, 0, -1):
                if lines[i].strip() == "```":
                    end = i
                    break
            raw = "\n".join(lines[start:end])

        review = json.loads(raw)

        # Validate expected fields
        if "visual_score" not in review:
            scores = review.get("scores", {})
            review["visual_score"] = sum(scores.values())
        if "recommendation" not in review:
            s = review["visual_score"]
            review["recommendation"] = "pass" if s >= 70 else ("needs_revision" if s >= 40 else "fail")

        # Write output
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(review, f, indent=2)

        print(f"  Visual score: {review['visual_score']}/100 — {review['recommendation']}")
        print(f"  Impression: {review.get('overall_impression', '')}")
        return review

    except json.JSONDecodeError as e:
        print(f"Error: Could not parse K2.5 response as JSON: {e}", file=sys.stderr)
        print(f"  Raw response: {raw[:300]}", file=sys.stderr)
        # Return a fallback
        fallback = {
            "visual_score": -1,
            "strengths": [],
            "issues": ["Could not parse visual review response"],
            "overall_impression": "Review failed — response was not valid JSON",
            "recommendation": "needs_revision",
            "raw_response": raw[:1000],
        }
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(fallback, f, indent=2)
        return fallback

    except requests.exceptions.Timeout:
        print("Error: K2.5 API timed out (90s)", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return None


def main():
    parser = argparse.ArgumentParser(description="Judge visual review via Kimi K2.5")
    parser.add_argument("--screenshot", required=True, help="Path to spec site screenshot")
    parser.add_argument("--research", required=True, help="Path to research.json")
    parser.add_argument("--output", required=True, help="Output path for visual-review.json")

    args = parser.parse_args()

    with open(args.research) as f:
        research_data = json.load(f)

    result = run_visual_review(args.screenshot, research_data, args.output)
    if not result:
        sys.exit(1)


if __name__ == "__main__":
    main()
