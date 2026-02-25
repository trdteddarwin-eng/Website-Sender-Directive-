#!/usr/bin/env python3
"""
Generate per-scene sound effects for AI Chatbot video using Replicate AudioGen.

Usage:
  python execution/generate_chatbot_sfx.py

Output:
  yt-growth-chart/public/sfx-chatbot/sfx_00.wav ... sfx_14.wav
"""

import os
import time
from replicate_sfx import generate_sfx

OUTPUT_DIR = "yt-growth-chart/public/sfx-chatbot"

# Per-scene SFX prompts matched to AI Chatbot video scenes
SFX_SCENES = [
    {"prompt": "chat notification bubble pop sound with waiting ambient", "duration": 3},
    {"prompt": "clock ticking slowly with heavy dramatic weight, time passing", "duration": 3},
    {"prompt": "crowd footsteps walking away and fading into distance, abandonment", "duration": 3},
    {"prompt": "heart monitor beeping slowing to flatline with dramatic tension", "duration": 3},
    {"prompt": "electric lightning strike with digital mail sorting whoosh sounds", "duration": 3},
    {"prompt": "scanning laser beam reading documents with electronic parsing beeps", "duration": 3},
    {"prompt": "database search query with successful retrieval chime ascending", "duration": 3},
    {"prompt": "rapid paper shuffling with multiple stamp sounds, efficient processing", "duration": 3},
    {"prompt": "smooth handoff relay baton pass with collaborative chime", "duration": 3},
    {"prompt": "stopwatch clicking then triumphant success chime, fast completion", "duration": 3},
    {"prompt": "globe spinning with multilingual whispers and channel switching clicks", "duration": 3},
    {"prompt": "rapid fire keyboard typing with parallel processing electronic hum", "duration": 3},
    {"prompt": "competitor racing ahead swoosh while stuck engine sputters behind", "duration": 3},
    {"prompt": "people fading away with coins dropping and echo, customer loss", "duration": 3},
    {"prompt": "rocket engine ignition building to liftoff with ascending sparkle", "duration": 3},
]


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Generating SFX for {len(SFX_SCENES)} scenes via Replicate AudioGen...")
    print(f"Output: {OUTPUT_DIR}/\n")

    for i, scene in enumerate(SFX_SCENES):
        output_path = os.path.join(OUTPUT_DIR, f"sfx_{i:02d}.wav")

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

        time.sleep(12.0)  # rate limit: 6 req/min with <$5 credit

    generated = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".wav")]
    print(f"\nDone! Generated {len(generated)}/{len(SFX_SCENES)} SFX files in {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
