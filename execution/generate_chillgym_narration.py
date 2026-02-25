#!/usr/bin/env python3
"""
Generate narration audio for ChillGym video using ElevenLabs TTS.

Uses calmer voice settings (high stability, no style exaggeration)
for a zen, meditative tone.

Usage:
  python execution/generate_chillgym_narration.py

Output:
  yt-growth-chart/public/narration-chillgym/scene_00.mp3 ... scene_04.mp3
"""

import os
import time
import requests

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "sk_19970146a3f8d3964e93feb3aff4acb54b2732be03e2cf5c")
OUTPUT_DIR = "yt-growth-chart/public/narration-chillgym"

# Voice: Roger (CwhRBWXzGAHq8TQ4Fs17) — deep, calm male voice
VOICE_ID = "CwhRBWXzGAHq8TQ4Fs17"
MODEL_ID = "eleven_multilingual_v2"

# Scene narration — short, meditative, speakable
SCENES = [
    "The iron doesn't care about your excuses.",
    "One rep at a time. One day at a time.",
    "Discipline is choosing between what you want now, and what you want most.",
    "Your body hears everything your mind says.",
    "Show up. Every single day.",
]


def generate_scene_audio(text, output_path):
    """Generate TTS audio for a single scene with calm voice settings."""
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
                "stability": 0.85,       # high stability = calm, steady
                "similarity_boost": 0.75,
                "style": 0.0,            # no style exaggeration = natural
            },
        },
        timeout=60,
    )
    resp.raise_for_status()

    with open(output_path, "wb") as f:
        f.write(resp.content)

    return len(resp.content) / 1024


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Generating narration for {len(SCENES)} scenes using Roger voice (calm mode)...")
    print(f"Voice ID: {VOICE_ID}")
    print(f"Model: {MODEL_ID}")
    print(f"Settings: stability=0.85, style=0.0 (zen mode)\n")

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
