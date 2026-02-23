#!/usr/bin/env python3
"""
Research the top 12 most-sold AI automations for small/medium businesses.
Calls OpenRouter API (Claude Sonnet) and saves structured JSON output.
"""

import json
import os
import sys
from typing import Optional

import requests
from dotenv import load_dotenv


def load_api_key() -> str:
    """Load OPENROUTER_API_KEY from .env file."""
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    load_dotenv(env_path)
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        print("ERROR: OPENROUTER_API_KEY not found in .env")
        sys.exit(1)
    return key


def research_automations(api_key: str) -> Optional[dict]:
    """Call OpenRouter API to research top AI automations for SMBs."""

    prompt = """You are an expert AI business consultant. Return a JSON object with the key "automations" containing an array of the top 12 most-sold AI automations for small and medium businesses in 2025-2026.

For each automation, provide:
- "name": the automation name (e.g., "AI Receptionist", "Lead Qualification Chatbot")
- "tagline": a short, punchy selling line (max 10 words)
- "pain_point": the specific business problem it solves (1-2 sentences)
- "roi_stat": a realistic, specific ROI statistic (e.g., "Saves 23 hours/week on average", "Increases lead conversion by 35%")
- "steps": an array of 6-7 flowchart steps describing how the automation works end-to-end. Each step has:
  - "label": short step name (3-5 words)
  - "description": what happens at this step (1 sentence)
  - "icon": an icon suggestion (e.g., "phone", "brain", "envelope", "calendar", "chart", "robot", "database", "lightning", "globe", "shield", "clock", "target")
  - "type": one of "trigger", "ai", or "outcome"

Focus on automations that agencies actually sell and deploy for SMBs — not enterprise solutions. Think: dental offices, law firms, real estate agencies, home services, e-commerce stores, restaurants, med spas, etc.

Order them by popularity/sales volume (most sold first).

Return ONLY valid JSON. No markdown, no code fences, no explanation."""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://ted-workspace.local",
        "X-Title": "Ted Workspace - Automation Research",
    }

    payload = {
        "model": "anthropic/claude-sonnet-4",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 8000,
        "temperature": 0.7,
        "response_format": {"type": "json_object"},
    }

    print("Calling OpenRouter API (anthropic/claude-sonnet-4)...")
    print("This may take up to 2 minutes...")

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
    except requests.exceptions.Timeout:
        print("ERROR: API call timed out after 120s")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"ERROR: HTTP {response.status_code}: {response.text}")
        return None
    except Exception as e:
        print(f"ERROR: Request failed: {e}")
        return None

    data = response.json()

    # Extract content from OpenRouter response
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        print(f"ERROR: Unexpected API response structure: {e}")
        print(f"Response: {json.dumps(data, indent=2)[:500]}")
        return None

    # Parse JSON from content
    try:
        result = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse JSON from API response: {e}")
        print(f"Raw content (first 500 chars): {content[:500]}")
        return None

    # Validate structure
    if "automations" not in result:
        print("WARNING: Response missing 'automations' key. Wrapping...")
        if isinstance(result, list):
            result = {"automations": result}
        else:
            print(f"ERROR: Unexpected response format: {list(result.keys())}")
            return None

    automations = result["automations"]
    print(f"Received {len(automations)} automations from API.")

    # Validate each automation has required fields
    required_fields = ["name", "tagline", "pain_point", "roi_stat", "steps"]
    for i, auto in enumerate(automations):
        missing = [f for f in required_fields if f not in auto]
        if missing:
            print(f"WARNING: Automation #{i+1} missing fields: {missing}")

    return result


def save_output(data: dict, output_path: str) -> None:
    """Save research output to JSON file, creating directories as needed."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved to: {output_path}")


def main() -> None:
    """Main entry point."""
    workspace = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_path = os.path.join(workspace, ".tmp", "automation_research.json")

    api_key = load_api_key()
    result = research_automations(api_key)

    if result is None:
        print("FAILED: No valid data returned from API.")
        sys.exit(1)

    save_output(result, output_path)

    # Print summary
    print("\n--- Summary ---")
    for i, auto in enumerate(result.get("automations", []), 1):
        print(f"  {i:2d}. {auto.get('name', 'N/A')} — {auto.get('tagline', 'N/A')}")

    print(f"\nTotal: {len(result.get('automations', []))} automations researched.")
    print("Done.")


if __name__ == "__main__":
    main()
