#!/usr/bin/env python3
"""
Analyze website content + Google reviews to identify pain points and ROI opportunities.

Uses Claude to analyze business data and generate:
- Pain points from reviews
- Automation/AI voice agent opportunities
- ROI estimates
- Personalized icebreakers

Can be called via CLI with JSON files or imported and called directly.
"""

import os
import sys
import json
import argparse
import time
import anthropic
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MAX_RETRIES = 3
MODEL = "claude-3-5-haiku-20241022"


def analyze_lead(company_name: str, website_summary: str, services: str, reviews: str) -> dict:
    """
    Analyze a lead using Claude to identify pain points and ROI opportunities.

    Args:
        company_name: Name of the business
        website_summary: Summary of website content
        services: Services offered by the business
        reviews: Google reviews text (formatted)

    Returns:
        dict with pain_points, automation_opportunities, roi_estimate, icebreaker
    """
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not set in .env")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""You are analyzing a local service business for sales opportunities.

BUSINESS INFO:
- Name: {company_name}
- Website content: {website_summary}
- Services: {services}

GOOGLE REVIEWS:
{reviews}

TASK:
1. Identify 2-3 pain points from reviews (slow response, missed calls, scheduling, etc.)
2. Suggest automation/AI voice agent opportunities that solve these pain points
3. Calculate rough ROI estimate (jobs lost per week/month from these issues)
4. Write a 1-2 sentence icebreaker that:
   - References a SPECIFIC pain point from their reviews
   - Ties to ROI (money/time they're losing)
   - Offers AI voice agent or automation as solution

OUTPUT FORMAT (return valid JSON only):
{{
  "pain_points": [...],
  "automation_opportunities": [...],
  "roi_estimate": "...",
  "icebreaker": "..."
}}"""

    for retry in range(MAX_RETRIES):
        try:
            message = client.messages.create(
                model=MODEL,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            response_text = message.content[0].text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                lines = response_text.split('\n')
                # Find the closing ``` and extract content between
                start_idx = 1
                end_idx = len(lines) - 1
                for i, line in enumerate(lines):
                    if i > 0 and line.strip() == "```":
                        end_idx = i
                        break
                response_text = '\n'.join(lines[start_idx:end_idx])

            result = json.loads(response_text)

            # Validate expected fields
            expected_fields = ["pain_points", "automation_opportunities", "roi_estimate", "icebreaker"]
            for field in expected_fields:
                if field not in result:
                    result[field] = [] if field in ["pain_points", "automation_opportunities"] else ""

            return result

        except anthropic.RateLimitError:
            if retry < MAX_RETRIES - 1:
                wait_time = (2 ** retry) * 2
                print(f"Rate limited, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise RuntimeError(f"Rate limit exceeded after {MAX_RETRIES} retries")

        except json.JSONDecodeError as e:
            if retry < MAX_RETRIES - 1:
                print(f"JSON parse error, retrying... ({e})")
                time.sleep(1)
            else:
                # Return empty result on persistent parse failure
                return {
                    "pain_points": [],
                    "automation_opportunities": [],
                    "roi_estimate": "",
                    "icebreaker": "",
                    "error": f"Failed to parse response: {str(e)}"
                }

        except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as e:
            # 401/403 — API key expired or invalid. Return template JSON with error flag.
            print(f"Auth error (key expired/invalid): {e}", file=sys.stderr)
            return {
                "pain_points": ["Unable to analyze — API key invalid"],
                "automation_opportunities": [],
                "roi_estimate": "",
                "icebreaker": "",
                "error": f"auth_failed: {str(e)}",
                "needs_manual_analysis": True,
            }

        except Exception as e:
            if retry < MAX_RETRIES - 1:
                print(f"Error: {e}, retrying...")
                time.sleep(1)
            else:
                return {
                    "pain_points": [],
                    "automation_opportunities": [],
                    "roi_estimate": "",
                    "icebreaker": "",
                    "error": f"failed: {str(e)}",
                    "needs_manual_analysis": True,
                }


def load_json_file(file_path: str) -> dict:
    """Load and parse a JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze website content + Google reviews to identify pain points and ROI opportunities"
    )

    # File-based input
    parser.add_argument("--website_data", help="Path to JSON file with website data")
    parser.add_argument("--reviews_data", help="Path to JSON file with reviews data")

    # Direct text input
    parser.add_argument("--website_text", help="Website summary text (direct input)")
    parser.add_argument("--reviews_text", help="Reviews text (direct input)")

    # Required for both modes
    parser.add_argument("--company_name", help="Company name (required if not in JSON)")
    parser.add_argument("--services", help="Services offered (optional, extracted from website if not provided)")

    # Output
    parser.add_argument("--output", help="Output JSON file path")

    args = parser.parse_args()

    if not ANTHROPIC_API_KEY:
        print("Error: ANTHROPIC_API_KEY not set in .env")
        sys.exit(1)

    # Determine input mode and extract data
    company_name = args.company_name
    website_summary = ""
    services = args.services or ""
    reviews = ""

    # Load from JSON files if provided
    if args.website_data:
        website_json = load_json_file(args.website_data)
        website_summary = website_json.get("summary", website_json.get("content", ""))
        if not company_name:
            company_name = website_json.get("company_name", "")
        if not services:
            services = website_json.get("services", "")

    if args.reviews_data:
        reviews_json = load_json_file(args.reviews_data)
        # Handle both list of reviews and pre-formatted text
        if isinstance(reviews_json, list):
            reviews = "\n\n".join([
                f"Rating: {r.get('rating', 'N/A')}/5\n{r.get('text', r.get('review', ''))}"
                for r in reviews_json
            ])
        elif isinstance(reviews_json, dict):
            if "reviews" in reviews_json:
                review_list = reviews_json["reviews"]
                reviews = "\n\n".join([
                    f"Rating: {r.get('rating', 'N/A')}/5\n{r.get('text', r.get('review', ''))}"
                    for r in review_list
                ])
            else:
                reviews = reviews_json.get("text", str(reviews_json))
        else:
            reviews = str(reviews_json)

    # Override with direct text if provided
    if args.website_text:
        website_summary = args.website_text

    if args.reviews_text:
        reviews = args.reviews_text

    # Validate required inputs
    if not company_name:
        print("Error: --company_name is required (or must be in website_data JSON)")
        sys.exit(1)

    if not website_summary and not reviews:
        print("Error: At least one of website data or reviews data is required")
        sys.exit(1)

    # Run analysis
    print(f"Analyzing {company_name}...")
    start_time = time.time()

    try:
        result = analyze_lead(
            company_name=company_name,
            website_summary=website_summary,
            services=services,
            reviews=reviews
        )

        elapsed = time.time() - start_time
        print(f"Analysis complete in {elapsed:.1f}s")

        # Output results
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2)
            print(f"Results saved to {args.output}")
        else:
            print("\nResults:")
            print(json.dumps(result, indent=2))

        return result

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
