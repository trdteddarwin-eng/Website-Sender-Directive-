#!/usr/bin/env python3
"""
Generate an AI reply to a lead's email using Claude Haiku via OpenRouter.

Usage (CLI):
    python3 execution/generate_reply_email.py \
        --input-json '{"lead_name":"John Smith","company":"Acme HVAC","reply_text":"Sounds interesting!","original_subject":"Re: Your website","sentiment":"positive"}'

Or as import:
    from execution.generate_reply_email import generate_reply
    result = generate_reply(lead_name=..., company=..., reply_text=..., ...)
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


def generate_reply(lead_name, company, reply_text, original_subject="",
                   original_snippet="", sentiment="neutral", sender_name="Ted"):
    """
    Generate a reply email using Claude Haiku.

    Args:
        lead_name: Lead's first name or full name
        company: Lead's company name
        reply_text: The lead's reply email body
        original_subject: Subject of our original outreach
        original_snippet: Short snippet of our original email
        sentiment: positive|negative|neutral
        sender_name: Name to sign off as (from account display_name)

    Returns:
        dict with reply_subject, reply_body (plain text)
    """
    if not OPENROUTER_API_KEY:
        # Fallback without API
        return _fallback_reply(lead_name, company, original_subject, sentiment, sender_name)

    # Build prompt based on sentiment
    if sentiment == "positive":
        tone_instruction = """The lead is INTERESTED. Be enthusiastic but professional.
- Thank them for their interest
- Suggest a quick 10-15 min call to walk through the site and discuss next steps
- Offer 2-3 time slots (say "this week" or "early next week")
- Keep it warm and personal, not salesy"""
    elif sentiment == "negative":
        tone_instruction = """The lead is NOT interested. Be gracious and brief.
- Thank them for letting you know
- No hard sell, no pushing
- Leave the door open ("if things change down the road...")
- 2-3 sentences max. Don't grovel."""
    else:
        tone_instruction = """The lead has questions or gave a neutral response. Be helpful.
- Answer any questions they raised directly
- Provide useful info without being pushy
- Soft CTA: suggest a call if they want to discuss further
- Match their energy level"""

    prompt = f"""You are {sender_name}, a web designer who sends spec websites to HVAC/service companies. A lead just replied to your outreach email. Write a reply.

LEAD INFO:
- Name: {lead_name}
- Company: {company}
- Original subject: {original_subject}
- Original email snippet: {original_snippet or "(outreach about a spec website we built for them)"}

THEIR REPLY:
{reply_text}

TONE: {tone_instruction}

RULES:
- Plain text only, no HTML, no markdown formatting
- Sound like a real person, not a bot
- No em dashes, no corporate speak, no filler phrases
- Use their first name
- Sign off with just your first name ({sender_name})
- Keep it concise: 3-6 sentences for positive/neutral, 2-3 for negative
- Don't repeat what they said back to them

OUTPUT FORMAT (valid JSON only):
{{
    "reply_subject": "Re: {original_subject}",
    "reply_body": "the full reply text here"
}}"""

    try:
        resp = http_requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "max_tokens": 500,
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

        result = json.loads(response_text)
        return {
            "reply_subject": result.get("reply_subject", f"Re: {original_subject}"),
            "reply_body": result.get("reply_body", ""),
        }
    except Exception as e:
        print(f"[generate_reply] OpenRouter error: {e}", file=sys.stderr)
        return _fallback_reply(lead_name, company, original_subject, sentiment, sender_name)


def _fallback_reply(lead_name, company, original_subject, sentiment, sender_name):
    """Template fallback if API is unavailable."""
    first = lead_name.split()[0] if lead_name else "there"
    subject = f"Re: {original_subject}" if original_subject else f"Re: {company}"

    if sentiment == "positive":
        body = (
            f"Hey {first},\n\n"
            f"Really glad you liked it! I'd love to walk you through the site "
            f"and talk about what we could do for {company}. "
            f"Do you have 15 minutes this week for a quick call?\n\n"
            f"{sender_name}"
        )
    elif sentiment == "negative":
        body = (
            f"Hey {first},\n\n"
            f"Totally understand, appreciate you letting me know. "
            f"If anything changes down the road, feel free to reach out.\n\n"
            f"{sender_name}"
        )
    else:
        body = (
            f"Hey {first},\n\n"
            f"Great question! Happy to go into more detail. "
            f"Would it be easier to hop on a quick call? "
            f"I can walk you through everything in 10 minutes.\n\n"
            f"{sender_name}"
        )
    return {"reply_subject": subject, "reply_body": body}


def main():
    parser = argparse.ArgumentParser(description="Generate AI reply to a lead email")
    parser.add_argument("--input-json", required=True, help="JSON string or path to JSON file with input data")
    parser.add_argument("--output-json", help="Path to write output JSON (optional, prints to stdout if omitted)")
    args = parser.parse_args()

    # Parse input
    if os.path.exists(args.input_json):
        with open(args.input_json) as f:
            data = json.load(f)
    else:
        data = json.loads(args.input_json)

    result = generate_reply(
        lead_name=data.get("lead_name", ""),
        company=data.get("company", ""),
        reply_text=data.get("reply_text", ""),
        original_subject=data.get("original_subject", ""),
        original_snippet=data.get("original_snippet", ""),
        sentiment=data.get("sentiment", "neutral"),
        sender_name=data.get("sender_name", "Ted"),
    )

    if args.output_json:
        with open(args.output_json, "w") as f:
            json.dump(result, f, indent=2)
        print(f"Output written to {args.output_json}")
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
