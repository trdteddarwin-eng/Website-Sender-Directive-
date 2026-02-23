#!/usr/bin/env python3
"""
Generate per-scene sound effects for Voice Receptionist video using Replicate AudioGen.

Usage:
  python execution/generate_receptionist_sfx.py

Output:
  tiktok-recreation/public/sfx-receptionist/sfx_00.mp3 ... sfx_14.mp3
"""

import os
import time
from replicate_sfx import generate_sfx
OUTPUT_DIR = "tiktok-recreation/public/sfx-receptionist"

# Per-scene SFX prompts matched to Voice Receptionist video scenes
SFX_SCENES = [
    {"prompt": "phone ringing in empty dark room, echoing unanswered, lonely and ominous", "duration": 2.5},
    {"prompt": "multiple phone ring tones cutting off abruptly one by one, missed calls", "duration": 2.5},
    {"prompt": "phone hang-up click sound repeated, dial tone fading, abandonment", "duration": 2.5},
    {"prompt": "phone dialing new number with competitive urgency, switching attention", "duration": 2.5},
    {"prompt": "cash register opening with money being swept away, financial loss whoosh", "duration": 2.5},
    {"prompt": "bright phone pickup click with instant connection tone, clean and welcoming", "duration": 2.5},
    {"prompt": "single crisp phone ring then smooth robotic answer, professional and fast", "duration": 2.5},
    {"prompt": "warm natural human-like voice hum with smooth audio wave, pleasant and real", "duration": 2.5},
    {"prompt": "checklist items being ticked off rapidly, pen clicks and paper, organized efficiency", "duration": 2.5},
    {"prompt": "calendar appointment booking confirmation chime, scheduling click, organized", "duration": 2.5},
    {"prompt": "phone notification ping with text message whoosh, summary delivered", "duration": 2.5},
    {"prompt": "steady reliable hum with clock ticking 24 hours, always running, dependable", "duration": 2.5},
    {"prompt": "hold music cutting off abruptly then clean silence with success chime", "duration": 2.5},
    {"prompt": "old cassette tape rewinding versus modern digital activation sound, contrast", "duration": 2.5},
    {"prompt": "phone ringing with bright green energy pulse, answered perfectly, triumphant", "duration": 2.5},
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
