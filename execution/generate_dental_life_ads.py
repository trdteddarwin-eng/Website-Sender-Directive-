#!/usr/bin/env python3
"""
generate_dental_life_ads.py — Generate premium ad images for Dental Life Panama.

Uses Gemini 3 Pro Image (Nano Banana Pro) to create luxury dental marketing images.
Brand: navy #1B2A4A + gold #C9A84C. Target: premium dental clinic in Panama City.

Usage:
    python3 execution/generate_dental_life_ads.py
    python3 execution/generate_dental_life_ads.py --only brand_hero miss_panama
    python3 execution/generate_dental_life_ads.py --start-from 5
"""

import os
import sys
import time
import argparse
from dotenv import load_dotenv

load_dotenv()

NANO_BANANA_MODEL = "gemini-3-pro-image-preview"

OUTPUT_DIR = "dental-life-website/public/images/ads"

AD_PROMPTS = [
    # --- High-converting smile/lifestyle shots ---
    {
        "name": "smile_closeup",
        "prompt": (
            "Professional dental advertisement photograph. Extreme close-up of a young Latina woman's perfect bright white smile, "
            "lips slightly parted showing top and bottom teeth. Flawless porcelain veneers. Dewy skin, subtle lip gloss. "
            "Shot with a macro lens, shallow depth of field. Soft studio lighting from the left. "
            "Clean white background. No text, no logos, no watermarks. "
            "Photorealistic, magazine-quality beauty photography. 1080x1080 square format."
        ),
    },
    {
        "name": "before_after_veneers",
        "prompt": (
            "Dental before and after photograph, side by side comparison. Left half: close-up of a real mouth with yellowed, "
            "slightly crooked teeth, natural unflattering lighting. Right half: same angle, same person, now with perfect "
            "bright white aligned veneers, beautiful smile. Clean white dividing line between the two halves. "
            "No text, no logos, no labels. Clinical photography style, authentic and believable. "
            "Photorealistic. 1080x1080 square format."
        ),
    },
    {
        "name": "woman_laughing",
        "prompt": (
            "Candid lifestyle photograph of a beautiful Latina woman in her late 20s laughing genuinely with her head tilted back slightly. "
            "Perfect white teeth visible. She is outdoors in golden hour sunlight, wearing a white blouse. "
            "Blurred warm bokeh background suggesting a tropical city. Her skin glows in the warm light. "
            "Shot on a 85mm lens, shallow depth of field. Natural, authentic joy — not posed. "
            "No text, no logos, no watermarks. Photorealistic lifestyle photography. 1080x1080 square format."
        ),
    },
    {
        "name": "couple_smiling",
        "prompt": (
            "Lifestyle advertisement photo of an attractive Latino couple in their 30s, both smiling broadly showing perfect white teeth. "
            "They are close together, cheek to cheek, looking at camera. The man has a trimmed beard. "
            "Bright natural lighting, clean modern background (white wall with a plant). "
            "Both look healthy, happy, and confident. Warm color tones. "
            "No text, no logos, no watermarks. High-end lifestyle photography like a Colgate or Crest ad. "
            "Photorealistic. 1080x1080 square format."
        ),
    },
    # --- Service-specific high-converters ---
    {
        "name": "clear_aligners",
        "prompt": (
            "Close-up photograph of a young professional Latina woman holding a clear dental aligner (like Invisalign) "
            "in front of her face at mouth level, smiling behind it. You can see through the transparent aligner. "
            "She has perfect teeth and is in a bright, modern setting. Soft natural window light. "
            "Clean, aspirational, lifestyle feel. Shot on portrait lens with blurred background. "
            "No text, no logos, no branding. Photorealistic product-lifestyle photography. 1080x1080 square format."
        ),
    },
    {
        "name": "whitening_result",
        "prompt": (
            "Before and after teeth whitening photograph. Split image: left side shows a close-up smile with naturally "
            "yellowish/stained teeth. Right side shows the same smile now brilliantly white and bright. "
            "Both shots taken from the same angle with consistent lighting. Clean clinical photography. "
            "The difference is dramatic and convincing. Simple white dividing line. "
            "No text, no logos, no labels. Authentic dental result photography. 1080x1080 square format."
        ),
    },
    {
        "name": "implant_xray",
        "prompt": (
            "Clean dental implant educational image. A photorealistic 3D render of a titanium dental implant "
            "shown cross-section inside a jawbone, with the crown on top matching natural teeth on either side. "
            "The implant is metallic silver, the crown is white porcelain, surrounding bone and gum tissue visible. "
            "Dark clean background, dramatic medical lighting. Highly detailed and anatomically accurate. "
            "No text, no logos, no labels. Medical illustration quality. 1080x1080 square format."
        ),
    },
    {
        "name": "modern_clinic",
        "prompt": (
            "Interior photograph of a premium modern dental clinic. A sleek dental chair in the center of a bright, "
            "immaculate treatment room. Large windows letting in natural light. White and light grey color scheme "
            "with subtle warm wood accents. A large overhead dental light, modern cabinetry, a mounted screen on the wall. "
            "Fresh flowers on the counter. The space feels like a luxury medical spa — calming and high-end. "
            "No text, no logos. Architectural interior photography. 1080x1080 square format."
        ),
    },
    # --- Trust/authority shots ---
    {
        "name": "dentist_patient",
        "prompt": (
            "Warm photograph of a female dentist (Latina, mid-30s, wearing a clean white coat and nitrile gloves) "
            "showing a patient a dental mirror with their new smile. The patient is reclined in the chair, "
            "looking at a hand mirror with a big genuine smile, clearly happy with the results. "
            "The dentist is smiling warmly too. Modern clinic background, bright overhead lighting. "
            "Authentic moment of care and trust. No text, no logos. "
            "Photorealistic medical photography. 1080x1080 square format."
        ),
    },
    {
        "name": "dentist_portrait",
        "prompt": (
            "Professional headshot portrait of a confident female dentist (Latina, mid-30s) in a pristine white lab coat. "
            "Arms crossed, warm approachable smile showing her own perfect teeth. "
            "She wears small gold earrings and has her hair pulled back neatly. "
            "Clean, slightly blurred modern dental clinic in the background. "
            "Soft professional studio lighting. Conveys expertise, trust, and warmth. "
            "No text, no name tag, no logos. Executive medical portrait photography. 1080x1080 square format."
        ),
    },
    # --- Emotional/aspirational ---
    {
        "name": "mirror_reveal",
        "prompt": (
            "Emotional dental reveal moment. A young Latina woman sitting in a dental chair, looking into a handheld mirror "
            "and seeing her new smile for the first time. Her eyes are wide with genuine happiness, one hand touching her cheek "
            "in amazement. Tears of joy forming. A dentist's gloved hand holds the mirror for her. "
            "Bright clinical lighting, clean modern dental office. An authentic emotional moment. "
            "No text, no logos. Photorealistic documentary-style photography. 1080x1080 square format."
        ),
    },
    {
        "name": "confidence_walk",
        "prompt": (
            "Lifestyle photograph of a stunning Latina woman walking down a modern city street, looking over her shoulder "
            "at the camera with a radiant confident smile. Perfect white teeth. She wears a fitted blazer and looks successful. "
            "Warm golden hour sunlight, modern glass buildings blurred in the background. "
            "Cinematic shallow depth of field, warm color grading. Movement and energy in the shot. "
            "No text, no logos, no watermarks. High-end fashion/lifestyle photography. 1080x1080 square format."
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
                time.sleep(3)
            else:
                print(f"    [FAIL] No image generated after {retries + 1} attempts")
                return None

        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "rate" in err_str.lower():
                wait = 10 * (attempt + 1)
                print(f"    Rate limited, waiting {wait}s...")
                time.sleep(wait)
            elif attempt < retries:
                print(f"    Error: {e}, retrying ({attempt + 1}/{retries})...")
                time.sleep(3)
            else:
                print(f"    [FAIL] {e}")
                return None

    return None


def main():
    parser = argparse.ArgumentParser(description="Generate Dental Life premium ad images")
    parser.add_argument("--output-dir", default=OUTPUT_DIR,
                        help="Output directory for generated images")
    parser.add_argument("--only", nargs="+", default=None,
                        help="Only generate specific images by name (e.g. --only brand_hero miss_panama)")
    parser.add_argument("--start-from", type=int, default=0,
                        help="Start from this index (0-based)")
    args = parser.parse_args()

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not found in .env")
        sys.exit(1)

    from google import genai
    client = genai.Client(api_key=api_key)

    os.makedirs(args.output_dir, exist_ok=True)

    # Filter prompts
    if args.only:
        prompts = [p for p in AD_PROMPTS if p["name"] in args.only]
        if not prompts:
            print(f"Error: No matching prompts for: {args.only}")
            print(f"Available: {[p['name'] for p in AD_PROMPTS]}")
            sys.exit(1)
    else:
        prompts = AD_PROMPTS[args.start_from:]

    print(f"Generating {len(prompts)} Dental Life ad images...")
    print(f"Output: {args.output_dir}/")
    print()

    success = 0
    failed = 0

    for i, ad in enumerate(prompts):
        output_path = os.path.join(args.output_dir, f"{ad['name']}.png")
        print(f"[{i+1}/{len(prompts)}] {ad['name']}...")

        result = generate_image(client, ad["prompt"], output_path)
        if result:
            size_kb = os.path.getsize(result) / 1024
            print(f"    Saved: {result} ({size_kb:.0f} KB)")
            success += 1
        else:
            print(f"    FAILED")
            failed += 1

        # Rate limit buffer between generations
        if i < len(prompts) - 1:
            time.sleep(2)

    print()
    print(f"Done! {success} generated, {failed} failed.")
    print(f"Images saved to: {args.output_dir}/")


if __name__ == "__main__":
    main()
