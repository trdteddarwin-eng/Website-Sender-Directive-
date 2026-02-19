"""
Process raw product photos into clean, transparent-background PNGs.

Pipeline per image:
1. Crop to isolate a single product using proportional bounding box
2. Remove background with rembg (isnet-general-use model + alpha matting)
3. Trim excess transparent padding (keep 20px margin)
4. Resize to max 1200px on longest side (Lanczos)
5. Save as optimized PNG

Usage:
    python3 execution/process_product_images.py                    # Full pipeline
    python3 execution/process_product_images.py --preview          # Crop-only previews to .tmp/
    python3 execution/process_product_images.py --only cremas-cocoye  # Reprocess single image
"""

import argparse
import os
import sys
from PIL import Image

# ---------------------
# CROP CONFIG
# Proportional bounding boxes: (left, top, right, bottom) as fractions of image size
# ---------------------
CROP_CONFIG = {
    "cremas-cocoye": {
        "src": "cremas-cocoye.jpeg",
        "crop": (0.05, 0.02, 0.50, 0.82),
    },
    "liqueur-grenadine": {
        "src": "liqueur-grenadine.jpeg",
        "crop": (0.02, 0.02, 0.35, 0.82),
    },
    "epis-lakay": {
        "src": "epis-lakay.jpeg",
        "crop": (0.25, 0.05, 0.72, 0.80),
    },
    "bon-piman": {
        "src": "bon-piman.jpeg",
        "crop": (0.08, 0.02, 0.52, 0.88),
    },
}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_DIR = os.path.join(BASE_DIR, "mixsy-website", "images")
TMP_DIR = os.path.join(BASE_DIR, ".tmp")
MAX_SIZE = 1200
MARGIN = 20


def crop_image(img: Image.Image, crop_box: tuple) -> Image.Image:
    """Crop image using proportional bounding box."""
    w, h = img.size
    left = int(w * crop_box[0])
    top = int(h * crop_box[1])
    right = int(w * crop_box[2])
    bottom = int(h * crop_box[3])
    return img.crop((left, top, right, bottom))


def remove_bg(img: Image.Image) -> Image.Image:
    """Remove background using rembg with isnet-general-use model."""
    from rembg import remove, new_session

    session = new_session("isnet-general-use")
    result = remove(
        img,
        session=session,
        alpha_matting=True,
        alpha_matting_foreground_threshold=240,
        alpha_matting_background_threshold=10,
        alpha_matting_erode_size=10,
    )
    return result


def trim_transparent(img: Image.Image, margin: int = MARGIN) -> Image.Image:
    """Trim transparent padding, keeping a margin."""
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    # Get bounding box of non-transparent pixels
    bbox = img.getbbox()
    if bbox is None:
        return img

    # Expand by margin, clamped to image bounds
    left = max(0, bbox[0] - margin)
    top = max(0, bbox[1] - margin)
    right = min(img.width, bbox[2] + margin)
    bottom = min(img.height, bbox[3] + margin)

    return img.crop((left, top, right, bottom))


def resize_image(img: Image.Image, max_size: int = MAX_SIZE) -> Image.Image:
    """Resize to max_size on longest side, preserving aspect ratio."""
    w, h = img.size
    if max(w, h) <= max_size:
        return img

    if w > h:
        new_w = max_size
        new_h = int(h * max_size / w)
    else:
        new_h = max_size
        new_w = int(w * max_size / h)

    return img.resize((new_w, new_h), Image.LANCZOS)


def process_image(name: str, config: dict, preview_only: bool = False):
    """Process a single product image."""
    src_path = os.path.join(IMAGES_DIR, config["src"])
    if not os.path.exists(src_path):
        print(f"  ERROR: Source not found: {src_path}")
        return False

    print(f"  Loading {config['src']} ...", end=" ", flush=True)
    img = Image.open(src_path).convert("RGB")
    print(f"{img.size[0]}x{img.size[1]}")

    # Step 1: Crop
    print(f"  Cropping with box {config['crop']} ...", end=" ", flush=True)
    cropped = crop_image(img, config["crop"])
    print(f"{cropped.size[0]}x{cropped.size[1]}")

    if preview_only:
        os.makedirs(TMP_DIR, exist_ok=True)
        preview_path = os.path.join(TMP_DIR, f"{name}_preview.png")
        cropped.save(preview_path)
        print(f"  Preview saved: {preview_path}")
        return True

    # Step 2: Remove background
    print("  Removing background (this may take a moment) ...", flush=True)
    nobg = remove_bg(cropped)
    print(f"  Background removed. Mode: {nobg.mode}")

    # Step 3: Trim transparent padding
    print("  Trimming transparent padding ...", end=" ", flush=True)
    trimmed = trim_transparent(nobg)
    print(f"{trimmed.size[0]}x{trimmed.size[1]}")

    # Step 4: Resize
    print(f"  Resizing to max {MAX_SIZE}px ...", end=" ", flush=True)
    resized = resize_image(trimmed)
    print(f"{resized.size[0]}x{resized.size[1]}")

    # Step 5: Save
    out_path = os.path.join(IMAGES_DIR, f"{name}.png")
    resized.save(out_path, "PNG", optimize=True)
    file_size_kb = os.path.getsize(out_path) / 1024
    print(f"  Saved: {out_path} ({file_size_kb:.0f} KB)")
    return True


def main():
    parser = argparse.ArgumentParser(description="Process product images for House of Miyou")
    parser.add_argument("--preview", action="store_true", help="Save crop previews only (no bg removal)")
    parser.add_argument("--only", type=str, help="Process only this image (e.g. cremas-cocoye)")
    args = parser.parse_args()

    if args.only:
        if args.only not in CROP_CONFIG:
            print(f"Unknown image: {args.only}")
            print(f"Available: {', '.join(CROP_CONFIG.keys())}")
            sys.exit(1)
        targets = {args.only: CROP_CONFIG[args.only]}
    else:
        targets = CROP_CONFIG

    mode = "PREVIEW" if args.preview else "FULL PIPELINE"
    print(f"\n{'='*50}")
    print(f"House of Miyou - Image Processing ({mode})")
    print(f"{'='*50}\n")

    success = 0
    for name, config in targets.items():
        print(f"[{name}]")
        if process_image(name, config, preview_only=args.preview):
            success += 1
        print()

    print(f"Done: {success}/{len(targets)} images processed successfully.")


if __name__ == "__main__":
    main()
