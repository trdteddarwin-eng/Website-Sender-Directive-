#!/usr/bin/env python3
"""
vlp_ocr_menu.py — OCR the 11 Viva la Pizza menu page images using Gemini Vision.

Downloads menu images from vivalapizza.net and extracts structured menu data
(categories, items, descriptions, prices, sizes) into JSON.

Usage:
    python3 execution/vlp_ocr_menu.py
"""

import os
import sys
import json
import time
import tempfile
import urllib.request
from dotenv import load_dotenv

load_dotenv()

MENU_IMAGE_URLS = [
    f"https://vivalapizza.net/wp-content/uploads/2024/04/menu{i}-scaled.jpg"
    for i in range(1, 12)
]

VISION_MODEL = "gemini-2.0-flash"

OCR_PROMPT = """You are a menu data extractor. Analyze this restaurant menu image and extract ALL items.

Return a JSON array of categories found on this page. Each category should have:
- "category": the section/category name (e.g., "Pizzas Clásicas", "Entradas", "Bebidas")
- "items": array of menu items, each with:
  - "name": item name
  - "description": item description (if visible), or "" if none
  - "prices": object with size→price mappings. Use keys like:
    - "único" for single-price items
    - "personal", "mediana", "familiar" for pizza sizes
    - "pequeña", "grande" for two-size items
    - Or whatever size labels appear on the menu

Important:
- Extract EVERY item visible, even if partially cut off
- Prices should be numbers (not strings), e.g., 6.95 not "$6.95"
- Keep all text in Spanish as it appears on the menu
- If a category continues from a previous page, still include it with whatever items are visible
- Return ONLY the JSON array, no other text

Example output:
[
  {
    "category": "Pizzas Clásicas",
    "items": [
      {
        "name": "Margherita",
        "description": "Salsa de tomate, mozzarella, albahaca fresca",
        "prices": {"personal": 6.95, "mediana": 11.95, "familiar": 16.95}
      }
    ]
  }
]"""


def download_image(url, dest_path):
    """Download an image from a URL."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as response:
            with open(dest_path, "wb") as f:
                f.write(response.read())
        return True
    except Exception as e:
        print(f"  [WARN] Failed to download {url}: {e}")
        return False


def ocr_menu_image(client, image_path, page_num):
    """OCR a single menu image using Gemini Vision."""
    from google.genai import types

    with open(image_path, "rb") as f:
        image_data = f.read()

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(data=image_data, mime_type="image/jpeg"),
                types.Part.from_text(text=OCR_PROMPT),
            ],
        )
    ]

    config = types.GenerateContentConfig(
        temperature=0.1,  # Low temp for accurate extraction
        response_mime_type="application/json",
    )

    try:
        response = client.models.generate_content(
            model=VISION_MODEL,
            contents=contents,
            config=config,
        )

        text = response.text.strip()
        # Try to parse as JSON
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        data = json.loads(text)
        return data
    except json.JSONDecodeError as e:
        print(f"  [WARN] Page {page_num}: JSON parse error: {e}")
        print(f"  Raw response: {response.text[:500]}")
        return []
    except Exception as e:
        print(f"  [ERROR] Page {page_num}: {e}")
        return []


def merge_categories(all_pages_data):
    """Merge categories across pages, combining items from the same category."""
    merged = {}
    order = []

    for page_categories in all_pages_data:
        for cat in page_categories:
            name = cat["category"]
            if name not in merged:
                merged[name] = []
                order.append(name)
            merged[name].extend(cat.get("items", []))

    # Deduplicate items within each category (by name)
    result = []
    for name in order:
        seen = set()
        unique_items = []
        for item in merged[name]:
            item_key = item["name"].strip().lower()
            if item_key not in seen:
                seen.add(item_key)
                unique_items.append(item)
        result.append({"category": name, "items": unique_items})

    return result


def main():
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not found in .env")
        sys.exit(1)

    from google import genai
    client = genai.Client(api_key=api_key)

    os.makedirs(".tmp", exist_ok=True)

    print("=" * 60)
    print("Viva la Pizza — Menu OCR Extraction")
    print("=" * 60)
    print()

    # Download all menu images
    print("Downloading menu images...")
    image_paths = []
    with tempfile.TemporaryDirectory() as tmpdir:
        for i, url in enumerate(MENU_IMAGE_URLS):
            page_num = i + 1
            dest = os.path.join(tmpdir, f"menu{page_num}.jpg")
            print(f"  Page {page_num}/11: {url}")
            if download_image(url, dest):
                image_paths.append((page_num, dest))
            time.sleep(0.5)

        print(f"\nDownloaded {len(image_paths)}/11 images.")
        print()

        # OCR each image
        print("Running OCR on each page...")
        all_pages_data = []
        for page_num, path in image_paths:
            print(f"  Page {page_num}/11...")
            data = ocr_menu_image(client, path, page_num)
            all_pages_data.append(data)
            cats = len(data)
            items = sum(len(c.get("items", [])) for c in data)
            print(f"    → {cats} categories, {items} items")
            time.sleep(1)  # Rate limit

    # Merge across pages
    print("\nMerging categories across pages...")
    merged = merge_categories(all_pages_data)

    total_items = sum(len(c["items"]) for c in merged)
    print(f"Final: {len(merged)} categories, {total_items} items total")

    # Save results
    output_path = ".tmp/vlp_menu_ocr.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    print(f"\nSaved to {output_path}")
    print("\nCategories found:")
    for cat in merged:
        print(f"  • {cat['category']} ({len(cat['items'])} items)")


if __name__ == "__main__":
    main()
