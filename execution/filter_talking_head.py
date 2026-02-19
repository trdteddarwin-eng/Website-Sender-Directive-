#!/usr/bin/env python3
"""
filter_talking_head.py — Analyze videos for "talking head" suitability.

Part of the TikTok Avatar Pipeline. Scores video files on how well they match
the "talking head" format: single person talking to camera, minimal cuts,
good for motion control AI avatar replacement.

Uses MediaPipe face detection + OpenCV scene change detection.
Samples 1 frame per second from each video.

Usage:
    python3 execution/filter_talking_head.py --videos-dir .tmp/tiktok_downloads/ --top 3
"""

import os
import sys
import json
import argparse
import glob
from concurrent.futures import ProcessPoolExecutor, as_completed

import cv2
import numpy as np
import mediapipe as mp
from dotenv import load_dotenv

load_dotenv()


def analyze_video(video_path):
    """
    Analyze a single video file for talking head suitability.

    Samples 1 frame per second, runs face detection, checks for scene cuts,
    and computes a composite score 0-100.

    Args:
        video_path: Path to the .mp4 video file.

    Returns:
        dict with keys:
            - video_path: str
            - filename: str
            - duration: float (seconds)
            - single_face_ratio: float (0-1)
            - avg_face_size: float (face area / frame area)
            - scene_cuts: int
            - composite_score: float (0-100)
            - passed: bool
            - error: str or None
    """
    result = {
        "video_path": video_path,
        "filename": os.path.basename(video_path),
        "duration": 0.0,
        "single_face_ratio": 0.0,
        "avg_face_size": 0.0,
        "scene_cuts": 0,
        "composite_score": 0.0,
        "passed": False,
        "error": None,
    }

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        result["error"] = "Could not open video file"
        return result

    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if fps <= 0 or total_frames <= 0:
            result["error"] = "Could not read video metadata (fps or frame count is 0)"
            return result

        duration = total_frames / fps
        result["duration"] = round(duration, 2)

        # Early exit: videos outside 8-35s can never pass the filter
        if duration < 8.0 or duration > 35.0:
            result["composite_score"] = 0.0
            result["passed"] = False
            return result

        # How many frames to skip between samples (1 sample per second)
        frame_interval = int(round(fps))
        if frame_interval < 1:
            frame_interval = 1

        single_face_count = 0
        face_sizes = []
        scene_cuts = 0
        frames_sampled = 0
        prev_frame_gray = None

        with mp.solutions.face_detection.FaceDetection(
            model_selection=1, min_detection_confidence=0.5
        ) as face_detection:
            frame_index = 0

            while True:
                # Seek to the target frame
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
                ret, frame = cap.read()
                if not ret or frame is None:
                    break

                frames_sampled += 1
                frame_h, frame_w = frame.shape[:2]
                frame_area = frame_h * frame_w

                if frame_area == 0:
                    frame_index += frame_interval
                    continue

                # --- Scene cut detection ---
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                if prev_frame_gray is not None:
                    # Resize if dimensions don't match (shouldn't happen but be safe)
                    if prev_frame_gray.shape == gray.shape:
                        diff = cv2.absdiff(prev_frame_gray, gray)
                        mean_diff = np.mean(diff)
                        if mean_diff > 30:
                            scene_cuts += 1
                prev_frame_gray = gray

                # --- Face detection ---
                # MediaPipe expects RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                detection_result = face_detection.process(rgb_frame)

                num_faces = 0
                if detection_result.detections:
                    num_faces = len(detection_result.detections)

                if num_faces == 1:
                    single_face_count += 1
                    # Get bounding box — MediaPipe returns relative coords
                    bbox = detection_result.detections[0].location_data.relative_bounding_box
                    face_w = bbox.width
                    face_h = bbox.height
                    face_area_ratio = face_w * face_h
                    face_sizes.append(face_area_ratio)

                frame_index += frame_interval

        if frames_sampled == 0:
            result["error"] = "No frames could be sampled from video"
            return result

        # --- Calculate metrics ---
        single_face_ratio = single_face_count / frames_sampled
        avg_face_size = float(np.mean(face_sizes)) if face_sizes else 0.0

        result["single_face_ratio"] = round(single_face_ratio, 4)
        result["avg_face_size"] = round(avg_face_size, 4)
        result["scene_cuts"] = scene_cuts

        # --- Composite score (0-100) ---
        score = 0.0

        # 40 points: single_face_ratio (linear: 0.7 -> 0, 1.0 -> 40)
        if single_face_ratio >= 1.0:
            score += 40.0
        elif single_face_ratio >= 0.7:
            score += 40.0 * ((single_face_ratio - 0.7) / 0.3)
        # below 0.7 -> 0 points

        # 25 points: face_size in sweet spot (peak at 0.15-0.40, drops off outside)
        if avg_face_size > 0:
            if 0.15 <= avg_face_size <= 0.40:
                # Perfect sweet spot
                score += 25.0
            elif 0.05 <= avg_face_size < 0.15:
                # Ramp up from 0.05 to 0.15
                score += 25.0 * ((avg_face_size - 0.05) / 0.10)
            elif 0.40 < avg_face_size <= 0.80:
                # Ramp down from 0.40 to 0.80
                score += 25.0 * ((0.80 - avg_face_size) / 0.40)
            # outside 0.05-0.80 -> 0 points

        # 20 points: fewer scene cuts (0 -> 20, 1 -> 15, 2 -> 10, 3+ -> 0)
        if scene_cuts == 0:
            score += 20.0
        elif scene_cuts == 1:
            score += 15.0
        elif scene_cuts == 2:
            score += 10.0
        # 3+ -> 0

        # 15 points: duration in sweet spot (15-30s -> 15, 8-35s partial, outside -> 0)
        if 15.0 <= duration <= 30.0:
            score += 15.0
        elif 8.0 <= duration < 15.0:
            score += 15.0 * ((duration - 8.0) / 7.0)
        elif 30.0 < duration <= 35.0:
            score += 15.0 * ((35.0 - duration) / 5.0)
        # outside 8-35 -> 0

        result["composite_score"] = round(score, 2)

        # --- Pass/fail ---
        passed = (
            score >= 50
            and single_face_ratio >= 0.7
            and scene_cuts < 3
            and 8.0 <= duration <= 35.0
        )
        result["passed"] = passed

    except Exception as e:
        result["error"] = f"Error analyzing video: {str(e)}"
    finally:
        cap.release()

    return result


def rank_candidates(filter_results, scrape_metadata=None):
    """
    Rank candidates by combined quality + engagement score.

    Args:
        filter_results: List of analysis dicts from filter (must have 'passed' and 'composite_score').
        scrape_metadata: Optional list of scrape result dicts with engagement data.
                        Matched to filter_results by filename/video_id.

    Returns:
        List of analysis dicts sorted by final_rank (best first).
    """
    if not filter_results:
        return []

    # Build engagement lookup by video_id / filename
    engagement_map = {}
    if scrape_metadata:
        for item in scrape_metadata:
            video_id = str(item.get("id") or item.get("videoId") or item.get("video_id", ""))
            if video_id:
                plays = int(item.get("playCount", 0) or 0)
                likes = int(item.get("diggCount", 0) or item.get("likes", 0) or 0)
                shares = int(item.get("shareCount", 0) or 0)
                comments = int(item.get("commentCount", 0) or 0)
                # Weighted engagement score
                engagement_map[video_id] = plays + likes * 5 + shares * 10 + comments * 3

    # Normalize quality scores
    max_quality = max(r["composite_score"] for r in filter_results) or 1.0

    # Normalize engagement scores
    engagement_scores = []
    for r in filter_results:
        # Try to match by filename (video_id.mp4)
        fname = r.get("filename", "")
        vid_id = fname.replace(".mp4", "")
        engagement_scores.append(engagement_map.get(vid_id, 0))

    max_engagement = max(engagement_scores) if engagement_scores and max(engagement_scores) > 0 else 1.0

    # Compute final rank: 60% quality + 40% engagement
    for i, r in enumerate(filter_results):
        norm_quality = r["composite_score"] / max_quality
        norm_engagement = engagement_scores[i] / max_engagement
        r["engagement_score"] = engagement_scores[i]
        r["final_rank"] = round(0.6 * norm_quality + 0.4 * norm_engagement, 4)

    filter_results.sort(key=lambda x: x["final_rank"], reverse=True)
    return filter_results


def filter_videos(videos_dir, top_n=5, min_score=50, max_workers=4, scrape_metadata=None):
    """
    Analyze all .mp4 files in a directory in parallel, rank by quality + engagement.

    Args:
        videos_dir: Path to directory containing .mp4 files.
        top_n: Number of top candidates to return.
        min_score: Minimum composite score threshold.
        max_workers: Number of parallel analysis workers.
        scrape_metadata: Optional list of scrape result dicts for engagement ranking.

    Returns:
        Sorted list of analysis dicts for passing videos (best first).
    """
    pattern = os.path.join(videos_dir, "*.mp4")
    video_files = sorted(glob.glob(pattern))

    if not video_files:
        print(f"No .mp4 files found in {videos_dir}")
        return []

    total = len(video_files)
    print(f"Found {total} video(s) to analyze in {videos_dir} ({max_workers} workers)\n")

    results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_to_path = {
            executor.submit(analyze_video, vp): vp for vp in video_files
        }
        for future in as_completed(future_to_path):
            video_path = future_to_path[future]
            filename = os.path.basename(video_path)
            try:
                analysis = future.result()
                if analysis["error"]:
                    print(f"  {filename}: WARNING — {analysis['error']} — skipping")
                    continue
                results.append(analysis)
                status = "PASS" if analysis["passed"] else "FAIL"
                print(
                    f"  {filename}: Score {analysis['composite_score']:.1f} | "
                    f"Face {analysis['single_face_ratio']:.0%} | "
                    f"Cuts {analysis['scene_cuts']} | "
                    f"Dur {analysis['duration']:.1f}s | {status}"
                )
            except Exception as e:
                print(f"  {filename}: ERROR — {e}")

    # Filter to passing videos above min_score
    passing = [
        r for r in results
        if r["passed"] and r["composite_score"] >= min_score
    ]

    # Rank by quality + engagement
    ranked = rank_candidates(passing, scrape_metadata)

    print(f"\n{len(ranked)} videos passed (of {len(results)} analyzed)")
    return ranked[:top_n]


def print_results_table(results, all_results=None):
    """Print a formatted table of video analysis results."""
    if all_results:
        print("=" * 90)
        print("ALL RESULTS (sorted by score)")
        print("=" * 90)
        print(
            f"{'Filename':<35} {'Score':>6} {'Face%':>6} {'Size':>6} "
            f"{'Cuts':>5} {'Dur':>6} {'Status':>6}"
        )
        print("-" * 90)
        for r in all_results:
            status = "PASS" if r["passed"] else "FAIL"
            print(
                f"{r['filename']:<35} {r['composite_score']:>6.1f} "
                f"{r['single_face_ratio']:>5.0%} {r['avg_face_size']:>6.3f} "
                f"{r['scene_cuts']:>5} {r['duration']:>5.1f}s {status:>6}"
            )
        print()

    if results:
        print("=" * 90)
        print(f"TOP {len(results)} PASSING CANDIDATES")
        print("=" * 90)
        for i, r in enumerate(results, start=1):
            print(
                f"  {i}. {r['filename']} — "
                f"Score: {r['composite_score']:.1f}, "
                f"Face: {r['single_face_ratio']:.0%}, "
                f"Size: {r['avg_face_size']:.3f}, "
                f"Cuts: {r['scene_cuts']}, "
                f"Duration: {r['duration']:.1f}s"
            )
        print()
    else:
        print("No videos passed the filter criteria.\n")


def main():
    parser = argparse.ArgumentParser(
        description="Filter videos for talking head suitability."
    )
    parser.add_argument(
        "--videos-dir",
        required=True,
        help="Directory containing .mp4 files to analyze.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=5,
        help="Return top N candidates (default: 5).",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=50,
        help="Minimum composite score threshold (default: 50).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Save results JSON to this path.",
    )
    args = parser.parse_args()

    if not os.path.isdir(args.videos_dir):
        print(f"Error: Directory not found: {args.videos_dir}")
        sys.exit(1)

    # Run parallel analysis + ranking
    top_results = filter_videos(
        args.videos_dir, top_n=args.top, min_score=args.min_score
    )

    # Print table
    print_results_table(top_results)

    # Save JSON if requested
    if args.output:
        output_data = {
            "top_candidates": top_results,
            "settings": {
                "videos_dir": args.videos_dir,
                "top_n": args.top,
                "min_score": args.min_score,
            },
        }
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(output_data, f, indent=2, default=str)
        print(f"Results saved to {args.output}")

    print(f"Summary: {len(top_results)} videos passed (min score: {args.min_score})")
    return top_results


if __name__ == "__main__":
    main()
