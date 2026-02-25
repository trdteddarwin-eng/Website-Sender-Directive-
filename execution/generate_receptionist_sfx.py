#!/usr/bin/env python3
"""
Generate per-scene sound effects for Voice Receptionist video using Replicate AudioGen.

Usage:
  python execution/generate_receptionist_sfx.py

Output:
  yt-growth-chart/public/sfx-receptionist/sfx_00.wav ... sfx_14.wav
"""

import os
import time
from replicate_sfx import generate_sfx

OUTPUT_DIR = "yt-growth-chart/public/sfx-receptionist"

# Per-scene SFX prompts matched to Voice Receptionist video scenes
SFX_SCENES = [
    {"prompt": "phone ringing then abruptly stopping with missed call buzz, opportunity lost", "duration": 3},
    {"prompt": "voicemail beep repeating with inbox full notification alarm", "duration": 3},
    {"prompt": "phone callback ringtone fading to static silence, no return", "duration": 3},
    {"prompt": "money coins draining down metal pipe drain, revenue loss", "duration": 3},
    {"prompt": "futuristic AI activation with phone pickup click and power surge", "duration": 3},
    {"prompt": "warm natural voice speaking with smooth audio waveform flow", "duration": 3},
    {"prompt": "triple checkmark stamps clicking in succession, qualification complete", "duration": 3},
    {"prompt": "calendar appointment booking confirmation chime, scheduling success", "duration": 3},
    {"prompt": "mobile notification ping with paper summary rustling", "duration": 3},
    {"prompt": "multiple phone lines connecting simultaneously with digital switchboard", "duration": 3},
    {"prompt": "globe spinning with multilingual voice whispers overlapping", "duration": 3},
    {"prompt": "steady reliable machine humming twenty four seven, always on", "duration": 3},
    {"prompt": "phone pickup on left side contrasting with voicemail beep on right, split", "duration": 3},
    {"prompt": "dollar bills with flapping wings flying away into distance, money lost", "duration": 3},
    {"prompt": "rocket engine ignition with ascending power and sparkle trail", "duration": 3},
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
