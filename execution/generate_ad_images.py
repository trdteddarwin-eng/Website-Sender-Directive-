#!/usr/bin/env python3
"""
generate_ad_images.py — Generate ad images using Nano Banana Pro (Gemini 3 Pro Image).

Creates marketing ad images for Green Grow Digital using text-to-image generation.
Brand color: GREEN. Target: local businesses needing Meta ads + AI marketing.

Usage:
    python3 execution/generate_ad_images.py --output-dir greengrow-strategy/ads
"""

import os
import sys
import time
import argparse
from dotenv import load_dotenv

load_dotenv()

NANO_BANANA_MODEL = "gemini-3-pro-image-preview"


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


# 20 ad prompts for Green Grow Digital
AD_PROMPTS = [
    # --- Brand Awareness ---
    {
        "name": "01_brand_hero",
        "prompt": (
            "A bold, modern digital marketing ad graphic. Dominant color: vibrant green (#00C853). "
            "Clean white background with green geometric shapes and flowing digital lines. "
            "Large bold text reads 'GROW SMARTER' in dark green. Below in smaller text: 'AI-Powered Facebook Ads for Local Business'. "
            "A small green leaf icon integrated into the design. Professional, sleek, tech-forward aesthetic. "
            "16:9 aspect ratio, suitable for a Facebook ad."
        ),
    },
    {
        "name": "02_brand_trust",
        "prompt": (
            "A professional marketing ad with green color scheme. Shows a confident business owner smiling in their shop, "
            "with a translucent green overlay showing upward-trending graphs and metrics (ROAS 3.5x, CPL -40%). "
            "Text overlay: 'Stop Guessing. Start Growing.' in bold white text on a green banner. "
            "Clean, trustworthy, results-focused aesthetic. Facebook ad format."
        ),
    },
    {
        "name": "03_ai_powered",
        "prompt": (
            "Futuristic ad graphic showing AI brain made of green circuit paths and glowing neural connections. "
            "The brain is surrounded by floating marketing icons: ad thumbnails, chat bubbles, analytics charts. "
            "Text: 'AI That Actually Gets You Leads' in bold modern font. Green (#00C853) is the dominant accent color. "
            "Dark background, neon green highlights. Tech-forward but approachable. Facebook ad."
        ),
    },
    # --- Results / ROI Focused ---
    {
        "name": "04_roi_stats",
        "prompt": (
            "Clean infographic-style ad with green color scheme on white background. "
            "Three large statistics displayed prominently: '3.5x ROAS' '40% Lower CPL' '55% More Leads'. "
            "Each stat has a small green icon (dollar sign, down arrow, upward chart). "
            "Bottom text: 'Real Results for Real Businesses - Green Grow Digital'. "
            "Professional, data-driven, minimal design. Facebook ad format."
        ),
    },
    {
        "name": "05_before_after",
        "prompt": (
            "Split-screen ad design. Left side (red tint): frustrated business owner looking at laptop with declining graph, "
            "text 'BEFORE' with stats 'CPL: $180, ROAS: 0.8x'. Right side (green tint): same business owner smiling, "
            "phone showing success metrics, text 'AFTER' with stats 'CPL: $85, ROAS: 3.2x'. "
            "Bottom banner in green: 'The Green Grow Difference'. Clean, compelling comparison. Facebook ad."
        ),
    },
    {
        "name": "06_money_growth",
        "prompt": (
            "Striking ad image: a green plant growing out of a smartphone screen, with the plant's leaves shaped like dollar signs. "
            "The phone shows a Facebook ads dashboard with green upward trends. "
            "Background is clean white with subtle green gradient. "
            "Text: 'Watch Your Ad Spend Bloom' in elegant green typography. "
            "Fresh, organic meets tech aesthetic. Facebook ad format."
        ),
    },
    # --- Industry-Specific (Med Spa) ---
    {
        "name": "07_medspa_niche",
        "prompt": (
            "Elegant marketing ad targeting med spa owners. Shows a luxurious med spa interior with soft lighting. "
            "Overlaid green accent elements showing '47 New Patients This Month' in stylish font. "
            "Text: 'Fill Your Med Spa with AI-Powered Ads'. Subtle green brand color accent throughout. "
            "Premium, sophisticated aesthetic with modern medical spa vibe. Facebook ad."
        ),
    },
    {
        "name": "08_medspa_results",
        "prompt": (
            "Clean ad graphic with split design: left shows beautiful med spa treatment room, "
            "right shows a green analytics dashboard with metrics (Bookings +62%, CPL $95, ROAS 4.1x). "
            "Connecting green line between the two sides. Text: 'From Empty Chairs to Full Books'. "
            "Elegant, professional, green accents. Facebook ad targeting med spa owners."
        ),
    },
    # --- Industry-Specific (Dental) ---
    {
        "name": "09_dental_niche",
        "prompt": (
            "Professional ad targeting dental practices. Modern dental office setting in background (blurred). "
            "Foreground shows a phone screen with Facebook lead form and green checkmarks. "
            "Bold text: '23 New Patient Leads in Week 1' in dark green. "
            "Subtitle: 'Cosmetic Dentistry Ads That Actually Work'. "
            "Clean, medical-professional aesthetic with green brand accents. Facebook ad."
        ),
    },
    # --- Industry-Specific (HVAC / Home Services) ---
    {
        "name": "10_hvac_niche",
        "prompt": (
            "Bold, practical ad targeting HVAC business owners. Shows an HVAC technician working, "
            "with a green-tinted phone notification overlay: '12 New Emergency Calls Today'. "
            "Stats bar at bottom in green: 'CPL: $120 | Avg Job: $2,800 | ROAS: 3.8x'. "
            "Text: 'Your Phone Should Ring More'. Direct, no-nonsense, results-driven. Facebook ad."
        ),
    },
    {
        "name": "11_contractor_niche",
        "prompt": (
            "Marketing ad for roofing/contractor businesses. Beautiful completed roofing project in background. "
            "Green overlay panel showing: 'Before: 3 leads/week | After: 14 leads/week'. "
            "Bold text: 'Contractors Who Use AI Ads Win More Jobs'. "
            "Green brand accent color, rugged yet professional aesthetic. Facebook ad format."
        ),
    },
    # --- Industry-Specific (Legal) ---
    {
        "name": "12_legal_niche",
        "prompt": (
            "Professional, authoritative ad targeting law firms. Dark sophisticated background with green accent lines. "
            "Scales of justice icon in green. Stats: 'Avg Case Value: $45,000 | CPL: $380 | 8 Cases/Month'. "
            "Text: 'Fill Your Caseload with Qualified Leads'. "
            "Elegant, serious, trustworthy design with green highlights. Facebook ad."
        ),
    },
    # --- Service / Feature Highlights ---
    {
        "name": "13_reels_ads",
        "prompt": (
            "Dynamic ad showcasing Reels advertising power. Shows a smartphone playing a vertical video ad, "
            "surrounded by floating green engagement metrics: hearts, comments, share icons, and a '1.5x ROAS' badge. "
            "Text: 'Reels Ads: 3x Higher ROAS Than Feed'. Green color scheme throughout. "
            "Energetic, social-media-native aesthetic. Facebook ad."
        ),
    },
    {
        "name": "14_chatbot_feature",
        "prompt": (
            "Modern ad highlighting AI chatbot lead capture. Shows a phone screen with a Messenger conversation: "
            "customer asks about services, chatbot responds instantly with booking link, green checkmark shows 'Lead Captured'. "
            "Text: 'Never Miss a Lead Again - 24/7 AI Chat'. Green message bubbles and accents. "
            "Clean, technological, practical. Facebook ad."
        ),
    },
    {
        "name": "15_dashboard_feature",
        "prompt": (
            "Sleek ad showing a marketing analytics dashboard on a large monitor. "
            "All graphs and charts use green color palette. Key metrics highlighted: ROAS, CPL, Lead Volume. "
            "Text: 'See Every Dollar at Work - Real-Time AI Reporting'. "
            "Green data visualization aesthetic, transparent, trustworthy. Facebook ad format."
        ),
    },
    # --- Lead Magnet / CTA Ads ---
    {
        "name": "16_free_audit",
        "prompt": (
            "Eye-catching lead magnet ad. Bold green banner with white text: 'FREE META AD AUDIT'. "
            "Below shows a magnifying glass over a Facebook ads dashboard revealing hidden insights (highlighted in green). "
            "Subtitle: 'Discover 3 Quick Wins in Your Ad Account'. "
            "Call-to-action button in green: 'Get Your Free Audit'. Clean, compelling, high-conversion design. Facebook ad."
        ),
    },
    {
        "name": "17_case_study",
        "prompt": (
            "Case study ad with green color scheme. Photo of a happy business owner in their shop. "
            "Green stats overlay: 'Revenue +142% in 90 Days'. "
            "Quote bubble: 'Green Grow changed everything for my business'. "
            "Bottom CTA in green: 'See How We Did It'. Authentic, testimonial-driven, trustworthy. Facebook ad."
        ),
    },
    {
        "name": "18_limited_spots",
        "prompt": (
            "Urgency-driven ad with green and white color scheme. Bold text: 'Only 3 Spots Left This Month'. "
            "Below shows a green progress bar almost full (showing limited availability). "
            "Subtitle: 'AI-Powered Ad Management for Local Businesses'. "
            "Green accent color, clean design, scarcity-focused but honest. Facebook ad format."
        ),
    },
    # --- Creative / Emotional ---
    {
        "name": "19_growth_metaphor",
        "prompt": (
            "Artistic ad: a small green seedling growing through cracked concrete, transforming into a towering digital tree "
            "made of glowing green data streams, social media icons, and currency symbols. "
            "Text at bottom: 'From Local Business to Local Legend'. Green Grow Digital branding. "
            "Inspirational, growth-focused, visually stunning. Facebook ad."
        ),
    },
    {
        "name": "20_partnership",
        "prompt": (
            "Professional ad showing two hands in a handshake, one wearing a business sleeve and one with a green digital glow "
            "representing AI technology. Green light emanates from the handshake point. "
            "Background shows a subtle city skyline. Text: 'Your Growth Partner. Powered by AI.' "
            "Trust-building, partnership-focused, premium green branding. Facebook ad."
        ),
    },
]


def main():
    parser = argparse.ArgumentParser(description="Generate ad images using Nano Banana Pro")
    parser.add_argument("--output-dir", default="greengrow-strategy/ads",
                        help="Output directory for generated images")
    args = parser.parse_args()

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not found in .env")
        sys.exit(1)

    from google import genai
    client = genai.Client(api_key=api_key)

    os.makedirs(args.output_dir, exist_ok=True)

    print(f"Generating {len(AD_PROMPTS)} ad images using Nano Banana Pro...")
    print(f"Output: {args.output_dir}/")
    print()

    success = 0
    failed = 0

    for i, ad in enumerate(AD_PROMPTS):
        output_path = os.path.join(args.output_dir, f"{ad['name']}.png")
        print(f"[{i+1}/{len(AD_PROMPTS)}] {ad['name']}...")

        result = generate_image(client, ad["prompt"], output_path)
        if result:
            print(f"    Saved: {result}")
            success += 1
        else:
            print(f"    FAILED")
            failed += 1

        # Rate limit buffer
        if i < len(AD_PROMPTS) - 1:
            time.sleep(2)

    print()
    print(f"Done! {success} generated, {failed} failed.")
    print(f"Images saved to: {args.output_dir}/")


if __name__ == "__main__":
    main()
