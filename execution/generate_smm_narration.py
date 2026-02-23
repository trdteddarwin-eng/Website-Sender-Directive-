#!/usr/bin/env python3
"""
Generate narration audio for Social Media Marketing video using ElevenLabs TTS.

Usage:
  python execution/generate_smm_narration.py

Output:
  tiktok-recreation/public/narration-smm/scene_00.mp3 ... scene_14.mp3
"""

import os
import time
import requests

ELEVENLABS_API_KEY = os.environ.get(
    "ELEVENLABS_API_KEY",
    "sk_19970146a3f8d3964e93feb3aff4acb54b2732be03e2cf5c",
)
OUTPUT_DIR = "tiktok-recreation/public/narration-smm"

# Voice: Roger (CwhRBWXzGAHq8TQ4Fs17)
VOICE_ID = "CwhRBWXzGAHq8TQ4Fs17"
MODEL_ID = "eleven_multilingual_v2"

# Scene texts (speakable versions — no special chars, numbers spelled out)
SCENES = [
    "You're invisible online and losing clients daily",
    "Businesses without social media lose seventy percent of potential leads",
    "No posts, no stories, no engagement",
    "That's thousands of dollars walking to your competitors",
    "Social media marketing changes everything",
    "Strategic content that attracts your ideal clients",
    "Posts that convert followers into paying customers",
    "Targeted ads that reach the right people every time",
    "Consistent branding that builds trust and recognition",
    "The ROI speaks for itself",
    "Three hundred dollars in ads generates three thousand in revenue",
    "That's a ten x return on every dollar",
    "Your competitors are posting every single day",
    "Every week without content is revenue you'll never get back",
    "DM me social to grow your brand",
]


def generate_scene_audio(text, output_path):
    """Generate TTS audio for a single scene."""
    resp = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
        headers={
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
        },
        json={
            "text": text,
            "model_id": MODEL_ID,
            "voice_settings": {
                "stability": 0.6,
                "similarity_boost": 0.75,
                "style": 0.3,
            },
        },
        timeout=60,
    )
    resp.raise_for_status()

    with open(output_path, "wb") as f:
        f.write(resp.content)

    size_kb = len(resp.content) / 1024
    return size_kb


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Generating narration for {len(SCENES)} scenes using Roger voice...")
    print(f"Voice ID: {VOICE_ID}")
    print(f"Model: {MODEL_ID}\n")

    for i, text in enumerate(SCENES):
        output_path = os.path.join(OUTPUT_DIR, f"scene_{i:02d}.mp3")

        if os.path.exists(output_path):
            print(f"  Scene {i:2d}: already exists, skipping")
            continue

        print(f"  Scene {i:2d}: \"{text[:50]}\"", end="", flush=True)
        try:
            size = generate_scene_audio(text, output_path)
            print(f" -> {size:.1f}KB")
        except Exception as e:
            print(f" FAILED: {e}")
            continue

        time.sleep(0.3)

    generated = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".mp3")]
    print(f"\nDone! Generated {len(generated)}/{len(SCENES)} narration files in {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
