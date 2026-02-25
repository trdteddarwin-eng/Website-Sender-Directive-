#!/usr/bin/env python3
"""
Batch-analyze top N TikTok videos with Claude Vision to extract a style guide.
Uses frame extraction + OpenRouter Claude Vision API.

Usage:
  python3 execution/analyze_tiktok_batch.py \
    --videos-dir .tmp/tiktok_conversion_doc \
    --num-frames 10 \
    --top-n 5 \
    --output .tmp/tiktok_conversion_doc/style_guide.json
"""

import argparse
import base64
import json
import os
import subprocess
import sys
import time
from typing import Optional, List, Dict, Any

import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
# Claude Sonnet 4.5 on OpenRouter (vision-capable)
VISION_MODEL = "anthropic/claude-sonnet-4.5"


def get_video_info(video_path: str) -> Dict[str, Any]:
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
    # Find the video stream (skip audio-only streams)
    stream = None
    for s in data.get("streams", []):
        if "width" in s and "height" in s:
            stream = s
            break
    if not stream:
        # Fallback: assume 1080x1920 TikTok vertical
        return {"duration": duration, "fps": 30.0, "width": 1080, "height": 1920}
    width = stream["width"]
    height = stream["height"]
    fps_str = stream.get("r_frame_rate", "30/1")
    fps_num, fps_den = map(int, fps_str.split("/"))
    fps = fps_num / fps_den if fps_den else 30.0
    return {"duration": duration, "fps": round(fps, 2), "width": width, "height": height}


def extract_frames(video_path: str, num_frames: int, output_dir: str) -> List[Dict]:
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


def frames_to_base64(frames: List[Dict]) -> List[Dict]:
    """Convert frame files to base64 for API."""
    result = []
    for f in frames:
        with open(f["path"], "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode()
        result.append({"timestamp": f["timestamp"], "base64": b64})
    return result


def analyze_single_video(video_path: str, num_frames: int, video_idx: int) -> Optional[Dict]:
    """Analyze one video: extract frames, send to Claude Vision, return analysis."""
    video_name = os.path.basename(video_path)
    frames_dir = os.path.join(os.path.dirname(video_path), f"frames_{video_idx}")

    print(f"\n  [{video_idx + 1}] Analyzing {video_name}...")

    # Extract frames
    frames, info = extract_frames(video_path, num_frames, frames_dir)
    if not frames:
        print(f"    No frames extracted from {video_name}", file=sys.stderr)
        return None

    print(f"    Extracted {len(frames)} frames ({info['duration']:.1f}s, {info['width']}x{info['height']})")

    # Convert to base64
    frames_b64 = frames_to_base64(frames)

    # Build Vision API request
    content = [
        {
            "type": "text",
            "text": f"""You are analyzing a TikTok video for visual style extraction. This is from @conversion.doc, a motion-graphics creator known for clean, bold, minimalist animations.

Video info: {info['duration']:.1f}s, {info['fps']:.0f}fps, {info['width']}x{info['height']}

I'm sending {len(frames_b64)} evenly-spaced frames. Analyze the VISUAL STYLE in detail:

For EACH frame, extract:
1. **text_content**: Exact text shown (preserve line breaks with \\n)
2. **text_position**: Where text sits (center, top-center, bottom-center, etc.)
3. **text_size_relative**: How much of the screen width the text occupies (0.0-1.0)
4. **text_weight**: Font weight estimate (400, 700, 800, 900)
5. **text_alignment**: left, center, right
6. **background**: Exact hex color or gradient description
7. **visual_elements**: Detailed list of every graphic element — shapes, icons, lines, dots, rings, particles, glows. For each: type, position, size, color, opacity
8. **animation_state**: What animation phase this frame captures (entering, holding, exiting, mid-transition)
9. **animation_type**: Spring entrance, fade, scale-up, slide-in, morph, particle burst, glow pulse, etc.

Also provide GLOBAL style properties:
- **primary_colors**: Array of hex colors used most (backgrounds, text, accents)
- **font_family**: Best guess (Inter, Montserrat, etc.)
- **font_weights**: Array of weights used [700, 900]
- **text_color**: Primary text color hex
- **bg_color**: Primary background color hex
- **accent_colors**: Array of accent color hexes
- **animation_style**: Overall animation philosophy (spring-based, eased, linear, bouncy)
- **spring_config**: Best guess at spring parameters {{damping, stiffness, mass}}
- **transition_type**: How scenes transition (hard cut, crossfade, slide, morph)
- **transition_duration_ms**: Estimated transition time in milliseconds
- **graphic_style**: Description of the visual language (geometric, organic, minimal, etc.)
- **particle_usage**: How particles/dots/small elements are used
- **glow_usage**: How glow/bloom effects are used
- **text_entrance**: How text typically enters the frame
- **text_exit**: How text typically exits

Return ONLY valid JSON:
{{
  "global": {{...}},
  "scenes": [{{...}}]
}}"""
        }
    ]

    for i, f in enumerate(frames_b64):
        content.append({
            "type": "text",
            "text": f"--- Frame {i} (t={f['timestamp']:.1f}s) ---"
        })
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{f['base64']}"}
        })

    # Call API with retries
    for attempt in range(3):
        try:
            if attempt > 0:
                time.sleep(5)
                print(f"    Retry {attempt + 1}...")

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

            # Strip markdown fences
            if text.startswith("```"):
                lines = text.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                text = "\n".join(lines)

            analysis = json.loads(text)
            analysis["video_file"] = video_name
            analysis["video_info"] = info
            print(f"    Done — {len(analysis.get('scenes', []))} scenes analyzed")
            return analysis

        except json.JSONDecodeError as e:
            print(f"    JSON parse error (attempt {attempt + 1}): {e}", file=sys.stderr)
            if attempt == 2:
                print(f"    Raw (first 500): {text[:500]}", file=sys.stderr)
                return None
        except requests.exceptions.HTTPError as e:
            body = ""
            try:
                body = e.response.text[:500]
            except Exception:
                pass
            print(f"    HTTP error (attempt {attempt + 1}): {e}\n    Body: {body}", file=sys.stderr)
            if attempt == 2:
                return None
        except Exception as e:
            print(f"    Error (attempt {attempt + 1}): {e}", file=sys.stderr)
            if attempt == 2:
                return None

    return None


def aggregate_style_guide(analyses: List[Dict]) -> Dict:
    """Aggregate individual video analyses into a unified style guide."""
    if not analyses:
        return {}

    # Collect all global properties
    all_globals = [a.get("global", {}) for a in analyses if a.get("global")]

    # Aggregate colors by frequency
    all_primary_colors = []
    all_accent_colors = []
    all_font_weights = []
    all_bg_colors = []
    all_text_colors = []

    for g in all_globals:
        all_primary_colors.extend(g.get("primary_colors", []))
        all_accent_colors.extend(g.get("accent_colors", []))
        all_font_weights.extend(g.get("font_weights", []))
        bg = g.get("bg_color")
        if bg:
            all_bg_colors.append(bg)
        tc = g.get("text_color")
        if tc:
            all_text_colors.append(tc)

    def most_common(items, n=5):
        """Return n most common items."""
        if not items:
            return []
        from collections import Counter
        return [item for item, _ in Counter(items).most_common(n)]

    # Collect all visual elements across all scenes
    all_visual_elements = []
    all_animation_types = []
    for a in analyses:
        for scene in a.get("scenes", []):
            all_visual_elements.extend(scene.get("visual_elements", []))
            anim = scene.get("animation_type", "")
            if anim:
                all_animation_types.append(anim)

    # Build aggregated guide
    style_guide = {
        "source": "@conversion.doc",
        "videos_analyzed": len(analyses),
        "palette": {
            "background": most_common(all_bg_colors, 3),
            "text": most_common(all_text_colors, 3),
            "primary": most_common(all_primary_colors, 5),
            "accent": most_common(all_accent_colors, 5),
        },
        "typography": {
            "font_family": most_common([g.get("font_family", "") for g in all_globals], 1),
            "font_weights": sorted(set(all_font_weights)),
            "text_entrance": most_common([g.get("text_entrance", "") for g in all_globals], 3),
            "text_exit": most_common([g.get("text_exit", "") for g in all_globals], 3),
        },
        "animation": {
            "style": most_common([g.get("animation_style", "") for g in all_globals], 3),
            "spring_configs": [g.get("spring_config") for g in all_globals if g.get("spring_config")],
            "transition_type": most_common([g.get("transition_type", "") for g in all_globals], 3),
            "transition_duration_ms": [g.get("transition_duration_ms") for g in all_globals if g.get("transition_duration_ms")],
            "common_animation_types": most_common(all_animation_types, 10),
        },
        "graphics": {
            "graphic_style": most_common([g.get("graphic_style", "") for g in all_globals], 3),
            "particle_usage": [g.get("particle_usage", "") for g in all_globals if g.get("particle_usage")],
            "glow_usage": [g.get("glow_usage", "") for g in all_globals if g.get("glow_usage")],
            "common_visual_elements": most_common(
                [str(e) for e in all_visual_elements], 15
            ),
        },
        "per_video_analyses": analyses,
    }

    return style_guide


def main():
    parser = argparse.ArgumentParser(description="Batch analyze TikTok videos for style extraction")
    parser.add_argument("--videos-dir", required=True, help="Directory containing .mp4 files and metadata.json")
    parser.add_argument("--num-frames", type=int, default=10, help="Frames to extract per video")
    parser.add_argument("--top-n", type=int, default=5, help="Analyze top N videos by view count")
    parser.add_argument("--output", default=None, help="Output path for style guide JSON")

    args = parser.parse_args()

    if not OPENROUTER_API_KEY:
        print("Error: OPENROUTER_API_KEY not found in .env", file=sys.stderr)
        sys.exit(1)

    # Load metadata to get view counts
    metadata_path = os.path.join(args.videos_dir, "metadata.json")
    if os.path.exists(metadata_path):
        with open(metadata_path) as f:
            metadata = json.load(f)
        print(f"Loaded metadata for {len(metadata)} videos")
    else:
        metadata = None
        print("No metadata.json found, will analyze all .mp4 files found")

    # Find video files
    mp4_files = sorted([
        f for f in os.listdir(args.videos_dir)
        if f.endswith(".mp4")
    ])

    if not mp4_files:
        print(f"No .mp4 files found in {args.videos_dir}")
        sys.exit(1)

    print(f"Found {len(mp4_files)} video files")

    # If we have metadata, sort by views and pick top N
    if metadata:
        # Build mapping of video_id -> view count
        id_to_views = {}
        for v in metadata:
            vid = v.get("video_id") or v.get("id") or v.get("videoId", "")
            views = 0
            for key in ("playCount", "plays", "views", "viewCount"):
                val = v.get(key)
                if val is not None:
                    try:
                        views = int(val)
                        break
                    except (ValueError, TypeError):
                        pass
            stats = v.get("stats", {})
            if isinstance(stats, dict) and views == 0:
                val = stats.get("playCount") or stats.get("plays")
                if val:
                    try:
                        views = int(val)
                    except (ValueError, TypeError):
                        pass
            id_to_views[str(vid)] = views

        # Sort mp4 files by view count
        def get_file_views(filename):
            vid = filename.replace(".mp4", "")
            return id_to_views.get(vid, 0)

        mp4_files.sort(key=get_file_views, reverse=True)

    # Take top N
    selected = mp4_files[:args.top_n]
    print(f"\nAnalyzing top {len(selected)} videos:")
    for f in selected:
        vid = f.replace(".mp4", "")
        views = id_to_views.get(vid, 0) if metadata else 0
        print(f"  - {f} ({views:,} views)")

    # Analyze each video
    analyses = []
    for i, filename in enumerate(selected):
        video_path = os.path.join(args.videos_dir, filename)
        analysis = analyze_single_video(video_path, args.num_frames, i)
        if analysis:
            analyses.append(analysis)

    if not analyses:
        print("No videos were successfully analyzed.", file=sys.stderr)
        sys.exit(1)

    print(f"\nSuccessfully analyzed {len(analyses)}/{len(selected)} videos")

    # Aggregate into style guide
    print("Aggregating style guide...")
    style_guide = aggregate_style_guide(analyses)

    # Save
    output_path = args.output or os.path.join(args.videos_dir, "style_guide.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(style_guide, f, indent=2, default=str)

    print(f"\nStyle guide saved to {output_path}")
    print(f"  Videos analyzed: {style_guide.get('videos_analyzed', 0)}")
    print(f"  Palette: {json.dumps(style_guide.get('palette', {}), indent=2)}")

    return style_guide


if __name__ == "__main__":
    main()
