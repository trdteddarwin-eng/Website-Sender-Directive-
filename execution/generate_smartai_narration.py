#!/usr/bin/env python3
"""
Generate narration audio for SmartAI video using ElevenLabs TTS.

Usage:
  python execution/generate_smartai_narration.py

Output:
  tiktok-recreation/public/narration-smartai/scene_00.mp3 ... scene_14.mp3
"""

import os
import time
import requests

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "sk_ca9e25701082fd7941547381912b051e8b6618330eaceb85")
OUTPUT_DIR = "tiktok-recreation/public/narration-smartai"

VOICE_ID = "CwhRBWXzGAHq8TQ4Fs17"  # Roger
MODEL_ID = "eleven_multilingual_v2"

SCENES = [
    "Small businesses fail because they can't scale",
    "You're competing against companies ten times your size",
    "They have teams of fifty. You have a team of three",
    "But here's the secret. They're not working harder",
    "They automated everything you still do by hand",
    "AI automation is the great equalizer",
    "One AI workflow replaces an entire department",
    "Emails answered in seconds, not hours",
    "Leads followed up instantly, twenty four seven",
    "Reports generated while you sleep",
    "A three person team with the output of thirty",
    "Running nonstop, even on weekends",
    "The businesses that automate, survive",
    "The ones that don't, get left behind",
    "DM me scale to automate your business",
]


def generate_scene_audio(text, output_path):
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
    return len(resp.content) / 1024


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Generating narration for {len(SCENES)} scenes using Roger voice...")
    print(f"Output: {OUTPUT_DIR}/\n")

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
