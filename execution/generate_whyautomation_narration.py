#!/usr/bin/env python3
"""
Generate narration audio for WhyAutomation video using ElevenLabs TTS.

Usage:
  python execution/generate_whyautomation_narration.py

Output:
  tiktok-recreation/public/narration-whyautomation/scene_00.mp3 ... scene_14.mp3
"""

import os
import time
import requests

ELEVENLABS_API_KEY = "sk_ca9e25701082fd7941547381912b051e8b6618330eaceb85"
OUTPUT_DIR = "tiktok-recreation/public/narration-whyautomation"

VOICE_ID = "CwhRBWXzGAHq8TQ4Fs17"  # Roger
MODEL_ID = "eleven_multilingual_v2"

SCENES = [
    "Still running your business the old-fashioned way?",
    "While you type one email, AI sends a thousand",
    "Sixty percent of tasks you do daily are repeatable",
    "Scheduling, follow-ups, data entry, invoicing",
    "That's hours of your life you'll never get back",
    "But what if all of that ran on autopilot?",
    "AI doesn't sleep. AI doesn't forget.",
    "It replies to leads in under sixty seconds",
    "It books appointments while you sleep",
    "It writes proposals that actually close deals",
    "Businesses using AI grow three times faster",
    "And save over twenty hours every single week",
    "Your competitors already figured this out",
    "The question isn't if, it's how fast can you start",
    "DM me automate to start saving time today",
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
