#!/usr/bin/env python3
"""
Generate narration audio for Voice Receptionist video using ElevenLabs TTS.

Usage:
  python execution/generate_receptionist_narration.py

Output:
  tiktok-recreation/public/narration-receptionist/scene_00.mp3 ... scene_14.mp3
"""

import os
import time
import requests

ELEVENLABS_API_KEY = "sk_ca9e25701082fd7941547381912b051e8b6618330eaceb85"
OUTPUT_DIR = "tiktok-recreation/public/narration-receptionist"

# Voice: Roger (CwhRBWXzGAHq8TQ4Fs17)
VOICE_ID = "CwhRBWXzGAHq8TQ4Fs17"
MODEL_ID = "eleven_multilingual_v2"

# Scene texts (matching VoiceReceptionist.tsx SCENES array)
SCENES = [
    "Your phone rings at 8 PM. Nobody answers.",
    "62 percent of calls to small businesses go unanswered",
    "80 percent of those callers won't leave a voicemail",
    "They just call your competitor instead",
    "That's 75 thousand dollars per year walking out the door",
    "What if every call was answered instantly?",
    "AI voice receptionist picks up in one ring",
    "It sounds human. It IS that good.",
    "Qualifies leads and answers FAQs on the spot",
    "Books appointments directly into your calendar",
    "Sends you a summary of every single call",
    "24/7. Weekends. Holidays. Always on.",
    "No hold music. No missed opportunities.",
    "Your competitors still use voicemail. You won't.",
    "DM receptionist to never miss a call",
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
