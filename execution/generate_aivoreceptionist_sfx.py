#!/usr/bin/env python3
"""
Generate per-scene sound effects for Aivo Receptionist video using Replicate AudioGen.

Usage:
  python execution/generate_aivoreceptionist_sfx.py

Output:
  yt-growth-chart/public/sfx-aivoreceptionist/sfx_00.wav ... sfx_11.wav
"""

import os
import time
from replicate_sfx import generate_sfx

OUTPUT_DIR = "yt-growth-chart/public/sfx-aivoreceptionist"

# Per-scene SFX prompts matched to Aivo Receptionist after-hours video scenes
SFX_SCENES = [
    {"prompt": "phone ringing in empty dark office at night, echoing unanswered", "duration": 3},
    {"prompt": "phone hanging up click then competitor phone pickup with success chime", "duration": 3},
    {"prompt": "clock ticking steadily with phone calls ringing in background, after hours", "duration": 3},
    {"prompt": "money coins dropping and rolling away on hard floor, revenue lost", "duration": 3},
    {"prompt": "office door closing, footsteps leaving, phone still ringing in distance", "duration": 3},
    {"prompt": "futuristic AI activation power up surge with warm welcoming tone", "duration": 3},
    {"prompt": "clear natural voice pickup click with smooth digital connection sound", "duration": 3},
    {"prompt": "calendar appointment booking confirmation chime with pen writing", "duration": 3},
    {"prompt": "mobile notification ping with document summary sliding sound", "duration": 3},
    {"prompt": "steady reliable machine humming twenty four seven, clock ticking all hours", "duration": 3},
    {"prompt": "phone pickup on left side contrasting with voicemail beep on right, split", "duration": 3},
    {"prompt": "rocket engine ignition with ascending power and sparkle trail, launch", "duration": 3},
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
