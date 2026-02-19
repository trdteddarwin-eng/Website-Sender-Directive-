"""
Batch optimize sequence frames for scroll canvas animation.
Resizes 3840x2160 JPGs → 1440x810 WebP (lossy, quality 82).
Drops file size ~60% and decode time ~4-5x for butter-smooth scrolling.
"""

import os
import sys
import glob

try:
    from PIL import Image
except ImportError:
    print("Pillow not installed. Installing...")
    os.system(f"{sys.executable} -m pip install Pillow")
    from PIL import Image

SEQUENCE_DIR = os.path.join(os.path.dirname(__file__), '..', 'mixsy-website', 'sequence')
INPUT_PATTERN = 'ezgif-frame-*.jpg'
OUTPUT_PREFIX = 'frame_'
TARGET_WIDTH = 1440
WEBP_QUALITY = 82


def optimize_frames():
    sequence_dir = os.path.abspath(SEQUENCE_DIR)
    input_files = sorted(glob.glob(os.path.join(sequence_dir, INPUT_PATTERN)))

    if not input_files:
        print(f"No files matching '{INPUT_PATTERN}' in {sequence_dir}")
        sys.exit(1)

    print(f"Found {len(input_files)} frames in {sequence_dir}")

    # Preview first frame dimensions
    with Image.open(input_files[0]) as sample:
        orig_w, orig_h = sample.size
        aspect = orig_h / orig_w
        target_h = round(TARGET_WIDTH * aspect)
        print(f"Original: {orig_w}x{orig_h} → Target: {TARGET_WIDTH}x{target_h}")

    converted = 0
    errors = 0

    for i, src_path in enumerate(input_files, start=1):
        num = f"{i:03d}"
        out_path = os.path.join(sequence_dir, f"{OUTPUT_PREFIX}{num}.webp")

        try:
            with Image.open(src_path) as img:
                w, h = img.size
                ar = h / w
                new_h = round(TARGET_WIDTH * ar)
                resized = img.resize((TARGET_WIDTH, new_h), Image.LANCZOS)
                resized.save(out_path, 'WEBP', quality=WEBP_QUALITY, method=4)
                converted += 1

                if i % 20 == 0 or i == len(input_files):
                    src_size = os.path.getsize(src_path) / 1024
                    out_size = os.path.getsize(out_path) / 1024
                    print(f"  [{i}/{len(input_files)}] {src_size:.0f}KB → {out_size:.0f}KB ({out_size/src_size*100:.0f}%)")
        except Exception as e:
            print(f"  ERROR on frame {i}: {e}")
            errors += 1

    print(f"\nDone: {converted} converted, {errors} errors")

    if converted == len(input_files) and errors == 0:
        print("Cleaning up old JPG files...")
        for src_path in input_files:
            os.remove(src_path)
        print(f"Deleted {len(input_files)} original JPGs")
    else:
        print("Skipping cleanup due to errors — old JPGs preserved")

    # Summary
    webp_files = sorted(glob.glob(os.path.join(sequence_dir, f"{OUTPUT_PREFIX}*.webp")))
    total_size = sum(os.path.getsize(f) for f in webp_files) / (1024 * 1024)
    print(f"\nTotal WebP sequence: {len(webp_files)} files, {total_size:.1f}MB")


if __name__ == '__main__':
    optimize_frames()
