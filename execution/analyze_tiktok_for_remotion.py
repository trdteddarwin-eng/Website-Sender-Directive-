#!/usr/bin/env python3
"""
Download a TikTok video and analyze it frame-by-frame for Remotion recreation.
Uses Claude Vision to break down each scene's text, visuals, and animations.

Usage:
  python execution/analyze_tiktok_for_remotion.py <tiktok_url> [--num-frames 15]

Output:
  .tmp/tiktok-recreation/source.mp4
  .tmp/tiktok-recreation/analysis.json
"""

import argparse
import base64
import json
import os
import subprocess
import sys
import time

import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
VISION_MODEL = "anthropic/claude-sonnet-4-5-20250929"
TMP_DIR = ".tmp/tiktok-recreation"


def download_video(url, output_path):
    """Download TikTok video via yt-dlp."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cmd = ["yt-dlp", "-o", output_path, "--force-overwrites", url]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp failed: {result.stderr}")
    # yt-dlp may append extension — find the actual file
    if not os.path.exists(output_path):
        # Check for common yt-dlp output patterns
        base = os.path.splitext(output_path)[0]
        for ext in [".mp4", ".webm", ".mkv"]:
            if os.path.exists(base + ext):
                os.rename(base + ext, output_path)
                break
    return output_path


def get_video_info(video_path):
    """Get video duration, fps, resolution via ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-show_entries", "stream=width,height,r_frame_rate",
        "-of", "json",
        video_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    data = json.loads(result.stdout)
    duration = float(data["format"]["duration"])
    stream = data["streams"][0]
    width = stream["width"]
    height = stream["height"]
    fps_str = stream["r_frame_rate"]
    fps_num, fps_den = map(int, fps_str.split("/"))
    fps = fps_num / fps_den
    return {"duration": duration, "fps": round(fps, 2), "width": width, "height": height}


def extract_frames(video_path, num_frames, output_dir):
    """Extract evenly-spaced frames from video."""
    os.makedirs(output_dir, exist_ok=True)
    info = get_video_info(video_path)
    duration = info["duration"]

    if num_frames <= 1:
        timestamps = [duration / 2]
    else:
        interval = duration / (num_frames + 1)
        timestamps = [interval * (i + 1) for i in range(num_frames)]

    frames = []
    for i, ts in enumerate(timestamps):
        frame_path = os.path.join(output_dir, f"frame_{i:03d}.jpg")
        cmd = [
            "ffmpeg", "-y", "-ss", str(ts),
            "-i", video_path,
            "-vframes", "1",
            "-q:v", "2",
            frame_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and os.path.isfile(frame_path):
            frames.append({"path": frame_path, "timestamp": round(ts, 2)})

    return frames, info


def frames_to_base64(frames):
    """Convert frame files to base64 for API."""
    result = []
    for f in frames:
        with open(f["path"], "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode()
        result.append({
            "timestamp": f["timestamp"],
            "base64": b64,
        })
    return result


def analyze_with_vision(frames_b64, video_info):
    """Send frames to Claude Vision for scene-by-scene analysis."""

    content = [
        {
            "type": "text",
            "text": f"""You are analyzing a TikTok video for recreation in Remotion (React video framework).

Video info: {video_info['duration']:.1f}s duration, {video_info['fps']:.0f}fps, {video_info['width']}x{video_info['height']}

I'm sending you {len(frames_b64)} evenly-spaced frames from this video. This is a motion-graphics style video from @conversion.doc with white text on black backgrounds, animated shapes/icons, and smooth transitions. Title: "Stop overcomplicating and start oversimplifying."

For EACH frame, analyze:
1. **text_content**: The exact text shown (preserve line breaks with \\n)
2. **text_position**: Where text is placed (top, center, bottom, top-left, etc.)
3. **text_size**: Relative size (small, medium, large, xl)
4. **background_color**: Hex color of the background
5. **visual_elements**: List of visual elements (dots, rings, lines, icons, shapes, etc.) with descriptions of position, size, color
6. **animation_hints**: What animation type likely produced this state (spring entrance, interpolate drift, pulse, glow sweep, particle burst, etc.)
7. **scene_mood**: Brief mood/energy description

Also provide these GLOBAL properties:
- **font_family**: Best guess at font (likely Inter or similar sans-serif)
- **font_weight**: Primary weight used (400, 700, 900)
- **font_color**: Primary text color (hex)
- **transition_type**: How scenes transition (fade, slide, cut, etc.)
- **transition_duration_estimate**: Estimated transition duration in seconds
- **total_scenes_estimate**: How many distinct scenes you think the full video has

Return a JSON object with this structure:
{{
  "global": {{
    "font_family": "Inter",
    "font_weight": "700",
    "font_color": "#FFFFFF",
    "transition_type": "fade",
    "transition_duration_estimate": 0.33,
    "total_scenes_estimate": 15
  }},
  "scenes": [
    {{
      "frame_index": 0,
      "timestamp": 1.5,
      "text_content": "Line one\\nLine two",
      "text_position": "top",
      "text_size": "large",
      "background_color": "#000000",
      "visual_elements": ["small white dot at center", "glowing ring expanding"],
      "animation_hints": "spring entrance, dot drifting down-right",
      "scene_mood": "attention-grabbing"
    }}
  ]
}}

Return ONLY the JSON, no markdown fences or extra text."""
        }
    ]

    # Add each frame as an image
    for i, f in enumerate(frames_b64):
        content.append({
            "type": "text",
            "text": f"--- Frame {i} (timestamp: {f['timestamp']:.1f}s) ---"
        })
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{f['base64']}"
            }
        })

    for attempt in range(3):
        try:
            if attempt > 0:
                time.sleep(5)
                print(f"  Retry attempt {attempt + 1}...")

            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": VISION_MODEL,
                    "max_tokens": 8000,
                    "messages": [{"role": "user", "content": content}],
                },
                timeout=420,
            )
            resp.raise_for_status()
            text = resp.json()["choices"][0]["message"]["content"].strip()

            # Strip markdown fences if present
            if text.startswith("```"):
                lines = text.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                text = "\n".join(lines)

            return json.loads(text)

        except json.JSONDecodeError as e:
            print(f"  JSON parse failed on attempt {attempt + 1}: {e}")
            print(f"  Raw response (first 500 chars): {text[:500]}")
            if attempt == 2:
                raise
        except Exception as e:
            print(f"  Attempt {attempt + 1} failed: {e}")
            if attempt == 2:
                raise

    raise RuntimeError("All analysis attempts failed")


def main():
    parser = argparse.ArgumentParser(description="Analyze TikTok video for Remotion recreation")
    parser.add_argument("url", help="TikTok video URL")
    parser.add_argument("--num-frames", type=int, default=15, help="Number of frames to extract")
    parser.add_argument("--skip-download", action="store_true", help="Skip download if source.mp4 exists")
    args = parser.parse_args()

    video_path = os.path.join(TMP_DIR, "source.mp4")
    frames_dir = os.path.join(TMP_DIR, "frames")
    analysis_path = os.path.join(TMP_DIR, "analysis.json")

    # Step 1: Download
    if args.skip_download and os.path.exists(video_path):
        print(f"Skipping download, using existing: {video_path}")
    else:
        print("Downloading video...")
        download_video(args.url, video_path)
        print(f"  Saved to {video_path}")

    # Step 2: Extract frames
    print(f"Extracting {args.num_frames} frames...")
    frames, info = extract_frames(video_path, args.num_frames, frames_dir)
    print(f"  Extracted {len(frames)} frames from {info['duration']:.1f}s video")
    print(f"  Resolution: {info['width']}x{info['height']}, FPS: {info['fps']}")

    # Step 3: Analyze with Vision
    print("Analyzing frames with Claude Vision...")
    frames_b64 = frames_to_base64(frames)
    analysis = analyze_with_vision(frames_b64, info)

    # Add video info to analysis
    analysis["video_info"] = info

    # Step 4: Save analysis
    with open(analysis_path, "w") as f:
        json.dump(analysis, f, indent=2)
    print(f"  Analysis saved to {analysis_path}")
    print(f"  Found {len(analysis.get('scenes', []))} scenes")

    return analysis


if __name__ == "__main__":
    main()
