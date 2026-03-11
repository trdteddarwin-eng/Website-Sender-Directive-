#!/usr/bin/env python3
"""
Generate narration audio for Auto Follow-Up Email video via KIE API.

Usage:
  python3 execution/generate_followupemail_narration.py

Output:
  yt-growth-chart/public/narration-followupemail/scene_00.mp3 ... scene_11.mp3
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kie_utils import generate_narration

OUTPUT_DIR = "yt-growth-chart/public/narration-followupemail"

SCENES = [
    "[matter-of-fact] Picture this. You just sent a killer proposal to a roofing company in Phoenix.",
    "[matter-of-fact] Three days go by. You get busy. No follow-up.",
    "[serious] They sign with a competitor — who sent FIVE emails while you sent one.",
    "[serious] Here's the thing. [pause] Eighty percent of deals close after the fifth touchpoint. But forty-four percent of reps? [short pause] They stop after the FIRST.",
    "[excited] So we built a system that follows up for you — automatically.",
    "[confident] It writes personalized emails for every lead in your pipeline. Different tone, different angle, every single time.",
    "[confident] And it knows WHEN to send — morning, evening, Tuesday at ten — whatever gets the highest open rate for that prospect.",
    "[excited] Warm lead gets a nudge. Cold lead gets re-engaged. Hot lead gets the close. All without you touching your inbox.",
    "[matter-of-fact] One real estate team ran this for thirty days. Three hundred leads. Every single one got followed up — on time, every time.",
    "[excited] They closed forty-four percent MORE deals. [pause] That's an extra forty-two hundred a month they were leaving on the table.",
    "[serious] Every day without this, deals are dying in your inbox. [short pause] Not because they said no — because you never asked AGAIN.",
    '[excited] DM followup — and stop bleeding revenue to silence.',
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
