#!/usr/bin/env python3
"""
Generate per-scene sound effects for AI Chatbot video via KIE API.

Usage:
  python3 execution/generate_chatbot_sfx.py

Output:
  yt-growth-chart/public/sfx-chatbot/sfx_00.mp3 ... sfx_14.mp3
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kie_utils import generate_sfx

OUTPUT_DIR = "yt-growth-chart/public/sfx-chatbot"

SFX_PROMPTS = [
    "chat notification bubble pop sound with waiting ambient",
    "clock ticking slowly with heavy dramatic weight, time passing",
    "crowd footsteps walking away and fading into distance, abandonment",
    "heart monitor beeping slowing to flatline with dramatic tension",
    "electric lightning strike with digital mail sorting whoosh sounds",
    "scanning laser beam reading documents with electronic parsing beeps",
    "database search query with successful retrieval chime ascending",
    "rapid paper shuffling with multiple stamp sounds, efficient processing",
    "smooth handoff relay baton pass with collaborative chime",
    "stopwatch clicking then triumphant success chime, fast completion",
    "globe spinning with multilingual whispers and channel switching clicks",
    "rapid fire keyboard typing with parallel processing electronic hum",
    "competitor racing ahead swoosh while stuck engine sputters behind",
    "people fading away with coins dropping and echo, customer loss",
    "rocket engine ignition building to liftoff with ascending sparkle",
]


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Generating SFX for {len(SFX_PROMPTS)} scenes via KIE API...")
    print(f"Model: elevenlabs/sound-effect-v2\n")

    for i, prompt in enumerate(SFX_PROMPTS):
        output_path = os.path.join(OUTPUT_DIR, f"sfx_{i:02d}.mp3")
        if os.path.exists(output_path):
            print(f"  Scene {i:2d}: already exists, skipping")
            continue
        print(f"  Scene {i:2d}: \"{prompt[:60]}\"", end="", flush=True)
        size = generate_sfx(prompt, 3.0, output_path)
        if size:
            print(f" -> {size:.1f}KB")
        else:
            print(" FAILED")

    generated = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".mp3")]
    print(f"\nDone! {len(generated)}/{len(SFX_PROMPTS)} SFX files in {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
