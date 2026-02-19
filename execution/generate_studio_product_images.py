#!/usr/bin/env python3
"""
generate_studio_product_images.py — Generate studio-quality product photos using Gemini image editing.

Takes each raw product JPEG and generates a professional studio product photograph:
- Warm cream/beige background with subtle vignette
- Product centered, ~70% of frame height
- Professional studio lighting, subtle contact shadow
- Editorial, premium feel

Usage:
    python3 execution/generate_studio_product_images.py                    # All products
    python3 execution/generate_studio_product_images.py --only cremas-cocoye  # Single product
    python3 execution/generate_studio_product_images.py --dry-run          # Show what would run
"""

import os
import sys
import time
import argparse
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_DIR = os.path.join(BASE_DIR, "mixsy-website", "images")
OUTPUT_DIR = IMAGES_DIR  # Overwrite existing PNGs

PRODUCTS = {
    "cremas-cocoye": {
        "src": "cremas-cocoye.jpeg",
        "out": "cremas-cocoye.png",
        "desc": "a cream-colored bottle of Haitian cremas (coconut cream liqueur) with a gold cap and a beige/cream label reading 'La Belle Miyou Cremas'",
    },
    "liqueur-grenadine": {
        "src": "liqueur-grenadine.jpeg",
        "out": "liqueur-grenadine.png",
        "desc": "a tall rose/pink bottle of Haitian grenadine liqueur with a gold cap and a label reading 'La Belle Miyou Liqueur Grenadine'",
    },
    "epis-lakay": {
        "src": "epis-lakay.jpeg",
        "out": "epis-lakay.png",
        "desc": "a mason jar of traditional Haitian spice base (epis) with a metal lid, containing yellow-green seasoning paste, with a label reading 'La Belle Miyou Epis Lakay'",
    },
    "bon-piman": {
        "src": "bon-piman.jpeg",
        "out": "bon-piman.png",
        "desc": "a small bottle of Haitian hot sauce with a red wax seal cap and twine tag, containing amber/red hot sauce, with a label reading 'La Belle Miyou Bon Piman'",
    },
}

STUDIO_PROMPT = """Transform this product photo into a professional studio product photograph.

Requirements:
- Place the product centered on a warm cream/beige studio background (similar to #E0D5C5)
- The background should have a subtle radial vignette (slightly darker at the edges)
- Professional soft studio lighting from above-left, creating gentle highlights on the product
- A subtle contact shadow beneath the product on the surface
- The product should fill approximately 70% of the frame height
- Keep ALL labels, text, logos, and branding on the product EXACTLY as they appear — do not alter, remove, or regenerate any text on the product
- Clean, editorial, premium product photography style
- High quality, sharp focus on the product
- The product is {desc}

This should look like a high-end e-commerce or magazine product photograph."""


def generate_studio_image(src_path, output_path, desc, retries=2):
    """Generate a studio product photo from a source image using Gemini."""
    from google import genai
    from google.genai import types

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("  ERROR: GOOGLE_API_KEY not set in .env")
        return False

    client = genai.Client(api_key=api_key)

    # Load source image
    with open(src_path, "rb") as f:
        image_data = f.read()

    prompt = STUDIO_PROMPT.format(desc=desc)

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(data=image_data, mime_type="image/jpeg"),
                types.Part.from_text(text=prompt),
            ],
        )
    ]

    config = types.GenerateContentConfig(
        response_modalities=["IMAGE", "TEXT"],
        temperature=0.4,
    )

    for attempt in range(retries + 1):
        try:
            print(f"  Generating (attempt {attempt + 1}/{retries + 1})...", flush=True)
            response = client.models.generate_content(
                model="gemini-2.0-flash-exp-image-generation",
                contents=contents,
                config=config,
            )

            if response.candidates:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, "inline_data") and part.inline_data:
                        with open(output_path, "wb") as f:
                            f.write(part.inline_data.data)
                        file_size_kb = os.path.getsize(output_path) / 1024
                        print(f"  Saved: {output_path} ({file_size_kb:.0f} KB)")
                        return True
                    elif hasattr(part, "text") and part.text:
                        print(f"  Model text response: {part.text[:200]}")

            if attempt < retries:
                print(f"  No image returned, retrying in 3s...")
                time.sleep(3)
            else:
                print(f"  [FAIL] No image generated after {retries + 1} attempts")
                return False

        except Exception as e:
            error_msg = str(e)
            print(f"  Error: {error_msg[:200]}")
            if attempt < retries:
                wait = 5 * (attempt + 1)
                print(f"  Retrying in {wait}s...")
                time.sleep(wait)
            else:
                return False

    return False


def main():
    parser = argparse.ArgumentParser(description="Generate studio product images")
    parser.add_argument("--only", type=str, help="Process only this product")
    parser.add_argument("--dry-run", action="store_true", help="Show what would run")
    args = parser.parse_args()

    if args.only:
        if args.only not in PRODUCTS:
            print(f"Unknown product: {args.only}")
            print(f"Available: {', '.join(PRODUCTS.keys())}")
            sys.exit(1)
        targets = {args.only: PRODUCTS[args.only]}
    else:
        targets = PRODUCTS

    print(f"\n{'='*55}")
    print(f"House of Miyou — Studio Product Image Generation")
    print(f"{'='*55}\n")

    if args.dry_run:
        for name, config in targets.items():
            src = os.path.join(IMAGES_DIR, config["src"])
            out = os.path.join(OUTPUT_DIR, config["out"])
            exists = "EXISTS" if os.path.exists(src) else "MISSING"
            print(f"  [{name}] {src} ({exists}) -> {out}")
        print("\nDry run — no images generated.")
        return

    success = 0
    for name, config in targets.items():
        src_path = os.path.join(IMAGES_DIR, config["src"])
        out_path = os.path.join(OUTPUT_DIR, config["out"])

        print(f"[{name}]")
        if not os.path.exists(src_path):
            print(f"  ERROR: Source not found: {src_path}")
            print()
            continue

        file_size_mb = os.path.getsize(src_path) / (1024 * 1024)
        print(f"  Source: {src_path} ({file_size_mb:.1f} MB)")

        if generate_studio_image(src_path, out_path, config["desc"]):
            success += 1
        else:
            print(f"  FAILED — keeping existing image")

        print()
        # Brief pause between generations to avoid rate limits
        if name != list(targets.keys())[-1]:
            time.sleep(2)

    print(f"Done: {success}/{len(targets)} images generated successfully.")


if __name__ == "__main__":
    main()
