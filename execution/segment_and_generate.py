#!/usr/bin/env python3
"""
segment_and_generate.py — Full-length avatar video generation.

Splits a source video into segments, face-swaps each segment's first frame
using InsightFace, generates all segments via Kling 3.0 Pro in parallel,
then stitches and overlays original audio.

Produces a full-length avatar video matching the source video duration.

Usage:
    python3 execution/segment_and_generate.py \
        --video .tmp/tiktok_downloads/best_video.mp4 \
        --avatar tiktok-avatar-pipeline/avatar.png \
        --segment-duration 10
"""

import os
import sys
import argparse
import subprocess
import shutil
import tempfile
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Ensure ffmpeg is findable (may be in ~/bin)
_home_bin = os.path.join(os.path.expanduser("~"), "bin")
if os.path.isdir(_home_bin) and _home_bin not in os.environ.get("PATH", ""):
    os.environ["PATH"] = _home_bin + ":" + os.environ.get("PATH", "")


def _find_ffmpeg():
    """Return path to ffmpeg binary, or raise if not found."""
    path = shutil.which("ffmpeg")
    if path:
        return path
    # Check ~/bin explicitly
    candidate = os.path.join(os.path.expanduser("~"), "bin", "ffmpeg")
    if os.path.isfile(candidate):
        return candidate
    raise FileNotFoundError(
        "ffmpeg not found. Install it: brew install ffmpeg"
    )

from create_reference_image import face_swap_insightface, extract_first_face_frame, detect_gender
from higgsfield_motion_control import run_motion_control


def split_video(video_path, segment_duration=10, output_dir=None):
    """
    Split a video into segments of segment_duration seconds using ffmpeg.

    Args:
        video_path: Path to source video.
        segment_duration: Duration of each segment in seconds.
        output_dir: Where to save segments. Auto-created if None.

    Returns:
        Ordered list of segment file paths, or empty list on failure.
    """
    if output_dir is None:
        output_dir = os.path.join(".tmp", "segments")
    os.makedirs(output_dir, exist_ok=True)

    # Clean prefix for this video — remove stale segments from prior runs
    base = os.path.splitext(os.path.basename(video_path))[0]
    for f in os.listdir(output_dir):
        if f.startswith(f"{base}_seg_") and f.endswith(".mp4"):
            os.remove(os.path.join(output_dir, f))

    pattern = os.path.join(output_dir, f"{base}_seg_%03d.mp4")

    ffmpeg = _find_ffmpeg()
    cmd = [
        ffmpeg, "-y", "-i", video_path,
        "-f", "segment",
        "-segment_time", str(segment_duration),
        "-c", "copy",
        "-reset_timestamps", "1",
        pattern,
    ]

    print(f"  Splitting video into {segment_duration}s segments...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        print(f"  [ERROR] ffmpeg split failed: {result.stderr}", file=sys.stderr)
        return []

    # Collect generated segments in order
    segments = sorted([
        os.path.join(output_dir, f)
        for f in os.listdir(output_dir)
        if f.startswith(f"{base}_seg_") and f.endswith(".mp4")
    ])

    print(f"  Split into {len(segments)} segment(s)")
    return segments


def _extract_and_swap_single(segment_path, avatar_path):
    """Extract first face frame from a segment and face-swap it. For parallel use."""
    # Extract first frame with a face
    scene_frame = extract_first_face_frame(segment_path)
    if not scene_frame:
        print(f"  [WARN] No face frame in {os.path.basename(segment_path)}, using avatar directly")
        return (segment_path, None)

    # Face swap with InsightFace (now returns tuple)
    swapped, _gender = face_swap_insightface(scene_frame, avatar_path)
    if not swapped:
        print(f"  [WARN] Face swap failed for {os.path.basename(segment_path)}, using avatar directly")
        return (segment_path, None)

    return (segment_path, swapped)


def face_swap_all_segments(segment_paths, avatar_path, max_workers=3):
    """
    Face-swap the first frame of each segment in parallel.

    Args:
        segment_paths: Ordered list of segment video paths.
        avatar_path: Path to avatar image.
        max_workers: Number of parallel swap workers.

    Returns:
        List of (segment_path, reference_image_path) tuples.
        reference_image_path may be None if swap failed (fallback to raw avatar).
    """
    print(f"\n  Face-swapping {len(segment_paths)} segments ({max_workers} workers)...")

    results = [None] * len(segment_paths)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_idx = {
            executor.submit(_extract_and_swap_single, seg, avatar_path): i
            for i, seg in enumerate(segment_paths)
        }
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                results[idx] = future.result()
            except Exception as e:
                print(f"  [ERROR] Swap failed for segment {idx}: {e}")
                results[idx] = (segment_paths[idx], None)

    swapped_count = sum(1 for _, ref in results if ref is not None)
    print(f"  Face swap complete: {swapped_count}/{len(segment_paths)} segments swapped")
    return results


def _generate_single_segment(segment_path, ref_image_path, avatar_path, output_dir,
                              segment_index, duration):
    """Generate a single segment via Kling. For parallel use."""
    # Use face-swapped reference if available, else raw avatar
    avatar_for_gen = ref_image_path or avatar_path

    seg_output_dir = os.path.join(output_dir, f"seg_{segment_index:03d}")
    os.makedirs(seg_output_dir, exist_ok=True)

    print(f"  Generating segment {segment_index} via Kling (duration={duration}s)...")
    result = run_motion_control(
        video_path=segment_path,
        avatar_path=avatar_for_gen,
        output_dir=seg_output_dir,
        timeout=600,
        poll_interval=10,
        duration=duration,
    )
    return (segment_index, result)


def generate_all_segments(segment_ref_pairs, avatar_path, output_dir,
                          max_workers=6, duration=10):
    """
    Generate all video segments via Kling 3.0 in parallel.

    Args:
        segment_ref_pairs: List of (segment_path, reference_image_path) tuples.
        avatar_path: Path to raw avatar (fallback if reference is None).
        output_dir: Directory for generated segment outputs.
        max_workers: Number of parallel Kling generations.
        duration: Duration per generated segment in seconds.

    Returns:
        Ordered list of generated segment paths (None for failed segments).
    """
    n = len(segment_ref_pairs)
    print(f"\n  Generating {n} segments via Kling 3.0 Pro ({max_workers} parallel)...")

    results = [None] * n
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for i, (seg_path, ref_path) in enumerate(segment_ref_pairs):
            future = executor.submit(
                _generate_single_segment, seg_path, ref_path, avatar_path,
                output_dir, i, duration
            )
            futures[future] = i

        for future in as_completed(futures):
            idx = futures[future]
            try:
                seg_idx, gen_path = future.result()
                results[seg_idx] = gen_path
                if gen_path:
                    print(f"  Segment {seg_idx} generated: {gen_path}")
                else:
                    print(f"  Segment {seg_idx} FAILED", file=sys.stderr)
            except Exception as e:
                print(f"  Segment {idx} ERROR: {e}", file=sys.stderr)

    success_count = sum(1 for r in results if r is not None)
    print(f"  Generation complete: {success_count}/{n} segments succeeded")
    return results


def stitch_and_add_audio(generated_segments, source_video_path, output_path):
    """
    Stitch generated segments together and overlay original audio.

    Args:
        generated_segments: Ordered list of generated segment paths.
        source_video_path: Original source video (for audio extraction).
        output_path: Where to save the final video.

    Returns:
        str: Path to final video, or None on failure.
    """
    # Filter out None entries (failed segments)
    valid_segments = [(i, p) for i, p in enumerate(generated_segments) if p is not None]
    if not valid_segments:
        print("  [ERROR] No generated segments to stitch", file=sys.stderr)
        return None

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    # Step 1: Create concat file for ffmpeg
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, prefix='concat_') as f:
        for _, seg_path in valid_segments:
            f.write(f"file '{os.path.abspath(seg_path)}'\n")
        concat_file = f.name

    try:
        # Step 2: Stitch segments (video only)
        ffmpeg = _find_ffmpeg()
        stitched_tmp = output_path + ".stitched.mp4"
        stitch_cmd = [
            ffmpeg, "-y", "-f", "concat", "-safe", "0",
            "-i", concat_file,
            "-c", "copy",
            stitched_tmp,
        ]
        print(f"  Stitching {len(valid_segments)} segments...")
        result = subprocess.run(stitch_cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            print(f"  [ERROR] Stitch failed: {result.stderr}", file=sys.stderr)
            return None

        # Step 3: Extract audio from source and merge with stitched video
        print(f"  Overlaying original audio...")
        merge_cmd = [
            ffmpeg, "-y",
            "-i", stitched_tmp,
            "-i", source_video_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            output_path,
        ]
        result = subprocess.run(merge_cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            # If source has no audio, just use stitched video
            print(f"  [WARN] Audio merge failed (source may have no audio), using video only")
            os.rename(stitched_tmp, output_path)
        else:
            # Clean up stitched tmp
            if os.path.exists(stitched_tmp):
                os.remove(stitched_tmp)

        print(f"  Final video: {output_path}")
        return output_path

    finally:
        # Clean up concat file
        if os.path.exists(concat_file):
            os.remove(concat_file)


def generate_full_video(source_video_path, avatar_path, output_dir=".tmp/tiktok_generated",
                        segment_duration=10, max_kling_workers=6, max_swap_workers=3,
                        avatar_male_path=None, avatar_female_path=None,
                        enable_analysis=False):
    """
    Main orchestrator: detect gender → split → swap → generate → stitch + audio → analyze → fix.

    Args:
        source_video_path: Path to the source TikTok video.
        avatar_path: Path to the avatar image (fallback if no gendered avatars).
        output_dir: Where to save outputs.
        segment_duration: How long each segment should be (seconds).
        max_kling_workers: Max parallel Kling generation workers.
        max_swap_workers: Max parallel InsightFace swap workers.
        avatar_male_path: Path to male avatar (used if source person is male).
        avatar_female_path: Path to female avatar (used if source person is female).
        enable_analysis: If True, run Claude Vision analysis + auto-fix after generation.

    Returns:
        str: Path to final full-length video, or None on failure.
    """
    os.makedirs(output_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(source_video_path))[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Step 0: Gender detection & avatar selection
    selected_avatar = avatar_path  # default fallback
    if avatar_male_path and avatar_female_path:
        print(f"\n[0/5] Detecting gender for avatar selection...")
        gender = detect_gender(source_video_path)
        if gender == "F":
            selected_avatar = avatar_female_path
            print(f"  Selected FEMALE avatar: {avatar_female_path}")
        elif gender == "M":
            selected_avatar = avatar_male_path
            print(f"  Selected MALE avatar: {avatar_male_path}")
        else:
            print(f"  Gender detection failed, using default avatar: {avatar_path}")
    else:
        gender = None

    print(f"\n{'='*60}")
    print(f"Full-Length Video Generation")
    print(f"  Source:   {source_video_path}")
    print(f"  Avatar:   {selected_avatar}" + (f" (auto-selected: {gender})" if gender else ""))
    print(f"  Segment:  {segment_duration}s")
    print(f"  Analysis: {'enabled' if enable_analysis else 'disabled'}")
    print(f"{'='*60}")

    # Step 1: Split video into segments
    print(f"\n[1/5] Splitting video...")
    segments_dir = os.path.join(output_dir, "segments", base)
    segments = split_video(source_video_path, segment_duration, segments_dir)
    if not segments:
        print("[ERROR] Failed to split video", file=sys.stderr)
        return None

    # Step 2: Face-swap first frame of each segment (parallel)
    print(f"\n[2/5] Face-swapping segment frames...")
    segment_ref_pairs = face_swap_all_segments(segments, selected_avatar, max_swap_workers)

    # Step 3: Generate all segments via Kling (parallel)
    print(f"\n[3/5] Generating segments via Kling 3.0 Pro...")
    gen_dir = os.path.join(output_dir, "generated", base)
    generated = generate_all_segments(
        segment_ref_pairs, selected_avatar, gen_dir,
        max_workers=max_kling_workers, duration=segment_duration,
    )

    # Step 4: Stitch + audio
    print(f"\n[4/5] Stitching and adding audio...")
    final_path = os.path.join(output_dir, f"final_{base}_{timestamp}.mp4")
    result = stitch_and_add_audio(generated, source_video_path, final_path)

    if not result:
        print(f"\n[ERROR] Failed to produce final video", file=sys.stderr)
        return None

    # Step 5: Analyze + auto-fix (if enabled)
    if enable_analysis:
        print(f"\n[5/5] Analyzing generated video with Claude Vision...")
        try:
            from analyze_generated_video import analyze_generated_video, build_fix_prompt

            analysis = analyze_generated_video(result, source_video_path, len(segments))

            if analysis and not analysis.get("overall_pass", True):
                bad_segments = analysis.get("segments_to_regenerate", [])
                print(f"  Analysis found {len(bad_segments)} segment(s) to fix: {bad_segments}")

                result = fix_bad_segments(
                    analysis=analysis,
                    segments=segments,
                    generated_segments=generated,
                    selected_avatar=selected_avatar,
                    source_video_path=source_video_path,
                    output_dir=output_dir,
                    gen_dir=gen_dir,
                    base=base,
                    timestamp=timestamp,
                    segment_duration=segment_duration,
                )
            else:
                print(f"  Analysis passed — all segments look good!")
        except ImportError:
            print(f"  [WARN] analyze_generated_video not available, skipping analysis")
        except Exception as e:
            print(f"  [WARN] Analysis failed ({e}), keeping first-pass video")
    else:
        print(f"\n[5/5] Analysis skipped (use --enable-analysis to enable)")

    if result:
        print(f"\nFull-length video generated: {result}")
    else:
        print(f"\n[ERROR] Failed to produce final video", file=sys.stderr)

    return result


def fix_bad_segments(analysis, segments, generated_segments, selected_avatar,
                     source_video_path, output_dir, gen_dir, base, timestamp,
                     segment_duration=10, max_retries=1):
    """
    Re-generate segments that Claude Vision flagged as bad.

    Args:
        analysis: Analysis dict from analyze_generated_video().
        segments: List of original segment video paths.
        generated_segments: List of generated segment paths.
        selected_avatar: Path to the selected avatar image.
        source_video_path: Path to the original source video.
        output_dir: Output directory.
        gen_dir: Generation directory for segments.
        base: Base name of the video.
        timestamp: Timestamp string for output naming.
        segment_duration: Duration per segment.
        max_retries: Max re-generation attempts per segment (default 1).

    Returns:
        str: Path to the re-stitched final video, or None on failure.
    """
    from analyze_generated_video import build_fix_prompt

    bad_indices = analysis.get("segments_to_regenerate", [])
    if not bad_indices:
        return None

    fixed_segments = list(generated_segments)  # copy

    for seg_idx in bad_indices:
        if seg_idx >= len(segments):
            print(f"  [WARN] Segment index {seg_idx} out of range, skipping")
            continue

        # Build a corrected prompt from the analysis
        seg_analysis = None
        for s in analysis.get("segments", []):
            if s.get("index") == seg_idx:
                seg_analysis = s
                break

        if not seg_analysis:
            continue

        issues = seg_analysis.get("issues", [])
        fix_prompt = build_fix_prompt(issues)
        print(f"  Re-generating segment {seg_idx} with prompt: {fix_prompt[:80]}...")

        # Face-swap for this segment
        scene_frame = extract_first_face_frame(segments[seg_idx])
        if scene_frame:
            swapped, _ = face_swap_insightface(scene_frame, selected_avatar)
            avatar_for_gen = swapped or selected_avatar
        else:
            avatar_for_gen = selected_avatar

        seg_output_dir = os.path.join(gen_dir, f"seg_{seg_idx:03d}_fix")
        os.makedirs(seg_output_dir, exist_ok=True)

        new_result = run_motion_control(
            video_path=segments[seg_idx],
            avatar_path=avatar_for_gen,
            output_dir=seg_output_dir,
            timeout=600,
            poll_interval=10,
            duration=segment_duration,
            prompt=fix_prompt,
        )

        if new_result:
            fixed_segments[seg_idx] = new_result
            print(f"  Segment {seg_idx} re-generated: {new_result}")
        else:
            print(f"  [WARN] Re-generation failed for segment {seg_idx}, keeping original")

    # Re-stitch with fixed segments
    print(f"  Re-stitching with fixed segments...")
    fixed_path = os.path.join(output_dir, f"final_{base}_{timestamp}_fixed.mp4")
    result = stitch_and_add_audio(fixed_segments, source_video_path, fixed_path)
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Generate full-length avatar video from source video.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 execution/segment_and_generate.py \\
      --video .tmp/tiktok_downloads/best_video.mp4 \\
      --avatar tiktok-avatar-pipeline/avatar.png

  python3 execution/segment_and_generate.py \\
      --video .tmp/tiktok_downloads/best_video.mp4 \\
      --avatar tiktok-avatar-pipeline/avatar.png \\
      --segment-duration 10 --max-kling-workers 3
        """,
    )
    parser.add_argument(
        "--video", required=True,
        help="Path to the source video (.mp4)",
    )
    parser.add_argument(
        "--avatar", required=True,
        help="Path to the avatar image (.png/.jpg)",
    )
    parser.add_argument(
        "--output-dir", default=".tmp/tiktok_generated",
        help="Output directory (default: .tmp/tiktok_generated)",
    )
    parser.add_argument(
        "--segment-duration", type=int, default=10,
        help="Duration of each segment in seconds (default: 10)",
    )
    parser.add_argument(
        "--max-kling-workers", type=int, default=6,
        help="Max parallel Kling generation workers (default: 6)",
    )
    parser.add_argument(
        "--max-swap-workers", type=int, default=3,
        help="Max parallel InsightFace swap workers (default: 3)",
    )
    parser.add_argument(
        "--avatar-male",
        help="Path to male avatar image (auto-selected when source person is male)",
    )
    parser.add_argument(
        "--avatar-female",
        help="Path to female avatar image (auto-selected when source person is female)",
    )
    parser.add_argument(
        "--enable-analysis", action="store_true",
        help="Enable Claude Vision analysis + auto-fix after generation",
    )

    args = parser.parse_args()

    if not os.path.isfile(args.video):
        print(f"Error: Video not found: {args.video}")
        sys.exit(1)

    if not os.path.isfile(args.avatar):
        print(f"Error: Avatar not found: {args.avatar}")
        sys.exit(1)

    result = generate_full_video(
        source_video_path=args.video,
        avatar_path=args.avatar,
        output_dir=args.output_dir,
        segment_duration=args.segment_duration,
        max_kling_workers=args.max_kling_workers,
        max_swap_workers=args.max_swap_workers,
        avatar_male_path=getattr(args, 'avatar_male', None),
        avatar_female_path=getattr(args, 'avatar_female', None),
        enable_analysis=args.enable_analysis,
    )

    if result:
        print(f"\nSuccess: {result}")
    else:
        print("\nFailed to generate full-length video.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
