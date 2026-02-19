#!/usr/bin/env python3
"""
generate_dental_images.py — Generate images for Dental Life website using Nano Banana Pro.

Creates professional dental/clinical imagery for each section of the website.
Images saved to dental-life-website/public/images/

Usage:
    python3 execution/generate_dental_images.py
    python3 execution/generate_dental_images.py --only hero
"""

import os
import sys
import time
import argparse
import subprocess
from dotenv import load_dotenv

load_dotenv()

NANO_BANANA_MODEL = "gemini-3-pro-image-preview"
OUTPUT_DIR = "dental-life-website/public/images"

STYLE_PREFIX = (
    "Professional high-end dental clinic photography. "
    "Clean, modern, luxurious aesthetic with warm lighting. "
    "Color palette emphasizes deep navy blue (#1B2A4A) and soft gold (#C9A84C) accents. "
    "No text, no logos, no watermarks. "
    "Photorealistic, aspirational, premium medical aesthetic. "
)

DENTAL_IMAGES = [
    # ─── HERO ───
    {
        "id": "hero",
        "prompt": (
            "A stunning close-up portrait of a beautiful Latina woman with a perfect, radiant white smile. "
            "She has flawless skin, warm brown eyes, and dark hair. She's looking confidently at the camera. "
            "Soft golden side lighting on a clean blurred background. "
            "The image conveys luxury, confidence, and dental perfection. "
            "Shot on a high-end camera with shallow depth of field. Aspirational dental advertisement style."
        ),
    },
    # ─── SERVICES ───
    {
        "id": "ortodoncia",
        "prompt": (
            "A close-up of a young woman smiling broadly showing clear ceramic orthodontic brackets on her teeth. "
            "She looks happy and confident. Modern dental clinic setting in the background, slightly blurred. "
            "Warm, inviting lighting. The brackets are clean, modern clear/transparent type. "
            "Professional orthodontic marketing photography."
        ),
    },
    {
        "id": "estetica",
        "prompt": (
            "A professional dental cosmetic treatment scene. A patient is reclined in a modern dental chair "
            "receiving teeth whitening treatment with LED light. The clinic is ultra-modern with clean white surfaces "
            "and navy blue accent details. Dramatic lighting on the treatment area. "
            "Premium cosmetic dentistry atmosphere."
        ),
    },
    {
        "id": "implantes",
        "prompt": (
            "A photorealistic close-up of a modern titanium dental implant model sitting on a clean white surface "
            "next to a porcelain dental crown. The implant is metallic silver with precise threading. "
            "Soft studio lighting with navy and gold background tones. "
            "Medical-grade product photography. Sharp focus, professional depth of field."
        ),
    },
    {
        "id": "ortoestetica",
        "prompt": (
            "A before-and-after style split image showing a dental transformation. "
            "Left side: slightly misaligned teeth. Right side: perfectly aligned, white, beautiful smile. "
            "Both shots are professional dental photography with even lighting. "
            "The transition between the two sides is clean. "
            "Conveys the combined power of orthodontics and aesthetic dentistry."
        ),
    },
    {
        "id": "restauracion",
        "prompt": (
            "A dentist's gloved hands carefully placing a porcelain dental crown onto a prepared tooth. "
            "Close-up macro photography showing precision dental work. "
            "Modern dental tools visible. Clean, sterile clinical environment with warm lighting. "
            "Professional dental restoration procedure photography."
        ),
    },
    {
        "id": "diseno-sonrisa",
        "prompt": (
            "A dental professional showing a digital smile design on a tablet screen to a smiling patient. "
            "The tablet displays a before/after digital mockup of the patient's smile transformation. "
            "Modern, high-tech dental office environment. Both people look engaged and happy. "
            "Conveys cutting-edge technology meets personal care. Warm, professional lighting."
        ),
    },
    # ─── ABOUT / CLINIC ───
    {
        "id": "clinic-interior",
        "prompt": (
            "Interior of a luxury modern dental clinic. Clean white walls with navy blue accent panels. "
            "State-of-the-art dental chair and equipment. Large windows with natural light. "
            "Fresh flowers in a gold vase on the counter. Spotless, organized, welcoming atmosphere. "
            "Premium medical interior design photography."
        ),
    },
    # ─── REVIEWS / TESTIMONIALS ───
    {
        "id": "patient-smile-1",
        "prompt": (
            "A warm, genuine portrait of a happy Latina woman in her 30s with a beautiful natural smile. "
            "She has dark wavy hair and warm brown eyes. Shot outdoors with soft natural golden hour lighting. "
            "Blurred green foliage in the background. She radiates confidence and happiness. "
            "Candid, authentic feel — not overly posed. Portrait photography style."
        ),
    },
    {
        "id": "patient-smile-2",
        "prompt": (
            "A close-up portrait of a smiling young Latino man with a perfect white smile. "
            "He has short dark hair and a well-groomed beard. Wearing a casual button-down shirt. "
            "Natural daylight, blurred urban background. Confident, genuine expression. "
            "Modern lifestyle portrait photography."
        ),
    },
    # ─── BEFORE/AFTER CASES ───
    {
        "id": "case-blanqueamiento",
        "prompt": (
            "Professional dental before-and-after photography of teeth whitening. "
            "Split image: left shows yellowish stained teeth, right shows the same teeth brilliantly white. "
            "Clinical dental photography with consistent lighting and positioning. "
            "Clean, medical aesthetic. Close-up of just the teeth and lips."
        ),
    },
    {
        "id": "case-carillas",
        "prompt": (
            "Professional dental before-and-after photography of porcelain veneer placement. "
            "Split image: left shows slightly uneven, discolored front teeth, "
            "right shows perfectly uniform, bright white veneers. "
            "Close-up dental photography with retractors showing teeth clearly. Clinical lighting."
        ),
    },
    {
        "id": "case-implante",
        "prompt": (
            "Professional dental before-and-after photography of a dental implant case. "
            "Split image: left shows a gap from a missing tooth in the smile, "
            "right shows a perfect implant crown filling the gap seamlessly matching surrounding teeth. "
            "Close-up dental photography. Clean clinical lighting."
        ),
    },
    {
        "id": "case-diseno-sonrisa",
        "prompt": (
            "Professional dental before-and-after photography of a complete smile design transformation. "
            "Split image: left shows crooked, stained, uneven teeth, "
            "right shows a stunning Hollywood-perfect smile with perfect alignment and whiteness. "
            "Dramatic dental transformation. Close-up lips and teeth. Clinical photography."
        ),
    },
    # ─── OG IMAGE ───
    {
        "id": "og-dental-life",
        "prompt": (
            "A sophisticated dental clinic branding image. A beautiful, confident woman with a perfect smile "
            "in the foreground. Behind her, a modern luxury dental clinic with navy blue and gold accents. "
            "The image conveys trust, luxury, and dental excellence. "
            "Wide format (16:9 aspect ratio), suitable for a website social media preview card. "
            "Premium, aspirational dental marketing photography."
        ),
    },
]


def generate_image(client, prompt, output_path, retries=2):
    """Generate a single image from a text prompt using Nano Banana Pro."""
    from google.genai import types

    full_prompt = STYLE_PREFIX + prompt

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=full_prompt)],
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
                print(f"    No image returned, retrying ({attempt + 1}/{retries})...", flush=True)
                time.sleep(3)
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
    parser = argparse.ArgumentParser(description="Generate Dental Life website images")
    parser.add_argument("--only", type=str, default=None,
                        help="Generate only this image ID")
    parser.add_argument("--start-from", type=int, default=0,
                        help="Start from image index (0-based)")
    args = parser.parse_args()

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not found in .env")
        sys.exit(1)

    from google import genai
    client = genai.Client(api_key=api_key)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if args.only:
        items = [m for m in DENTAL_IMAGES if m["id"] == args.only]
        if not items:
            print(f"Error: Image '{args.only}' not found")
            sys.exit(1)
    else:
        items = DENTAL_IMAGES[args.start_from:]

    print(f"Generating {len(items)} dental images using Nano Banana Pro...", flush=True)
    print(f"Output: {OUTPUT_DIR}/", flush=True)
    print(flush=True)

    success = 0
    failed = 0
    skipped = 0

    for i, item in enumerate(items):
        global_idx = args.start_from + i if not args.only else 0
        output_path = os.path.join(OUTPUT_DIR, f"{item['id']}.png")

        # Skip if already exists
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            print(f"[{global_idx + 1}] {item['id']} — already exists, skipping")
            skipped += 1
            continue

        print(f"[{global_idx + 1}/{len(DENTAL_IMAGES)}] {item['id']}...", flush=True)

        result = generate_image(client, item["prompt"], output_path)
        if result:
            size_kb = os.path.getsize(result) / 1024
            print(f"    Saved ({size_kb:.0f} KB)", flush=True)
            success += 1
        else:
            print(f"    FAILED")
            failed += 1

        # Rate limit buffer
        if i < len(items) - 1:
            time.sleep(2.5)

    print()
    print(f"Done! {success} generated, {failed} failed, {skipped} skipped.")
    print(f"Images saved to: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
