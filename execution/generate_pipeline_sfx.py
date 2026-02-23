#!/usr/bin/env python3
"""
Generate per-slide sound effects for PipelinePresentation using Replicate AudioGen.

Usage:
  python execution/generate_pipeline_sfx.py

Output:
  tiktok-recreation/public/sfx-pipeline/sfx_00.mp3 ... sfx_31.mp3
"""

import os
import time
from replicate_sfx import generate_sfx
OUTPUT_DIR = "tiktok-recreation/public/sfx-pipeline"

SFX_SCENES = [
    # 0 - Title
    {"prompt": "cinematic dark ambient whoosh with subtle digital sparkle, epic introduction, technology reveal", "duration": 3.0},
    # 1 - Hook visual
    {"prompt": "futuristic digital transformation sound, morphing data into visual, clean technology process", "duration": 3.0},
    # 2 - Manual process
    {"prompt": "ticking clock getting faster, time pressure building, repetitive and exhausting loop", "duration": 3.0},
    # 3 - Architecture
    {"prompt": "ascending digital chime sequence, three layered tones building up, organized system activation", "duration": 3.0},
    # 4 - Directives
    {"prompt": "page turning with subtle digital overlay, document reveal, organized filing sound", "duration": 3.0},
    # 5 - Directive code
    {"prompt": "keyboard typing with terminal beeps, code appearing on screen, developer workflow", "duration": 3.0},
    # 6 - Scene formula
    {"prompt": "strategic planning sound, pieces clicking into place, puzzle solving, satisfying arrangement", "duration": 3.0},
    # 7 - Orchestration flow
    {"prompt": "smooth flowing data stream, connected pipeline sounds, sequential process activation", "duration": 3.0},
    # 8 - Agent decision making
    {"prompt": "neural network processing hum, branching decisions, intelligent routing clicks", "duration": 3.0},
    # 9 - Execution scripts
    {"prompt": "mechanical assembly line starting up, tools activating in sequence, factory production", "duration": 3.0},
    # 10 - ElevenLabs narration
    {"prompt": "human voice waveform visualization, audio wave morphing, speech synthesis activation", "duration": 3.0},
    # 11 - Narration code
    {"prompt": "code compiling with soft digital beeps, terminal output scrolling, API response received", "duration": 3.0},
    # 12 - SFX flow
    {"prompt": "layered sound effect creation, multiple audio textures blending, sound design studio", "duration": 3.0},
    # 13 - Remotion title
    {"prompt": "epic cinematic reveal with deep bass, technology brand presentation, powerful entrance", "duration": 3.0},
    # 14 - Composition structure
    {"prompt": "building blocks snapping together, modular construction, React component assembly", "duration": 3.0},
    # 15 - SVG graphics
    {"prompt": "vector shapes drawing themselves, pen tool swooshes, geometric animation sounds", "duration": 3.0},
    # 16 - TransitionSeries timeline
    {"prompt": "film reel advancing with smooth transitions, timeline scrubbing, video editing interface", "duration": 3.0},
    # 17 - Audio layers
    {"prompt": "three audio tracks mixing together, layered sound design, professional mixing board", "duration": 3.0},
    # 18 - Render command
    {"prompt": "powerful computer processing render, GPU fans spinning up, video encoding progress", "duration": 3.0},
    # 19 - CapCut title
    {"prompt": "dramatic challenge reveal, obstacle encountered, determined resolve sound", "duration": 3.0},
    # 20 - CapCut JSON
    {"prompt": "nested data structure expanding, JSON tree unfolding, hierarchical organization", "duration": 3.0},
    # 21 - draft_info skeleton
    {"prompt": "blueprint unrolling, technical schematic reveal, architecture diagram", "duration": 3.0},
    # 22 - Video material
    {"prompt": "video file icon appearing with a pop, media import confirmation, file recognized", "duration": 3.0},
    # 23 - Audio material
    {"prompt": "audio waveform display, MP3 file loading, sound file confirmation tone", "duration": 3.0},
    # 24 - Path resolution
    {"prompt": "satisfying lock click, puzzle piece fitting perfectly, problem solved confirmation", "duration": 3.0},
    # 25 - Cloud sync
    {"prompt": "cloud upload whoosh with sync chime, data floating upward, wireless transfer complete", "duration": 3.0},
    # 26 - Stats
    {"prompt": "achievement unlocked fanfare, counter ticking up rapidly, impressive milestone celebration", "duration": 3.0},
    # 27 - Live demo title
    {"prompt": "stage lights turning on, spotlight activation, live performance beginning", "duration": 3.0},
    # 28 - Pipeline stages
    {"prompt": "assembly line progression with five distinct steps, each step a satisfying click forward", "duration": 3.0},
    # 29 - Self-annealing title
    {"prompt": "evolving ambient sound growing stronger, system upgrading, progressive improvement", "duration": 3.0},
    # 30 - Error fix update
    {"prompt": "error buzzer followed by repair sounds then triumphant chime, break then fix cycle", "duration": 3.0},
    # 31 - Speed stat
    {"prompt": "rocket ignition building to liftoff, fast acceleration, impressive speed achievement", "duration": 3.0},
]


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Generating SFX for {len(SFX_SCENES)} slides via Replicate AudioGen...")
    print(f"Output: {OUTPUT_DIR}/\n")

    for i, scene in enumerate(SFX_SCENES):
        output_path = os.path.join(OUTPUT_DIR, f"sfx_{i:02d}.mp3")
        if os.path.exists(output_path):
            print(f"  Slide {i:2d}: already exists, skipping")
            continue
        print(f"  Slide {i:2d}: \"{scene['prompt'][:60]}\" ({scene['duration']}s)", end="", flush=True)
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
