#!/usr/bin/env python3
"""
generate_chiro_service_images.py — Generate service images for AlignWell chiropractic website.

Uses Gemini 3 Pro Image (Nano Banana Pro) to create professional medical/wellness
photography-style images for each service detail page. Purple/indigo clinic accents.

Usage:
    python3 execution/generate_chiro_service_images.py
    python3 execution/generate_chiro_service_images.py --slug spinal-adjustments
"""

import os
import sys
import time
import argparse
from dotenv import load_dotenv

load_dotenv()

NANO_BANANA_MODEL = "gemini-3-pro-image-preview"

SERVICE_PROMPTS = [
    {
        "slug": "spinal-adjustments",
        "prompt": (
            "Professional medical photography of a chiropractor performing a spinal adjustment on a patient. "
            "The patient is lying face down on a modern chiropractic adjustment table. The chiropractor's hands "
            "are positioned precisely on the patient's upper back. Clean, modern clinic setting with soft natural "
            "lighting. Subtle purple and indigo accent colors on the clinic walls and equipment. "
            "No text or watermarks. Warm, reassuring atmosphere. High-resolution, photorealistic."
        ),
    },
    {
        "slug": "sports-injury-rehab",
        "prompt": (
            "Professional wellness photography of an athlete receiving sports rehabilitation treatment in a "
            "modern chiropractic clinic. The practitioner is working on the athlete's shoulder/knee area. "
            "Rehabilitation equipment visible in the background — resistance bands, foam rollers, exercise balls. "
            "Dynamic, energetic mood. Clean clinical environment with purple and indigo accent lighting and decor. "
            "No text or watermarks. High-resolution, photorealistic."
        ),
    },
    {
        "slug": "posture-correction",
        "prompt": (
            "Professional medical photography showing a posture assessment session. A chiropractor is evaluating "
            "a patient's posture from the side, possibly using a posture grid or digital analysis screen. "
            "The patient is standing upright in activewear. Modern, bright clinic with clean white walls and "
            "purple/indigo accent elements. Educational and professional atmosphere. "
            "No text or watermarks. High-resolution, photorealistic."
        ),
    },
    {
        "slug": "sciatica-treatment",
        "prompt": (
            "Professional medical photography of a chiropractor treating a patient for lower back and leg pain. "
            "The practitioner is performing a gentle lumbar adjustment or decompression technique. The patient "
            "is lying on their side on a modern treatment table. Warm, soothing clinic lighting with "
            "purple and indigo accent colors on walls and furnishings. Compassionate, healing atmosphere. "
            "No text or watermarks. High-resolution, photorealistic."
        ),
    },
    {
        "slug": "neck-pain-relief",
        "prompt": (
            "Professional medical photography of a chiropractor performing a gentle cervical (neck) adjustment. "
            "The practitioner's hands are carefully positioned on the patient's neck area. The patient appears "
            "relaxed and comfortable. Modern clinic setting with soft ambient lighting and purple/indigo accent "
            "colors. Therapeutic and calming atmosphere. "
            "No text or watermarks. High-resolution, photorealistic."
        ),
    },
    {
        "slug": "headache-migraine-relief",
        "prompt": (
            "Professional wellness photography of a chiropractor treating a patient's upper cervical area and "
            "base of the skull for headache relief. Gentle hands positioned at the occipital region. "
            "The patient's expression shows relief and relaxation. Serene clinic environment with soft "
            "purple and indigo ambient lighting. Calming, therapeutic mood. "
            "No text or watermarks. High-resolution, photorealistic."
        ),
    },
    {
        "slug": "prenatal-chiropractic",
        "prompt": (
            "Professional medical photography of a pregnant woman receiving gentle chiropractic care. "
            "She is positioned comfortably on a specialized pregnancy adjustment table (side-lying position). "
            "The chiropractor is performing a gentle pelvic adjustment. Warm, nurturing clinic atmosphere "
            "with soft lighting and purple/indigo accent colors. Safe, gentle, reassuring mood. "
            "No text or watermarks. High-resolution, photorealistic."
        ),
    },
    {
        "slug": "wellness-programs",
        "prompt": (
            "Professional wellness photography showing a holistic health consultation. A chiropractor and "
            "patient are sitting together reviewing a wellness plan, with healthy foods, exercise equipment, "
            "and a laptop visible on the table. Bright, uplifting clinic environment with natural light "
            "and purple/indigo accent decor. Positive, proactive health and wellness atmosphere. "
            "No text or watermarks. High-resolution, photorealistic."
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
    parser = argparse.ArgumentParser(description="Generate chiropractic service images")
    parser.add_argument("--slug", help="Generate image for a single service by slug")
    parser.add_argument(
        "--output-dir",
        default="chiropractor-website/public/services",
        help="Output directory for generated images",
    )
    args = parser.parse_args()

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not found in .env")
        sys.exit(1)

    from google import genai

    client = genai.Client(api_key=api_key)

    os.makedirs(args.output_dir, exist_ok=True)

    prompts = SERVICE_PROMPTS
    if args.slug:
        prompts = [p for p in SERVICE_PROMPTS if p["slug"] == args.slug]
        if not prompts:
            print(f"Error: Unknown slug '{args.slug}'")
            print(f"Available: {', '.join(p['slug'] for p in SERVICE_PROMPTS)}")
            sys.exit(1)

    print(f"Generating {len(prompts)} service image(s) using Nano Banana Pro...")
    print(f"Output: {args.output_dir}/")
    print()

    success = 0
    failed = 0

    for i, service in enumerate(prompts):
        output_path = os.path.join(args.output_dir, f"{service['slug']}.png")
        print(f"[{i + 1}/{len(prompts)}] {service['slug']}...")

        result = generate_image(client, service["prompt"], output_path)
        if result:
            print(f"    Saved: {result}")
            success += 1
        else:
            print(f"    FAILED")
            failed += 1

        # Rate limit buffer
        if i < len(prompts) - 1:
            time.sleep(2)

    print()
    print(f"Done! {success} generated, {failed} failed.")
    print(f"Images saved to: {args.output_dir}/")


if __name__ == "__main__":
    main()
