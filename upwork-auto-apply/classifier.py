#!/usr/bin/env python3
"""
AI job classifier and relevance scorer for Upwork jobs.

Uses a single Claude Sonnet API call per job to score relevance (1-10)
and classify the job type (website, automation, other).
"""

import os
import sys
import json
import argparse
import requests
from typing import Optional, List, Dict, Tuple

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------

ENV_PATH = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(ENV_PATH)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
DEFAULT_MODEL = "anthropic/claude-sonnet-4-5"

DEFAULT_SKILLS_PROFILE = (
    "AI/automation, n8n workflows, voice AI agents, API integrations, "
    "Claude/GPT apps, website development, landing pages"
)

# ---------------------------------------------------------------------------
# Core classifier
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are an Upwork job evaluator. You score job relevance and classify type.

You will receive a job posting and a skills profile. Return ONLY valid JSON with these fields:
{
  "score": <integer 1-10>,
  "category": "<website|automation|other>",
  "notes": "<1-2 sentence explanation of the score>",
  "red_flags": "<any concerns, or empty string>"
}

Scoring guide:
- 9-10: Perfect match. Job explicitly asks for skills we have, good budget, clear scope.
- 7-8: Strong match. Most skills align, reasonable budget, minor gaps.
- 5-6: Partial match. Some overlap but missing key requirements or vague scope.
- 3-4: Weak match. Tangential overlap, unclear requirements, or low budget.
- 1-2: No match. Completely unrelated skills needed.

Category definitions:
- "website": Client wants a website, landing page, redesign, WordPress site, web app UI, Shopify store, or any web-based front-end deliverable.
- "automation": Client wants workflow automation, AI agents, n8n/Zapier/Make workflows, API integrations, bots, chatbots, voice AI, or backend automation.
- "other": Does not clearly fit website or automation. Could still be worth applying (e.g., consulting, data work, general AI tasks).

Red flags to note:
- Budget under $200 for significant work
- "Need it done in 24 hours" with large scope
- Asking for free work / unpaid trial
- Vague requirements with fixed budget
- Client has 0 hires or low rating
- Scope creep signals (long wishlists, no clear deliverable)

Return ONLY the JSON object. No markdown, no explanation outside the JSON."""


def score_and_classify(
    job: dict,
    model: str = DEFAULT_MODEL,
    skills_profile: Optional[str] = None,
) -> dict:
    """Score relevance (1-10) and classify job type via OpenRouter API call.

    Args:
        job: dict with keys: title, description, skills, budget, experience_level
        model: OpenRouter model ID to use
        skills_profile: string describing our skills

    Returns:
        {
            'score': int (1-10),
            'category': 'website' | 'automation' | 'other',
            'notes': str,
            'red_flags': str,
        }
    """
    profile = skills_profile or DEFAULT_SKILLS_PROFILE

    user_msg = f"""## Our Skills Profile
{profile}

## Job Posting
**Title:** {job.get('title', 'N/A')}
**Budget:** {job.get('budget', 'N/A')}
**Experience Level:** {job.get('experience_level', 'N/A')}
**Skills Required:** {job.get('skills', 'N/A')}

**Description:**
{job.get('description', 'N/A')}"""

    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "max_tokens": 512,
                "messages": [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
            },
            timeout=30,
        )
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"].strip()

        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()

        result = json.loads(raw)

        # Validate and coerce
        result["score"] = max(1, min(10, int(result.get("score", 1))))
        if result.get("category") not in ("website", "automation", "other"):
            result["category"] = "other"
        result.setdefault("notes", "")
        result.setdefault("red_flags", "")

        return result

    except json.JSONDecodeError as e:
        return {
            "score": 1,
            "category": "other",
            "notes": f"Failed to parse classifier response: {e}",
            "red_flags": f"Raw response: {raw[:200] if 'raw' in dir() else 'N/A'}",
        }
    except Exception as e:
        return {
            "score": 1,
            "category": "other",
            "notes": f"Classifier error: {e}",
            "red_flags": str(e),
        }


# ---------------------------------------------------------------------------
# Batch classifier
# ---------------------------------------------------------------------------

def score_and_classify_batch(
    jobs: List[dict],
    config: dict,
) -> Tuple[List[dict], List[dict]]:
    """Score and classify a batch of jobs.

    Args:
        jobs: list of job dicts (each with title, description, skills, budget, experience_level)
        config: pipeline config dict (uses scoring.model, scoring.min_score)

    Returns:
        (qualified_jobs, rejected_jobs) -- qualified have score >= min_score.
        Each job dict gets these keys added:
            'relevance_score', 'job_type', 'relevance_notes', 'relevance_red_flags'
    """
    scoring_cfg = config.get("scoring", {})
    model = scoring_cfg.get("model", DEFAULT_MODEL)
    min_score = scoring_cfg.get("min_score", 7)
    skills_profile = scoring_cfg.get("skills_profile", DEFAULT_SKILLS_PROFILE)

    qualified = []
    rejected = []

    for i, job in enumerate(jobs):
        print(f"  [{i + 1}/{len(jobs)}] Scoring: {job.get('title', 'N/A')[:60]}...", flush=True)

        result = score_and_classify(
            job=job,
            model=model,
            skills_profile=skills_profile,
        )

        # Attach results to the job dict
        job["relevance_score"] = result["score"]
        job["job_type"] = result["category"]
        job["relevance_notes"] = result["notes"]
        job["relevance_red_flags"] = result["red_flags"]

        if result["score"] >= min_score:
            qualified.append(job)
        else:
            rejected.append(job)

    print(f"\n  Batch complete: {len(qualified)} qualified, {len(rejected)} rejected "
          f"(min_score={min_score})")
    return qualified, rejected


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Upwork job classifier")
    sub = parser.add_subparsers(dest="command")

    # score — score a single job from JSON string or file
    score_p = sub.add_parser("score", help="Score a single job")
    score_p.add_argument("--title", required=True, help="Job title")
    score_p.add_argument("--description", required=True, help="Job description")
    score_p.add_argument("--budget", default="N/A", help="Budget")
    score_p.add_argument("--skills", default="N/A", help="Required skills (comma-sep)")
    score_p.add_argument("--experience", default="N/A", help="Experience level")
    score_p.add_argument("--model", default=DEFAULT_MODEL, help="Model to use")

    # batch — score jobs from a JSON file
    batch_p = sub.add_parser("batch", help="Score a batch of jobs from JSON file")
    batch_p.add_argument("file", help="Path to JSON file with list of job dicts")
    batch_p.add_argument("--config", default=None, help="Path to config.json")
    batch_p.add_argument("--min-score", type=int, default=None, help="Override min score")

    args = parser.parse_args()

    if args.command == "score":
        job = {
            "title": args.title,
            "description": args.description,
            "budget": args.budget,
            "skills": args.skills,
            "experience_level": args.experience,
        }
        result = score_and_classify(job, model=args.model)
        print(json.dumps(result, indent=2))

    elif args.command == "batch":
        with open(args.file) as f:
            jobs = json.load(f)

        config_path = args.config or os.path.join(os.path.dirname(__file__), "config.json")
        if os.path.exists(config_path):
            with open(config_path) as f:
                config = json.load(f)
        else:
            config = {"scoring": {"model": DEFAULT_MODEL, "min_score": 7}}

        if args.min_score is not None:
            config.setdefault("scoring", {})["min_score"] = args.min_score

        qualified, rejected = score_and_classify_batch(jobs, config)

        print("\n--- QUALIFIED ---")
        for j in qualified:
            print(f"  [{j['relevance_score']}/10] [{j['job_type']}] {j.get('title', 'N/A')}")
            if j.get("relevance_notes"):
                print(f"         {j['relevance_notes']}")

        print("\n--- REJECTED ---")
        for j in rejected:
            print(f"  [{j['relevance_score']}/10] [{j['job_type']}] {j.get('title', 'N/A')}")

        # Write results to file
        out_path = args.file.replace(".json", "_scored.json")
        with open(out_path, "w") as f:
            json.dump({"qualified": qualified, "rejected": rejected}, f, indent=2)
        print(f"\nResults written to {out_path}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
