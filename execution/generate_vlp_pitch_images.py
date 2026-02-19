#!/usr/bin/env python3
"""
generate_vlp_pitch_images.py — Generate pitch images for Viva la Pizza.

Creates 3 pitch images using Gemini 3 Pro Image (text-to-image generation).
Brand colors: cream (#FFF8E7), olive green (#556B2F), red (#C41E3A), gold (#DAA520).

Usage:
    python3 execution/generate_vlp_pitch_images.py
"""

import os
import sys
import time
from dotenv import load_dotenv

load_dotenv()

MODEL = "gemini-3-pro-image-preview"
OUTPUT_DIR = ".tmp/vlp_pitch_images"

PITCH_IMAGES = [
    {
        "name": "pitch_before_after",
        "prompt": (
            "Professional marketing comparison graphic, split-screen layout. "
            "Left side labeled 'ANTES' in red: a phone screen showing a blurry, cramped static JPG restaurant menu "
            "with tiny unreadable text, no buttons, no interactivity — looks outdated and frustrating. "
            "Right side labeled 'DESPUÉS' in olive green (#556B2F): a phone screen showing a beautiful modern "
            "interactive digital menu with food photography cards, prices, category tabs, and a green "
            "'Ordenar por WhatsApp' button on each item. A big red arrow points from left to right. "
            "Bottom banner in cream (#FFF8E7) with olive text: 'Viva la Pizza — Menú Digital Interactivo'. "
            "Square format, clean professional design, suitable for WhatsApp."
        ),
    },
    {
        "name": "pitch_whatsapp_auto",
        "prompt": (
            "Professional marketing graphic showing a smartphone screen with a WhatsApp conversation. "
            "The conversation flow: Customer taps 'Ordenar' button → WhatsApp opens with pre-filled message "
            "'Hola! Me gustaría ordenar: Pizza Pepperoni Grande \U0001f355' → Restaurant chatbot auto-responds "
            "'Perfecto! Tu pedido está confirmado. Listo en 25 min \u23f1\ufe0f'. "
            "Green WhatsApp bubbles on a clean white background. "
            "Header text in olive green (#556B2F): 'Pedidos Automáticos por WhatsApp'. "
            "Bottom text: '24/7 — Sin esperas — Sin errores'. "
            "Square format, professional, suitable for WhatsApp."
        ),
    },
    {
        "name": "pitch_stats",
        "prompt": (
            "Clean professional infographic on cream background (#FFF8E7). "
            "Three large statistics displayed in a vertical stack with icons: "
            "'99 Platos Digitalizados \U0001f4cb' in olive green, "
            "'1 Click para Ordenar \U0001f4f1' in red (#C41E3A), "
            "'24/7 Atención Automática \U0001f916' in gold (#DAA520). "
            "Each stat has a subtle icon or accent. "
            "At the bottom: 'Viva la Pizza — Más Pedidos, Menos Fricción' in elegant dark text. "
            "Square format, clean modern design, suitable for WhatsApp."
        ),
    },
]


def generate_image(client, prompt, output_path, retries=2):
    """Generate a single image from a text prompt."""
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
                model=MODEL,
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
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not found in .env")
        sys.exit(1)

    from google import genai
    client = genai.Client(api_key=api_key)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Generating {len(PITCH_IMAGES)} Viva la Pizza pitch images...")
    print(f"Output: {OUTPUT_DIR}/")
    print()

    success = 0
    failed = 0

    for i, img in enumerate(PITCH_IMAGES):
        output_path = os.path.join(OUTPUT_DIR, f"{img['name']}.png")
        print(f"[{i+1}/{len(PITCH_IMAGES)}] {img['name']}...")

        result = generate_image(client, img["prompt"], output_path)
        if result:
            print(f"    Saved: {result}")
            success += 1
        else:
            print(f"    FAILED")
            failed += 1

        # Rate limit buffer
        if i < len(PITCH_IMAGES) - 1:
            time.sleep(2)

    print()
    print(f"Done! {success} generated, {failed} failed.")
    print(f"Images saved to: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
