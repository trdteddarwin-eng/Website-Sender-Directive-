#!/usr/bin/env python3
"""
create_reference_image.py — Create a face-swapped reference image for Higgsfield.

Extracts the first frame with a face from a video, then swaps the avatar's face
into that frame using InsightFace inswapper (local, ~1-2s per image on CPU).

Falls back to Nano Banana Pro (Gemini 3 Pro Image) with --use-nano-banana flag.

This gives Higgsfield better scene context for motion control — the reference
image shows the avatar in the same setting/lighting as the original video.

Part of the TikTok Avatar Pipeline (Step 3.5):
  1. Scrape trending products (optional)
  2. Scrape + download TikTok videos
  3. Filter for talking head format
  3.5. Extract first face frame → InsightFace face swap → reference image  <-- THIS
  4. Higgsfield motion control (using swapped reference image)

Usage:
    python3 execution/create_reference_image.py \\
        --video .tmp/tiktok_downloads/video123.mp4 \\
        --avatar tiktok-avatar-pipeline/avatar.png

    # Use Nano Banana Pro instead of InsightFace:
    python3 execution/create_reference_image.py \\
        --video .tmp/tiktok_downloads/video123.mp4 \\
        --avatar tiktok-avatar-pipeline/avatar.png \\
        --use-nano-banana
"""

import os
import sys
import argparse
from datetime import datetime

import cv2
import mediapipe as mp
from dotenv import load_dotenv

load_dotenv()

# Nano Banana Pro = Gemini 3 Pro Image (codename) — fallback only
NANO_BANANA_MODEL = "gemini-3-pro-image-preview"

# InsightFace model paths
INSIGHTFACE_MODEL_DIR = os.path.expanduser("~/.insightface/models")
INSWAPPER_MODEL_PATH = os.path.join(INSIGHTFACE_MODEL_DIR, "inswapper_128.onnx")

# Singleton cache for InsightFace models (expensive to load)
_face_app = None
_swapper = None


def _get_insightface_models():
    """Load and cache InsightFace FaceAnalysis + inswapper models."""
    global _face_app, _swapper
    if _face_app is not None and _swapper is not None:
        return _face_app, _swapper

    import insightface
    from insightface.app import FaceAnalysis

    _face_app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
    _face_app.prepare(ctx_id=-1, det_size=(640, 640))

    _swapper = insightface.model_zoo.get_model(
        INSWAPPER_MODEL_PATH, providers=['CPUExecutionProvider']
    )
    return _face_app, _swapper


def extract_first_face_frame(video_path):
    """
    Extract the first frame from a video where exactly 1 face is detected.

    Uses the same MediaPipe parameters as filter_talking_head.py:
    model_selection=1, min_detection_confidence=0.5.

    Args:
        video_path: Path to the .mp4 video file.

    Returns:
        str: Path to saved frame, or None if no face found.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"  [ERROR] Could not open video: {video_path}")
        return None

    try:
        with mp.solutions.face_detection.FaceDetection(
            model_selection=1, min_detection_confidence=0.5
        ) as face_detection:
            while True:
                ret, frame = cap.read()
                if not ret or frame is None:
                    break

                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                result = face_detection.process(rgb_frame)

                if result.detections and len(result.detections) == 1:
                    # Save scene frame
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    output_dir = ".tmp/reference_images"
                    os.makedirs(output_dir, exist_ok=True)
                    frame_path = os.path.join(output_dir, f"scene_frame_{timestamp}.png")
                    cv2.imwrite(frame_path, frame)
                    print(f"  Extracted face frame: {frame_path}")
                    return frame_path
    finally:
        cap.release()

    print("  No single-face frame found in video")
    return None


def detect_gender(video_path):
    """
    Detect the gender of the person in the video using InsightFace.

    Extracts the first frame with a face and uses buffalo_l's genderage model
    to determine gender via face.sex attribute.

    Args:
        video_path: Path to the .mp4 video file.

    Returns:
        str: "M" or "F", or None if no face found.
    """
    scene_frame = extract_first_face_frame(video_path)
    if not scene_frame:
        print("  [WARN] Could not extract face frame for gender detection")
        return None

    try:
        app, _ = _get_insightface_models()
    except Exception as e:
        print(f"  [ERROR] Failed to load InsightFace models for gender detection: {e}")
        return None

    img = cv2.imread(scene_frame)
    if img is None:
        print(f"  [ERROR] Could not read scene frame: {scene_frame}")
        return None

    faces = app.get(img)
    if not faces:
        print("  [WARN] No face detected for gender detection")
        return None

    gender = "M" if faces[0].sex == "M" else "F"
    print(f"  Detected gender: {gender}")
    return gender


def face_swap_insightface(scene_frame_path, avatar_path):
    """
    Face swap using InsightFace inswapper — ~1-2s per image on CPU.

    Uses buffalo_l for face detection/analysis and inswapper_128 for the swap.
    Much faster and free compared to Nano Banana Pro (~15-20s, API cost).

    Args:
        scene_frame_path: Path to the extracted scene frame.
        avatar_path: Path to the avatar image.

    Returns:
        tuple: (swapped_image_path, detected_gender) where gender is "M"/"F"/None.
               Returns (None, None) on failure.
    """
    try:
        app, swapper = _get_insightface_models()
    except Exception as e:
        print(f"  [ERROR] Failed to load InsightFace models: {e}")
        return None, None

    scene_img = cv2.imread(scene_frame_path)
    avatar_img = cv2.imread(avatar_path)

    if scene_img is None:
        print(f"  [ERROR] Could not read scene frame: {scene_frame_path}")
        return None, None
    if avatar_img is None:
        print(f"  [ERROR] Could not read avatar image: {avatar_path}")
        return None, None

    scene_faces = app.get(scene_img)
    avatar_faces = app.get(avatar_img)

    if not scene_faces:
        print("  [ERROR] No face detected in scene frame")
        return None, None
    if not avatar_faces:
        print("  [ERROR] No face detected in avatar image")
        return None, None

    # Detect gender from scene face
    gender = None
    try:
        gender = "M" if scene_faces[0].sex == "M" else "F"
        print(f"  Detected gender from scene: {gender}")
    except AttributeError:
        print("  [WARN] Could not detect gender (sex attribute missing)")

    # Swap: put avatar face onto scene face
    result = swapper.get(scene_img, scene_faces[0], avatar_faces[0], paste_back=True)

    # Save result
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output_dir = ".tmp/reference_images"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"swapped_{timestamp}.png")
    cv2.imwrite(output_path, result)

    print(f"  Face swap complete (InsightFace): {output_path}")
    return output_path, gender


def face_swap_nano_banana(scene_frame_path, avatar_path):
    """
    Use Nano Banana Pro (Gemini 3 Pro Image) to swap the avatar face into the scene.

    Sends both images as multimodal content with a natural language face swap
    instruction. Nano Banana Pro handles the rest — no mask needed.

    Requires GOOGLE_API_KEY in environment.

    Args:
        scene_frame_path: Path to the extracted scene frame.
        avatar_path: Path to the avatar image.

    Returns:
        str: Path to the swapped image, or None on failure.
    """
    from google import genai
    from google.genai import types

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("  [ERROR] GOOGLE_API_KEY not found in .env")
        return None

    client = genai.Client(api_key=api_key)

    # Load both images
    with open(scene_frame_path, "rb") as f:
        scene_bytes = f.read()
    with open(avatar_path, "rb") as f:
        avatar_bytes = f.read()

    # Detect mime types
    scene_ext = os.path.splitext(scene_frame_path)[1].lower()
    avatar_ext = os.path.splitext(avatar_path)[1].lower()
    mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
    scene_mime = mime_map.get(scene_ext, "image/png")
    avatar_mime = mime_map.get(avatar_ext, "image/png")

    # Build multimodal content: scene frame + avatar + instruction
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(data=scene_bytes, mime_type=scene_mime),
                types.Part.from_bytes(data=avatar_bytes, mime_type=avatar_mime),
                types.Part.from_text(
                    text=(
                        "Replace the face of the person in the first image with the face "
                        "from the second image. Keep the exact same pose, body, clothing, "
                        "background, and lighting from the first image. Only change the face. "
                        "The result should be photorealistic and natural looking."
                    )
                ),
            ],
        )
    ]

    config = types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        temperature=0.8,
    )

    print(f"  Calling Nano Banana Pro ({NANO_BANANA_MODEL})...")
    image_data = None

    for chunk in client.models.generate_content_stream(
        model=NANO_BANANA_MODEL,
        contents=contents,
        config=config,
    ):
        if chunk.candidates:
            for part in chunk.candidates[0].content.parts:
                if hasattr(part, "inline_data") and part.inline_data:
                    image_data = part.inline_data.data

    if not image_data:
        print("  [ERROR] Nano Banana Pro returned no image")
        return None

    # Save result
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output_dir = ".tmp/reference_images"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"swapped_{timestamp}.png")
    with open(output_path, "wb") as f:
        f.write(image_data)

    print(f"  Face swap complete: {output_path}")
    return output_path


def create_reference_image(video_path, avatar_path, output_dir=".tmp/reference_images",
                           use_nano_banana=False):
    """
    Full pipeline: extract face frame → face swap (InsightFace or Nano Banana Pro).

    This is the main entry point called by the orchestrator pipeline.
    Falls back to None so the orchestrator can use the raw avatar.

    Args:
        video_path: Path to the source video.
        avatar_path: Path to the avatar image.
        output_dir: Where to save intermediate and final images.
        use_nano_banana: If True, use Nano Banana Pro instead of InsightFace.

    Returns:
        tuple: (swapped_image_path, detected_gender) where gender is "M"/"F"/None.
               Returns (None, None) on failure.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Step 1: Extract first face frame
    print("  Extracting first face frame...")
    scene_path = extract_first_face_frame(video_path)
    if not scene_path:
        print("  Warning: Could not extract face frame, falling back to raw avatar")
        return None, None

    # Step 2: Face swap
    if use_nano_banana:
        print("  Running Nano Banana Pro face swap...")
        try:
            swapped = face_swap_nano_banana(scene_path, avatar_path)
            return swapped, None  # Nano Banana doesn't detect gender
        except Exception as e:
            print(f"  Warning: Nano Banana Pro face swap failed ({e}), falling back to raw avatar")
            return None, None
    else:
        print("  Running InsightFace face swap (~1-2s)...")
        try:
            swapped, gender = face_swap_insightface(scene_path, avatar_path)
            return swapped, gender
        except Exception as e:
            print(f"  Warning: InsightFace face swap failed ({e}), falling back to raw avatar")
            return None, None


def main():
    parser = argparse.ArgumentParser(
        description="Create a face-swapped reference image for Higgsfield motion control.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 execution/create_reference_image.py \\
      --video .tmp/tiktok_downloads/video123.mp4 \\
      --avatar tiktok-avatar-pipeline/avatar.png

  python3 execution/create_reference_image.py \\
      --video .tmp/tiktok_downloads/video123.mp4 \\
      --avatar tiktok-avatar-pipeline/avatar.png \\
      --output-dir .tmp/reference_images
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
        "--output-dir", default=".tmp/reference_images",
        help="Output directory (default: .tmp/reference_images)",
    )
    parser.add_argument(
        "--use-nano-banana", action="store_true",
        help="Use Nano Banana Pro (Gemini) instead of InsightFace for face swap",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.video):
        print(f"Error: Video not found: {args.video}")
        sys.exit(1)

    if not os.path.isfile(args.avatar):
        print(f"Error: Avatar not found: {args.avatar}")
        sys.exit(1)

    method = "Nano Banana Pro" if args.use_nano_banana else "InsightFace (local)"
    print(f"Creating reference image...")
    print(f"  Video:  {args.video}")
    print(f"  Avatar: {args.avatar}")
    print(f"  Method: {method}")
    print()

    result, gender = create_reference_image(args.video, args.avatar, args.output_dir,
                                             use_nano_banana=args.use_nano_banana)
    if result:
        print(f"\nReference image created: {result}")
        if gender:
            print(f"Detected gender: {gender}")
    else:
        print("\nFailed to create reference image (would fall back to raw avatar in pipeline)")
        sys.exit(1)


if __name__ == "__main__":
    main()
