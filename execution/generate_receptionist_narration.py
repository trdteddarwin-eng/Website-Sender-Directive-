#!/usr/bin/env python3
"""
Generate narration audio for Voice Receptionist video using ElevenLabs TTS.

Usage:
  python execution/generate_receptionist_narration.py

Output:
  yt-growth-chart/public/narration-receptionist/scene_00.mp3 ... scene_14.mp3
"""

import os
import time
import requests

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "sk_19970146a3f8d3964e93feb3aff4acb54b2732be03e2cf5c")
OUTPUT_DIR = "yt-growth-chart/public/narration-receptionist"

# Voice: Roger (CwhRBWXzGAHq8TQ4Fs17)
VOICE_ID = "CwhRBWXzGAHq8TQ4Fs17"
MODEL_ID = "eleven_multilingual_v2"

# Scene narration texts (speakable — no special characters, numbers spelled out)
SCENES = [
    "That call you just missed? It was a ten thousand dollar client",
    "Sixty two percent of calls go to voicemail",
    "Most people never call back",
    "You're losing revenue every single ring",
    "What if AI answered every call instantly?",
    "Picks up in one ring. Sounds completely human.",
    "Qualifies the caller. Asks the right questions.",
    "Books appointments right on your calendar",
    "Sends you a summary of every call",
    "Handles ten calls at once. Zero hold time.",
    "Speaks any language your clients speak",
    "Twenty four seven. Including holidays.",
    "Your competitor picks up. You don't. They win.",
    "Every missed call is a missed deal",
    "DM receptionist to get your AI receptionist",
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

    return len(resp.content) / 1024


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
