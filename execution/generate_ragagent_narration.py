#!/usr/bin/env python3
"""
Generate narration audio for RAG Agent video using ElevenLabs TTS.

Usage:
  export $(grep -v '^#' .env | xargs) && python3 execution/generate_ragagent_narration.py

Output:
  yt-growth-chart/public/narration-ragagent/scene_00.mp3 ... scene_11.mp3
"""

import os
import time
import requests

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
OUTPUT_DIR = "yt-growth-chart/public/narration-ragagent"

# User's custom voice
VOICE_ID = "yj30vwTGJxSHezdAGsv9"
MODEL_ID = "eleven_multilingual_v2"

# 12 scenes — short, punchy, speakable
SCENES = [
    "Your team answers the same questions every day.",
    "Where's that document? What's our policy on this?",
    "Eighty percent of questions have the same answer.",
    "Your best people waste hours on repetitive lookup.",
    "What if your business had its own ChatGPT?",
    "Feed it your documents, policies, and knowledge.",
    "It learns everything about your company.",
    "Ask it anything. Get instant answers.",
    "No more digging through folders, emails, or Slack.",
    "It gets smarter with every conversation.",
    "Your competitors already have this running.",
    'DM "AI" to get your own business ChatGPT.',
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
                "stability": 0.45,
                "similarity_boost": 0.80,
                "style": 0.40,
            },
        },
        timeout=60,
    )
    resp.raise_for_status()

    with open(output_path, "wb") as f:
        f.write(resp.content)

    return len(resp.content) / 1024


def main():
    if not ELEVENLABS_API_KEY:
        print("ERROR: ELEVENLABS_API_KEY not set. Run: export $(grep -v '^#' .env | xargs)")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Generating narration for {len(SCENES)} scenes...")
    print(f"Voice ID: {VOICE_ID}")
    print(f"Model: {MODEL_ID}\n")

    generated = 0
    for i, text in enumerate(SCENES):
        output_path = os.path.join(OUTPUT_DIR, f"scene_{i:02d}.mp3")

        if os.path.exists(output_path):
            print(f"  Scene {i:2d}: already exists, skipping")
            continue

        print(f"  Scene {i:2d}: \"{text[:50]}\"", end="", flush=True)
        try:
            size = generate_scene_audio(text, output_path)
            print(f" -> {size:.1f}KB")
            generated += 1
        except Exception as e:
            print(f" FAILED: {e}")
            continue

        time.sleep(0.3)

    total = len([f for f in os.listdir(OUTPUT_DIR) if f.endswith(".mp3")])
    print(f"\nDone! {total}/{len(SCENES)} narration files in {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
