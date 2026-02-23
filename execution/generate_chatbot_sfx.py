#!/usr/bin/env python3
"""
Generate per-scene sound effects for AI Chatbot video using Replicate AudioGen.

Usage:
  python execution/generate_chatbot_sfx.py

Output:
  tiktok-recreation/public/sfx-chatbot/sfx_00.mp3 ... sfx_14.mp3
"""

import os
import time
from replicate_sfx import generate_sfx
OUTPUT_DIR = "tiktok-recreation/public/sfx-chatbot"

# Per-scene SFX prompts matched to AI Chatbot video scenes
SFX_SCENES = [
    {"prompt": "frustrated waiting sound with ticking clock, impatient notification dings fading", "duration": 2.5},
    {"prompt": "urgent stopwatch ticking with pressure building, time sensitive alarm", "duration": 2.5},
    {"prompt": "overlapping phone rings and notification sounds, overwhelmed chaos buzzing", "duration": 2.5},
    {"prompt": "door slamming shut with footsteps walking away, customer lost, departure", "duration": 2.5},
    {"prompt": "coins and money whooshing away into distance, financial loss fading", "duration": 2.5},
    {"prompt": "instant message pop with bright confirmation chime, fast and clean response", "duration": 2.5},
    {"prompt": "satisfying progress bar filling up with achievement unlock sound, completion", "duration": 2.5},
    {"prompt": "triple checkmark stamps in quick succession, organized and efficient clicks", "duration": 2.5},
    {"prompt": "smooth routing swoosh with connection established tone, transfer complete", "duration": 2.5},
    {"prompt": "digital neural network growing with soft electronic pulses, intelligence expanding", "duration": 2.5},
    {"prompt": "rapid fire message notification pings, many simultaneous, powerful and busy", "duration": 2.5},
    {"prompt": "steady powerful engine humming continuously, reliable and tireless machine", "duration": 2.5},
    {"prompt": "downward slide with positive savings chime, cost reduction celebration", "duration": 2.5},
    {"prompt": "competitive racing swooshes accelerating ahead, robots rushing forward fast", "duration": 2.5},
    {"prompt": "chat bubble pop with sparkle activation sound, ready to engage, bright", "duration": 2.5},
]


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Generating SFX for {len(SFX_SCENES)} scenes via Replicate AudioGen...")
    print(f"Output: {OUTPUT_DIR}/\n")

    for i, scene in enumerate(SFX_SCENES):
        output_path = os.path.join(OUTPUT_DIR, f"sfx_{i:02d}.mp3")

        if os.path.exists(output_path):
            print(f"  Scene {i:2d}: already exists, skipping")
            continue

        print(f"  Scene {i:2d}: \"{scene['prompt'][:60]}\" ({scene['duration']}s)", end="", flush=True)
        try:
            size = generate_sfx(scene["prompt"], scene["duration"], output_path)
            print(f" -> {size:.1f}KB")
        except Exception as e:
            print(f" FAILED: {e}")
            continue

        time.sleep(1.0)

    generated = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".mp3")]
    print(f"\nDone! Generated {len(generated)}/{len(SFX_SCENES)} SFX files in {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
