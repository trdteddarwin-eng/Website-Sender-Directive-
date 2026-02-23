#!/usr/bin/env python3
"""
Generate narration audio for each scene using ElevenLabs TTS.

Usage:
  python execution/generate_narration.py

Output:
  tiktok-recreation/public/narration/scene_00.mp3 ... scene_14.mp3
"""

import os
import sys
import time
import requests

ELEVENLABS_API_KEY = "sk_ca9e25701082fd7941547381912b051e8b6618330eaceb85"
OUTPUT_DIR = "tiktok-recreation/public/narration"

# Scene texts (matching RecreatedVideo.tsx SCENES array)
SCENES = [
    "Let's test",
    "your marketing knowledge",
    "What do you think performs better?",
    "You write a letter with 10 paragraphs",
    "to explain your business",
    "Or you can explain it with a 30 second video",
    "Sounds obvious",
    "but most businesses still overcomplicate",
    "Yes, information matters",
    "But how it's delivered matters even more",
    "A great video speaks to both sides",
    "logic and emotion at once",
    "action follows immediately",
    "So stop over-explaining and Start making people understand",
    "DM me animation to start selling without over-selling",
]


def list_voices():
    """List available ElevenLabs voices."""
    resp = requests.get(
        "https://api.elevenlabs.io/v1/voices",
        headers={"xi-api-key": ELEVENLABS_API_KEY},
        timeout=30,
    )
    resp.raise_for_status()
    voices = resp.json().get("voices", [])
    print(f"Available voices ({len(voices)}):")
    for v in voices[:15]:
        labels = v.get("labels", {})
        accent = labels.get("accent", "")
        gender = labels.get("gender", "")
        desc = labels.get("description", "")
        print(f"  {v['voice_id'][:12]}... | {v['name']:20s} | {gender:8s} | {accent:12s} | {desc}")
    return voices


def generate_scene_audio(text, voice_id, output_path, model_id="eleven_multilingual_v2"):
    """Generate TTS audio for a single scene."""
    resp = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        headers={
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
        },
        json={
            "text": text,
            "model_id": model_id,
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

    # List voices to find a good narrator
    print("Fetching available voices...")
    voices = list_voices()

    # Pick a voice — prefer a male narrator with clear delivery
    # Default to "Adam" (deep male) or first available
    voice_id = None
    preferred = ["Adam", "Josh", "Daniel", "Arnold", "Charlie"]
    for name in preferred:
        match = [v for v in voices if v["name"].lower() == name.lower()]
        if match:
            voice_id = match[0]["voice_id"]
            print(f"\nUsing voice: {match[0]['name']} ({voice_id})")
            break

    if not voice_id and voices:
        voice_id = voices[0]["voice_id"]
        print(f"\nUsing first available voice: {voices[0]['name']} ({voice_id})")

    if not voice_id:
        print("ERROR: No voices available")
        sys.exit(1)

    # Generate narration for each scene
    print(f"\nGenerating narration for {len(SCENES)} scenes...")
    for i, text in enumerate(SCENES):
        output_path = os.path.join(OUTPUT_DIR, f"scene_{i:02d}.mp3")

        if os.path.exists(output_path):
            print(f"  Scene {i:2d}: already exists, skipping")
            continue

        print(f"  Scene {i:2d}: \"{text[:40]}...\"", end="", flush=True)
        try:
            size = generate_scene_audio(text, voice_id, output_path)
            print(f" -> {size:.1f}KB")
        except Exception as e:
            print(f" FAILED: {e}")
            continue

        # Small delay to avoid rate limiting
        time.sleep(0.3)

    # Verify all files exist
    generated = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".mp3")]
    print(f"\nDone! Generated {len(generated)}/{len(SCENES)} narration files in {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
