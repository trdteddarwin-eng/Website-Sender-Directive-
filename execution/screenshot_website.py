#!/usr/bin/env python3
"""
Screenshot a website using Playwright headless Chromium.

Usage:
    python3 execution/screenshot_website.py \
        --url "https://example-hvac.com" \
        --output .tmp/acme-hvac/old-site.png \
        --viewport_width 1440 --viewport_height 900

    # For local HTML files:
    python3 execution/screenshot_website.py \
        --url "file:///path/to/index.html" \
        --output .tmp/acme-hvac/new-site.png

If the site is down or times out, generates a placeholder image.
"""

import os
import sys
import argparse
from pathlib import Path


def screenshot_website(url, output_path, viewport_width=1440, viewport_height=900, full_page=True, timeout=30000, compress=False):
    """
    Take a screenshot of a website using Playwright.

    Args:
        url: URL to screenshot (supports http/https/file://)
        output_path: Where to save the PNG
        viewport_width: Browser viewport width (default 1440)
        viewport_height: Browser viewport height (default 900)
        full_page: Capture full scrollable page (default True)
        timeout: Page load timeout in ms (default 30000)
        compress: If True, convert PNG to JPEG 85% quality (~5MB → ~400KB)

    Returns:
        output_path on success, or path to placeholder on failure
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": viewport_width, "height": viewport_height},
                device_scale_factor=2,
            )
            page = context.new_page()

            print(f"Loading: {url}")
            page.goto(url, wait_until="networkidle", timeout=timeout)

            # Wait a beat for fonts/images to finish rendering
            page.wait_for_timeout(2000)

            # Force scroll-reveal animations to show (for local spec sites)
            page.evaluate("""() => {
                // Force all animated/reveal elements visible
                document.querySelectorAll('.reveal, .animate, [data-animate], [data-aos]').forEach(el => {
                    el.classList.add('visible', 'animated', 'in-view', 'aos-animate');
                    el.style.opacity = '1';
                    el.style.transform = 'none';
                    el.style.visibility = 'visible';
                });
                // Also force any elements with opacity:0 in inline styles
                document.querySelectorAll('[style*="opacity: 0"], [style*="opacity:0"]').forEach(el => {
                    el.style.opacity = '1';
                });
            }""")
            page.wait_for_timeout(500)  # Let styles settle

            page.screenshot(path=output_path, full_page=full_page)
            browser.close()

        # Compress PNG → JPEG if requested
        if compress:
            output_path = compress_screenshot(output_path)

        print(f"Screenshot saved: {output_path}")
        return output_path

    except Exception as e:
        print(f"Screenshot failed: {e}", file=sys.stderr)
        print("Generating placeholder image...", file=sys.stderr)
        return generate_placeholder(output_path, url, viewport_width, viewport_height, str(e))


def compress_screenshot(png_path, quality=85):
    """Convert PNG to JPEG for smaller file size (~5MB → ~400KB)."""
    try:
        from PIL import Image
        img = Image.open(png_path)
        if img.mode == "RGBA":
            img = img.convert("RGB")
        jpeg_path = png_path.rsplit(".", 1)[0] + ".jpg"
        img.save(jpeg_path, "JPEG", quality=quality, optimize=True)
        size_before = os.path.getsize(png_path)
        size_after = os.path.getsize(jpeg_path)
        print(f"  Compressed: {size_before//1024}KB → {size_after//1024}KB ({jpeg_path})")
        # Replace the PNG with the JPEG path reference, keep both files
        return jpeg_path
    except ImportError:
        print("Warning: Pillow not available, skipping compression", file=sys.stderr)
        return png_path


def generate_placeholder(output_path, url, width=1440, height=900, error_msg=""):
    """
    Generate a placeholder PNG when the site can't be screenshotted.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont

        img = Image.new("RGB", (width, height), color=(245, 245, 245))
        draw = ImageDraw.Draw(img)

        # Cross-platform font detection
        import platform
        font_large = None
        font_small = None
        font_paths = []
        if platform.system() == "Darwin":
            font_paths = ["/System/Library/Fonts/Helvetica.ttc", "/System/Library/Fonts/SFNSText.ttf"]
        elif platform.system() == "Linux":
            font_paths = ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/TTF/DejaVuSans.ttf"]
        elif platform.system() == "Windows":
            font_paths = ["C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/segoeui.ttf"]

        for fp in font_paths:
            try:
                font_large = ImageFont.truetype(fp, 32)
                font_small = ImageFont.truetype(fp, 18)
                break
            except (OSError, IOError):
                continue

        if not font_large:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Draw border
        draw.rectangle([10, 10, width - 10, height - 10], outline=(200, 200, 200), width=2)

        # Draw text
        draw.text((width // 2, height // 3), "Website Unavailable", fill=(100, 100, 100), font=font_large, anchor="mm")
        draw.text((width // 2, height // 2), url[:80], fill=(150, 150, 150), font=font_small, anchor="mm")

        if error_msg:
            short_error = error_msg[:100]
            draw.text((width // 2, height // 2 + 40), short_error, fill=(180, 100, 100), font=font_small, anchor="mm")

        img.save(output_path)
        print(f"Placeholder saved: {output_path}")
        return output_path

    except ImportError:
        # If Pillow isn't available, create a minimal 1x1 PNG
        print("Warning: Pillow not available, creating minimal placeholder", file=sys.stderr)
        # Minimal valid PNG (1x1 white pixel)
        import struct
        import zlib

        def create_minimal_png(path):
            signature = b'\x89PNG\r\n\x1a\n'
            ihdr_data = struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)
            ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data)
            ihdr = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
            raw = b'\x00\xff\xff\xff'
            compressed = zlib.compress(raw)
            idat_crc = zlib.crc32(b'IDAT' + compressed)
            idat = struct.pack('>I', len(compressed)) + b'IDAT' + compressed + struct.pack('>I', idat_crc)
            iend_crc = zlib.crc32(b'IEND')
            iend = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)
            with open(path, 'wb') as f:
                f.write(signature + ihdr + idat + iend)

        create_minimal_png(output_path)
        return output_path


def main():
    parser = argparse.ArgumentParser(description="Screenshot a website using Playwright")
    parser.add_argument("--url", required=True, help="URL to screenshot (http/https/file://)")
    parser.add_argument("--output", required=True, help="Output PNG path")
    parser.add_argument("--viewport_width", type=int, default=1440, help="Viewport width (default: 1440)")
    parser.add_argument("--viewport_height", type=int, default=900, help="Viewport height (default: 900)")
    parser.add_argument("--full_page", action="store_true", default=True, help="Capture full page (default: True)")
    parser.add_argument("--no_full_page", action="store_true", help="Only capture viewport, not full page")
    parser.add_argument("--timeout", type=int, default=30000, help="Page load timeout in ms (default: 30000)")
    parser.add_argument("--compress", action="store_true", help="Compress PNG to JPEG 85%% quality")

    args = parser.parse_args()

    full_page = not args.no_full_page

    result = screenshot_website(
        url=args.url,
        output_path=args.output,
        viewport_width=args.viewport_width,
        viewport_height=args.viewport_height,
        full_page=full_page,
        timeout=args.timeout,
        compress=args.compress,
    )

    if result:
        print(f"Done: {result}")
    else:
        print("Failed to create screenshot")
        sys.exit(1)


if __name__ == "__main__":
    main()
