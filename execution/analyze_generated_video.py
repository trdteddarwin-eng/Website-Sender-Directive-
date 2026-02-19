#!/usr/bin/env python3
"""
analyze_generated_video.py — Claude Vision scene analysis for generated avatar videos.

Compares generated video frames against the original source video to detect:
- Uncanny faces / face swap artifacts
- Missing products or objects
- Wrong body position / poses
- Scene mismatches
- Visual artifacts

Uses Claude Vision (claude-sonnet-4-5-20250929) to analyze paired frames.

Part of the TikTok Avatar Pipeline (post-generation quality check):
  1. Extract key frames from both generated and source videos
  2. Send paired frames to Claude Vision for comparison
  3. Return structured analysis with pass/fail per segment
  4. Optionally build corrected prompts for re-generation

Usage:
    python3 execution/analyze_generated_video.py \
        --generated .tmp/tiktok_generated/final_video.mp4 \
        --source .tmp/tiktok_downloads/original.mp4 \
        --segments 3
"""

import os
import sys
import json
import argparse
import subprocess
import shutil
import base64
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()


def _find_ffmpeg():
    """Return path to ffmpeg binary."""
    path = shutil.which("ffmpeg")
    if path:
        return path
    candidate = os.path.join(os.path.expanduser("~"), "bin", "ffmpeg")
    if os.path.isfile(candidate):
        return candidate
    raise FileNotFoundError("ffmpeg not found. Install it: brew install ffmpeg")


def extract_key_frames(video_path, num_frames, output_dir=None):
    """
    Extract evenly-spaced key frames from a video.

    Args:
        video_path: Path to the video file.
        num_frames: Number of frames to extract.
        output_dir: Where to save frames. Auto-created if None.

    Returns:
        List of frame image paths, or empty list on failure.
    """
    if output_dir is None:
        output_dir = os.path.join(".tmp", "analysis_frames")
    os.makedirs(output_dir, exist_ok=True)

    # Get video duration
    ffmpeg = _find_ffmpeg()
    ffprobe = ffmpeg.replace("ffmpeg", "ffprobe")
    if not os.path.isfile(ffprobe):
        ffprobe = shutil.which("ffprobe") or ffprobe

    probe_cmd = [
        ffprobe, "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]
    try:
        result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=30)
        duration = float(result.stdout.strip())
    except (ValueError, subprocess.TimeoutExpired):
        print(f"  [WARN] Could not determine video duration, using 30s default")
        duration = 30.0

    # Calculate timestamps for evenly-spaced frames
    if num_frames <= 1:
        timestamps = [duration / 2]
    else:
        interval = duration / (num_frames + 1)
        timestamps = [interval * (i + 1) for i in range(num_frames)]

    base = os.path.splitext(os.path.basename(video_path))[0]
    frames = []

    for i, ts in enumerate(timestamps):
        frame_path = os.path.join(output_dir, f"{base}_frame_{i:03d}.jpg")
        cmd = [
            ffmpeg, "-y", "-ss", str(ts),
            "-i", video_path,
            "-vframes", "1",
            "-q:v", "2",
            frame_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and os.path.isfile(frame_path):
            frames.append(frame_path)
        else:
            print(f"  [WARN] Failed to extract frame at {ts:.1f}s")

    return frames


def _encode_image_base64(image_path):
    """Read an image file and return base64-encoded string."""
    with open(image_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def _get_media_type(image_path):
    """Get MIME type from file extension."""
    ext = os.path.splitext(image_path)[1].lower()
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }.get(ext, "image/jpeg")


def analyze_generated_video(generated_video, source_video, segment_count):
    """
    Compare generated vs source video frames using Claude Vision.

    Extracts key frames from both videos, sends paired frames to Claude,
    and returns structured analysis per segment.

    Args:
        generated_video: Path to the generated avatar video.
        source_video: Path to the original source video.
        segment_count: Number of segments (determines how many frames to extract).

    Returns:
        dict: {
            "segments": [
                {"index": 0, "status": "pass", "score": 85, "issues": []},
                {"index": 1, "status": "fail", "score": 30,
                 "issues": ["product missing from frame", "hand position wrong"]},
            ],
            "overall_pass": False,
            "segments_to_regenerate": [1]
        }
    """
    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("  [ERROR] ANTHROPIC_API_KEY not set in .env")
        return None

    # Extract frames — 1 per segment from each video
    num_frames = max(segment_count, 1)
    print(f"  Extracting {num_frames} key frames from each video...")

    source_frames = extract_key_frames(
        source_video, num_frames,
        os.path.join(".tmp", "analysis_frames", "source"),
    )
    generated_frames = extract_key_frames(
        generated_video, num_frames,
        os.path.join(".tmp", "analysis_frames", "generated"),
    )

    if not source_frames or not generated_frames:
        print("  [ERROR] Could not extract frames for analysis")
        return None

    # Pair up frames (use min of both lists)
    pairs = list(zip(source_frames, generated_frames))
    print(f"  Analyzing {len(pairs)} frame pair(s) with Claude Vision...")

    # Build the multimodal message
    content = []

    content.append({
        "type": "text",
        "text": (
            "You are analyzing a generated avatar video compared to its source. "
            "Below are paired frames: each pair shows the ORIGINAL (source) frame first, "
            "then the GENERATED (avatar) frame. The generated video should replicate the source "
            "with a different person's face, keeping the same pose, scene, products, and composition.\n\n"
            "For each pair, evaluate:\n"
            "1. Face quality — is the face natural or uncanny/distorted?\n"
            "2. Body match — does the body position match the source?\n"
            "3. Product/object presence — are products/objects in the source also in the generated?\n"
            "4. Scene consistency — same background, lighting, composition?\n"
            "5. Artifacts — any visual glitches, blurring, or distortion?\n\n"
            "Respond with ONLY valid JSON in this exact format:\n"
            "```json\n"
            '{"segments": [{"index": 0, "status": "pass"|"fail", "score": 0-100, '
            '"issues": ["issue1", "issue2"]}], '
            '"overall_pass": true|false, '
            '"segments_to_regenerate": [indices]}\n'
            "```\n"
            "Score guide: 80+ = pass, below 80 = fail. "
            "Be strict about uncanny faces and missing products.\n\n"
        ),
    })

    for i, (src_frame, gen_frame) in enumerate(pairs):
        content.append({
            "type": "text",
            "text": f"\n--- Segment {i} ---\nORIGINAL (source):",
        })
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": _get_media_type(src_frame),
                "data": _encode_image_base64(src_frame),
            },
        })
        content.append({
            "type": "text",
            "text": "GENERATED (avatar):",
        })
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": _get_media_type(gen_frame),
                "data": _encode_image_base64(gen_frame),
            },
        })

    # Call Claude Vision
    client = anthropic.Anthropic(api_key=api_key)

    try:
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2000,
            messages=[{"role": "user", "content": content}],
        )
    except Exception as e:
        print(f"  [ERROR] Claude Vision API call failed: {e}")
        return None

    # Parse response
    response_text = response.content[0].text if response.content else ""
    print(f"  Claude response: {response_text[:200]}...")

    # Extract JSON from response (may be wrapped in ```json ... ```)
    json_str = response_text
    if "```json" in json_str:
        json_str = json_str.split("```json")[1].split("```")[0]
    elif "```" in json_str:
        json_str = json_str.split("```")[1].split("```")[0]

    try:
        analysis = json.loads(json_str.strip())
    except json.JSONDecodeError as e:
        print(f"  [ERROR] Could not parse Claude's response as JSON: {e}")
        print(f"  Raw response: {response_text}")
        return None

    # Log results
    overall = analysis.get("overall_pass", True)
    bad_segs = analysis.get("segments_to_regenerate", [])
    print(f"  Analysis complete — overall_pass: {overall}, bad segments: {bad_segs}")

    for seg in analysis.get("segments", []):
        status = seg.get("status", "unknown")
        score = seg.get("score", 0)
        issues = seg.get("issues", [])
        print(f"    Segment {seg.get('index', '?')}: {status} (score={score}) "
              f"{'— ' + ', '.join(issues) if issues else ''}")

    return analysis


def build_fix_prompt(issues):
    """
    Build a corrected generation prompt based on identified issues.

    Takes a list of issue descriptions and constructs a prompt that
    guides the motion control model to avoid those issues.

    Args:
        issues: List of issue description strings.

    Returns:
        str: Corrected prompt for re-generation.
    """
    base_prompt = "person talking to camera, natural movement"

    if not issues:
        return base_prompt

    # Build corrective instructions
    corrections = []
    for issue in issues:
        issue_lower = issue.lower()
        if "product" in issue_lower or "object" in issue_lower or "missing" in issue_lower:
            corrections.append("ensure all visible products and objects from the scene are preserved")
        if "face" in issue_lower or "uncanny" in issue_lower or "distort" in issue_lower:
            corrections.append("natural realistic face with proper proportions")
        if "hand" in issue_lower or "position" in issue_lower or "pose" in issue_lower or "body" in issue_lower:
            corrections.append("match the exact body pose and hand positions from the reference")
        if "artifact" in issue_lower or "glitch" in issue_lower or "blur" in issue_lower:
            corrections.append("clean sharp image without visual artifacts")
        if "background" in issue_lower or "scene" in issue_lower or "lighting" in issue_lower:
            corrections.append("maintain consistent background and lighting")

    if not corrections:
        corrections.append("high quality natural looking result matching source scene")

    # Deduplicate
    corrections = list(dict.fromkeys(corrections))

    return f"{base_prompt}, {', '.join(corrections)}"


def main():
    parser = argparse.ArgumentParser(
        description="Analyze generated avatar video against source using Claude Vision.",
    )
    parser.add_argument(
        "--generated", required=True,
        help="Path to the generated avatar video (.mp4)",
    )
    parser.add_argument(
        "--source", required=True,
        help="Path to the original source video (.mp4)",
    )
    parser.add_argument(
        "--segments", type=int, default=2,
        help="Number of segments / frames to compare (default: 2)",
    )

    args = parser.parse_args()

    if not os.path.isfile(args.generated):
        print(f"Error: Generated video not found: {args.generated}")
        sys.exit(1)
    if not os.path.isfile(args.source):
        print(f"Error: Source video not found: {args.source}")
        sys.exit(1)

    print(f"Analyzing generated video...")
    print(f"  Generated: {args.generated}")
    print(f"  Source:    {args.source}")
    print(f"  Segments:  {args.segments}")
    print()

    analysis = analyze_generated_video(args.generated, args.source, args.segments)

    if analysis:
        print(f"\nAnalysis result:")
        print(json.dumps(analysis, indent=2))
    else:
        print("\nAnalysis failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
