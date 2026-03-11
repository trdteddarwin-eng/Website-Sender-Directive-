#!/usr/bin/env python3
"""
Generate narration audio for Automatic Email Reply video via KIE API.

Usage:
  python3 execution/generate_autoreply_narration.py

Output:
  yt-growth-chart/public/narration-autoreply/scene_00.mp3 ... scene_11.mp3
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kie_utils import generate_narration

OUTPUT_DIR = "yt-growth-chart/public/narration-autoreply"

SCENES = [
    "[matter-of-fact] Picture this. A hot prospect replies to your outreach — eleven PM on a Tuesday.",
    "[matter-of-fact] You're asleep. [pause] By morning... they've already booked a call with someone else.",
    "[serious] That deal? Gone. -- -- And you didn't even know it happened.",
    "[serious] Sixty-seven percent of deals go to whoever responds FIRST. [pause] Not the best offer. The fastest one.",
    "[excited] So we built an AI that replies to your emails — instantly — in YOUR voice.",
    "[confident] It reads every incoming message, understands the intent, and drafts a response that sounds exactly like you wrote it.",
    "[confident] Handles objections. Answers pricing questions. Books meetings on your calendar — without you lifting a finger.",
    '[excited] Urgent lead? It pings you. Routine stuff? Handled. [pause] You only touch the deals that MATTER.',
    "[matter-of-fact] One sales team plugged this in and cut their response time from six hours — to two minutes.",
    "[excited] Their reply rate jumped thirty-eight percent. [short pause] First month.",
    "[serious] Every minute you're not replying, that deal walks out the door — straight to a competitor who IS.",
    '[excited] DM reply to make sure you never lose another deal to your pillow.',
]


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Generating narration for {len(SCENES)} scenes via KIE API...")
    print(f"Voice: Liam (elevenlabs/text-to-dialogue-v3)\n")

    durations = []
    for i, text in enumerate(SCENES):
        output_path = os.path.join(OUTPUT_DIR, f"scene_{i:02d}.mp3")
        if os.path.exists(output_path):
            print(f"  Scene {i:2d}: already exists, skipping")
            continue
        clean = text.replace("[", "").replace("]", "")[:50]
        print(f"  Scene {i:2d}: \"{clean}\"", end="", flush=True)
        dur = generate_narration(text, output_path)
        if dur:
            durations.append(round(dur, 3))
            print(f" -> {dur:.2f}s")
        else:
            durations.append(3.0)
            print(" FAILED")

    total = len([f for f in os.listdir(OUTPUT_DIR) if f.endswith(".mp3")])
    print(f"\nDone! {total}/{len(SCENES)} narration files in {OUTPUT_DIR}/")
    if durations:
        print(f"AUDIO_DURATIONS = [{', '.join(str(d) for d in durations)}]")


if __name__ == "__main__":
    main()
