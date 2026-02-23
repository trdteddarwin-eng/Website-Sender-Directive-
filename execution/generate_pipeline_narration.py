#!/usr/bin/env python3
"""
Generate narration audio for PipelinePresentation video using ElevenLabs TTS.

Usage:
  python execution/generate_pipeline_narration.py

Output:
  tiktok-recreation/public/narration-pipeline/scene_00.mp3 ... scene_31.mp3
"""

import os
import time
import requests

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "sk_ca9e25701082fd7941547381912b051e8b6618330eaceb85")
OUTPUT_DIR = "tiktok-recreation/public/narration-pipeline"

VOICE_ID = "CwhRBWXzGAHq8TQ4Fs17"  # Roger
MODEL_ID = "eleven_multilingual_v2"

# 32 slides — speakable narration text for each
SCENES = [
    # 0 - Title
    "How I built an AI video pipeline. From one sentence to a finished TikTok in five minutes.",
    # 1 - Hook visual
    "I type one sentence. And five minutes later, I have a fully edited TikTok video with narration, sound effects, and custom graphics.",
    # 2 - Manual process
    "The old way? Write the script, thirty minutes. Record voiceover, twenty minutes. Find sound effects, fifteen minutes. Edit in the timeline, forty five minutes. Export and upload, ten minutes. That's two hours per video.",
    # 3 - Architecture
    "The solution is a three layer system. Directives tell the agent what to do. Orchestration handles decision making. And execution scripts do the actual work.",
    # 4 - Layer 1 Directives
    "Layer one: Directives. These are markdown files that act as standard operating procedures. They define goals, inputs, tools, outputs, and edge cases. Like giving clear instructions to a mid-level employee.",
    # 5 - Directive code
    "Here's the actual directive for TikTok videos. It defines a scene formula table. Hook scenes in red, pain points, a green shift to the solution, proof of results, urgency, and a call to action.",
    # 6 - Scene formula
    "Every video follows this arc. Scenes zero and one are the hook in red. Two through four are pain points. Five and six shift to green, introducing the solution. Seven through nine prove how it works. Twelve and thirteen create urgency. And scene fourteen is always the call to action.",
    # 7 - Orchestration flow
    "Layer two is where Claude sits. It reads the directive, writes the script, creates the Remotion composition, then calls the execution scripts in order. Narration, sound effects, then render.",
    # 8 - Agent decision making
    "The agent makes intelligent routing decisions. It reads the directive, parses the inputs, checks for existing scripts, routes to the correct execution tool, handles errors with retries, and updates the directive with anything it learns.",
    # 9 - Execution scripts
    "Layer three: the execution scripts. Generate narration with ElevenLabs text to speech. Generate sound effects with the sound effects API. Render with Remotion, turning React into MP4. And inject into CapCut with a custom Python script.",
    # 10 - ElevenLabs narration flow
    "For narration, each scene's text goes through the ElevenLabs API and comes back as an MP3 file. Fifteen scenes, fifteen audio clips, all generated automatically.",
    # 11 - Narration code
    "Here's the actual code. It loops through each scene, calls the text to speech API with the Roger voice and multilingual v2 model, then saves each chunk to an MP3 file.",
    # 12 - SFX flow
    "Sound effects work the same way. Each scene gets a descriptive prompt like dramatic tension hit with low rumble. The API generates a two and a half second MP3 clip for each one.",
    # 13 - Remotion title
    "Remotion. Video creation in React. This is what makes the whole thing possible. You write React components, and Remotion renders them frame by frame into a real MP4 video.",
    # 14 - Composition structure
    "The composition uses Transition Series. Each scene is a sequence with seventy frames, about two point three seconds. Between scenes, there's a ten frame fade transition. The total is eleven hundred ninety frames.",
    # 15 - SVG graphics
    "Every scene gets a custom SVG graphic. Animated circles, rotating rectangles, robot icons. All built with React and Remotion's interpolate and spring functions.",
    # 16 - TransitionSeries timeline
    "Here's how the timeline looks. Fifteen colored slots, one per scene. Red for problem scenes, green for solution scenes. The fade transitions overlap by ten frames between each slot.",
    # 17 - Audio layers
    "Each scene has three audio layers stacked together. The video track on top, narration in the middle at full volume, and sound effects on the bottom at forty percent volume with fade in and fade out.",
    # 18 - Render command
    "Rendering is one command. N P X remotion render, the composition name, and the output path. You can customize the codec, quality, and scale. Or use remotion studio to preview in the browser.",
    # 19 - CapCut title
    "CapCut integration. This was the hardest part of the entire pipeline.",
    # 20 - CapCut JSON
    "CapCut stores projects as a JSON file called draft info dot json. Inside, there's a materials object with arrays for videos and audios, and a tracks array with segments that reference those materials.",
    # 21 - draft_info.json skeleton
    "Here's the skeleton. Materials contain the video and audio references. Tracks define the timeline with segments. Each segment points to a material by ID and specifies its position on the timeline.",
    # 22 - Video material
    "A video material needs a unique ID, a local material ID for CapCut's internal database, the absolute path to the file in the Resources folder, the duration in microseconds, and the width and height.",
    # 23 - Audio material
    "Audio materials are similar. A unique ID, local material ID, the path to the MP3 file, the duration, and the name. The volume is set at the segment level, not the material level.",
    # 24 - Path resolution
    "The key fix: copy all media files into the project's Resources folder, then use absolute paths. CapCut's placeholder path format didn't work for programmatically generated projects.",
    # 25 - Cloud sync
    "Once the project is on your Mac, CapCut's cloud sync pushes it to your iPad and iPhone automatically. You can edit on mobile and publish directly.",
    # 26 - Stats
    "Eleven videos. All generated with this pipeline. AI Automation, Email Automation, Voice Receptionist, Why Ads, Why SEO, Why Website, Good versus Bad Ads, AI Chatbot, Social Media Marketing, Smart AI, and more.",
    # 27 - Live demo title
    "Let me show you a live demo. Watch the pipeline in action.",
    # 28 - Pipeline stages
    "Here are the five stages. Start with a topic. The agent writes the script. Audio is generated for narration and sound effects. Remotion renders the video. And the CapCut script injects it into a project. Total time: about five minutes.",
    # 29 - Self-annealing title
    "Self annealing. This is what makes the system get smarter over time.",
    # 30 - Error fix update
    "When something breaks, the system follows a loop. Hit an error during execution. Fix the script automatically. Update the directive with the new knowledge. Now the system is stronger. Errors become permanent rules logged in the Claude MD file.",
    # 31 - Speed stat
    "Five minutes. From topic to finished TikTok. That's twenty four times faster than doing it manually. Build your own pipeline. The code is on GitHub. Subscribe for more AI automation content.",
]


def generate_scene_audio(text, output_path):
    resp = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
        headers={
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
        },
        json={
            "text": text,
            "model_id": MODEL_ID,
            "voice_settings": {
                "stability": 0.6,
                "similarity_boost": 0.75,
                "style": 0.3,
            },
        },
        timeout=60,
    )
    resp.raise_for_status()
    with open(output_path, "wb") as f:
        f.write(resp.content)
    return len(resp.content) / 1024


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Generating narration for {len(SCENES)} slides using Roger voice...")
    print(f"Output: {OUTPUT_DIR}/\n")

    for i, text in enumerate(SCENES):
        output_path = os.path.join(OUTPUT_DIR, f"scene_{i:02d}.mp3")
        if os.path.exists(output_path):
            print(f"  Slide {i:2d}: already exists, skipping")
            continue
        print(f"  Slide {i:2d}: \"{text[:50]}\"", end="", flush=True)
        try:
            size = generate_scene_audio(text, output_path)
            print(f" -> {size:.1f}KB")
        except Exception as e:
            print(f" FAILED: {e}")
            continue
        time.sleep(0.3)

    generated = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".mp3")]
    print(f"\nDone! Generated {len(generated)}/{len(SCENES)} narration files in {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
