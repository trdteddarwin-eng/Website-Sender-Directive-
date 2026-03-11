#!/usr/bin/env python3
"""
Generate narration audio for WhatsApp Agent video via KIE API.

Usage:
  python3 execution/generate_whatsappagent_narration.py

Output:
  yt-growth-chart/public/narration-whatsappagent/scene_00.mp3 ... scene_11.mp3
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kie_utils import generate_narration

OUTPUT_DIR = "yt-growth-chart/public/narration-whatsappagent"

SCENES = [
    '[matter-of-fact] A customer sends your business a WhatsApp message. [pause] "Hey, how much for the full package?"',
    "[matter-of-fact] You're in a meeting. Three hours go by. -- -- Still no reply.",
    "[serious] They message your competitor. [short pause] Two minutes later — they're booked.",
    "[serious] Ninety percent of customers expect a response within TEN minutes. [pause] Three hundred conversations a month are going unanswered in your inbox right now.",
    "[excited] So we built an AI agent that lives inside your WhatsApp — and it never clocks out.",
    "[confident] It knows your entire business. Pricing, services, availability — answers questions in your brand voice, not some generic bot tone.",
    "[confident] Sends quotes. Books appointments. Handles support tickets — all inside the same chat thread.",
    "[excited] Complex issue? It hands off to your team with FULL context. [pause] No one repeats themselves.",
    "[matter-of-fact] One clinic plugged this in and went from missing half their messages — to responding to every single one in under sixty seconds.",
    "[excited] Forty percent higher engagement. [short pause] That's forty percent more conversations turning into REVENUE.",
    "[serious] Your customers are already on WhatsApp. Every message you miss — that's money walking to someone who showed up faster.",
    '[excited] DM whatsapp to stop leaving conversations — and cash — on the table.',
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
