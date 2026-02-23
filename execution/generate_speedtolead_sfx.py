#!/usr/bin/env python3
"""
Generate per-scene sound effects for Speed To Lead video using Replicate AudioGen.

Usage:
  python execution/generate_speedtolead_sfx.py

Output:
  yt-growth-chart/public/sfx-speedtolead/sfx_00.mp3 ... sfx_14.mp3
"""

import os
import time
from replicate_sfx import generate_sfx
OUTPUT_DIR = "yt-growth-chart/public/sfx-speedtolead"

# Per-scene SFX prompts matched to Speed To Lead video scenes
SFX_SCENES = [
    {"prompt": "mouse click then digital form submission whoosh sound, clean interface", "duration": 3},
    {"prompt": "ticking clock accelerating faster and faster, countdown timer urgent pressure", "duration": 3},
    {"prompt": "deep prestigious academic reveal tone, scholarly announcement, impressive", "duration": 3},
    {"prompt": "phone ringing fading slowly into silence and empty void, missed connection", "duration": 3},
    {"prompt": "glass shattering crash impact with bar chart falling, destructive collapse", "duration": 3},
    {"prompt": "electric zap with lightning crack then smooth power up activation, energetic", "duration": 3},
    {"prompt": "warm natural human voice hum with smooth audio waveform, pleasant and real", "duration": 3},
    {"prompt": "triple checkmark stamps clicking in rapid succession, organized efficient", "duration": 3},
    {"prompt": "calendar appointment booking confirmation chime, scheduling click organized", "duration": 3},
    {"prompt": "smooth routing swoosh with connection established tone, transfer complete", "duration": 3},
    {"prompt": "steady reliable engine humming continuously, tireless machine running", "duration": 3},
    {"prompt": "cash register ching with downward cost savings chime, money saved celebration", "duration": 3},
    {"prompt": "multiple racing swooshes accelerating ahead, competitive robots rushing forward", "duration": 3},
    {"prompt": "footsteps walking away with coins dropping and fading, money leaving", "duration": 3},
    {"prompt": "rocket engine ignition building to powerful liftoff with ascending sparkle trail", "duration": 3},
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
