#!/usr/bin/env python3
"""
generate_email_storyboard.py — Generate storyboard images for cold email setup guide.

Creates a visual step-by-step storyboard using Nano Banana Pro (Gemini 3 Pro Image)
that walks someone through the entire cold email domain + outreach setup process.

Usage:
    python3 execution/generate_email_storyboard.py --output-dir .tmp/email-storyboard
"""

import os
import sys
import time
import argparse
from dotenv import load_dotenv

load_dotenv()

NANO_BANANA_MODEL = "gemini-3-pro-image-preview"

# Consistent style directive applied to every prompt
STYLE = (
    "Modern flat illustration style with clean lines, soft shadows, and a cohesive color palette "
    "of navy blue (#1a2332), teal (#00BFA5), white, and light gray. Minimal, professional, "
    "tech-forward aesthetic. No photorealistic faces. Use simple character silhouettes or icons for people. "
    "Each image should have a large step number in the top-left corner in a teal circle. "
    "16:9 aspect ratio, suitable for a presentation slide or social media carousel."
)

STORYBOARD = [
    {
        "name": "01_the_problem",
        "prompt": (
            f"Step 1 storyboard illustration. {STYLE} "
            "Show a person at a desk looking frustrated at a laptop screen. The screen shows emails "
            "falling into a red 'SPAM' folder. Red warning icons and X marks surround the laptop. "
            "A thought bubble reads 'Why are my emails going to spam?'. "
            "Title at bottom: 'THE PROBLEM: Your Main Domain Is Burned'. "
            "Mood: frustration, confusion."
        ),
    },
    {
        "name": "02_why_separate_domains",
        "prompt": (
            f"Step 2 storyboard illustration. {STYLE} "
            "Split screen concept. Left side shows a single building (representing one domain) on fire, "
            "with flames labeled 'SPAM' — everything is burning. Right side shows 3 separate smaller buildings "
            "(representing 3 domains), only one has a small flame, the other 2 are safe with green checkmarks. "
            "Title at bottom: 'WHY: Separate Domains Protect Your Business'. "
            "Visual metaphor: don't put all eggs in one basket."
        ),
    },
    {
        "name": "03_buy_domain",
        "prompt": (
            f"Step 3 storyboard illustration. {STYLE} "
            "Show a clean browser window with a Namecheap-style domain registrar interface. "
            "A shopping cart icon shows a domain name 'yourbrand.online' with a price tag of '$2.88'. "
            "A hand cursor is clicking an 'Add to Cart' button. Green checkmarks next to 'Domain Privacy: FREE'. "
            "A big red X next to 'Web Hosting' (crossed out — not needed). "
            "Title at bottom: 'STEP 1: Buy a Cheap Domain (~$3)'. "
        ),
    },
    {
        "name": "04_setup_email",
        "prompt": (
            f"Step 4 storyboard illustration. {STYLE} "
            "Show 3 email envelope icons lined up, each with a different name: 'ted@', 'john@', 'patrick@', "
            "all connected to a single domain icon labeled 'yourbrand.online'. "
            "Each envelope has a key icon representing passwords. "
            "A settings gear connects the envelopes to a mail server icon. "
            "Title at bottom: 'STEP 2: Create 3 Mailboxes on Your Domain'. "
            "Clean, organized, shows the concept of multiple emails on one domain."
        ),
    },
    {
        "name": "05_dns_wiring",
        "prompt": (
            f"Step 5 storyboard illustration. {STYLE} "
            "Show a domain icon on the left connected by glowing teal lines/wires to a mail server on the right. "
            "The wires are labeled 'MX Records', 'SPF', 'DKIM'. "
            "Small lock icons on each wire showing security. A green 'CONNECTED' status badge. "
            "Think of it like plugging in cables — simple visual of domain connecting to email service. "
            "Title at bottom: 'STEP 3: Connect DNS Records (5 Minutes)'. "
        ),
    },
    {
        "name": "06_warmup_phase",
        "prompt": (
            f"Step 6 storyboard illustration. {STYLE} "
            "Show a thermometer or gauge gradually filling up from blue (cold) to green (warm) over a 3-week timeline. "
            "Week 1: thermometer at 33%, small number of email icons (5/day). "
            "Week 2: thermometer at 66%, medium emails (10/day). "
            "Week 3: thermometer at 100% with a green glow, full emails (30/day). "
            "A shield icon with 'REPUTATION' label grows larger as the thermometer fills. "
            "Title at bottom: 'STEP 4: Warm Up for 3 Weeks (Automated)'. "
        ),
    },
    {
        "name": "07_warmup_how",
        "prompt": (
            f"Step 7 storyboard illustration. {STYLE} "
            "Show a circular loop diagram: Email Account sends email → Warm-up Network receives it → "
            "They open it (eye icon) → They reply (reply arrow) → They mark 'Not Spam' (green checkmark) → "
            "Domain reputation goes up (upward arrow) → Loop repeats. "
            "An 'Instantly' logo placeholder (just a lightning bolt icon) in the center of the loop. "
            "Title at bottom: 'HOW WARM-UP WORKS: Real Accounts Engage With Your Emails'. "
        ),
    },
    {
        "name": "08_sending_limits",
        "prompt": (
            f"Step 8 storyboard illustration. {STYLE} "
            "Show 3 email account icons arranged in a row, each with a meter/gauge showing '30-40/day'. "
            "Below them, arrows converge into a combined total showing '~100 emails/day'. "
            "A red danger zone above 50 per account is marked. A green safe zone at 30-40 is highlighted. "
            "Small calendar icon showing 'Daily'. "
            "Title at bottom: 'SAFE LIMITS: 30-40 Per Account, ~100/Day Total'. "
        ),
    },
    {
        "name": "09_scale_with_domains",
        "prompt": (
            f"Step 9 storyboard illustration. {STYLE} "
            "Show a scaling diagram: 1 domain with 3 accounts = 100/day, "
            "2 domains with 6 accounts = 200/day, 3 domains with 9 accounts = 300/day. "
            "Each domain is a different colored building, accounts are people icons inside. "
            "Arrows show the math adding up. Green upward trend line across the top. "
            "Title at bottom: 'TO SCALE: Buy More Domains, Not More Accounts'. "
        ),
    },
    {
        "name": "10_the_system",
        "prompt": (
            f"Step 10 storyboard illustration. {STYLE} "
            "Show the final automated system as a clean flowchart: "
            "Prospect List (spreadsheet icon) → Sending Script (code icon with Python logo) → "
            "3 Email Accounts (envelope icons) → Prospects receive emails (inbox icons) → "
            "Replies come back (reply arrows) → Stats Dashboard (chart icon). "
            "A robot/AI icon labeled 'Claude Code' sits at the center orchestrating everything. "
            "Title at bottom: 'THE SYSTEM: Code Does The Work, You Close The Deals'. "
            "Mood: empowerment, automation, efficiency."
        ),
    },
]


def generate_image(client, prompt, output_path, retries=2):
    """Generate a single image from a text prompt using Nano Banana Pro."""
    from google.genai import types

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=prompt),
            ],
        )
    ]

    config = types.GenerateContentConfig(
        response_modalities=["IMAGE", "TEXT"],
        temperature=1.0,
    )

    for attempt in range(retries + 1):
        try:
            response = client.models.generate_content(
                model=NANO_BANANA_MODEL,
                contents=contents,
                config=config,
            )

            if response.candidates:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, "inline_data") and part.inline_data:
                        with open(output_path, "wb") as f:
                            f.write(part.inline_data.data)
                        return output_path

            if attempt < retries:
                print(f"    No image returned, retrying ({attempt + 1}/{retries})...")
                time.sleep(2)
            else:
                print(f"    [FAIL] No image generated after {retries + 1} attempts")
                return None

        except Exception as e:
            if attempt < retries:
                print(f"    Error: {e}, retrying ({attempt + 1}/{retries})...")
                time.sleep(3)
            else:
                print(f"    [FAIL] {e}")
                return None

    return None


def main():
    parser = argparse.ArgumentParser(description="Generate email setup storyboard images")
    parser.add_argument("--output-dir", default=".tmp/email-storyboard",
                        help="Output directory for generated images")
    args = parser.parse_args()

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not found in .env")
        sys.exit(1)

    from google import genai
    client = genai.Client(api_key=api_key)

    os.makedirs(args.output_dir, exist_ok=True)

    print(f"Generating {len(STORYBOARD)} storyboard images using Nano Banana Pro...")
    print(f"Output: {args.output_dir}/")
    print()

    success = 0
    failed = 0

    for i, slide in enumerate(STORYBOARD):
        output_path = os.path.join(args.output_dir, f"{slide['name']}.png")
        print(f"[{i+1}/{len(STORYBOARD)}] {slide['name']}...")

        result = generate_image(client, slide["prompt"], output_path)
        if result:
            print(f"    Saved: {result}")
            success += 1
        else:
            print(f"    FAILED")
            failed += 1

        # Rate limit buffer
        if i < len(STORYBOARD) - 1:
            time.sleep(2)

    print()
    print(f"Done! {success} generated, {failed} failed.")
    print(f"Images saved to: {args.output_dir}/")


if __name__ == "__main__":
    main()
