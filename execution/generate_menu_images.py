#!/usr/bin/env python3
"""
generate_menu_images.py — Generate food images for Viva la Pizza menu using Nano Banana Pro.

Uses Gemini 3 Pro Image to create photorealistic food photography for each menu item.
Images are saved as WebP to viva-la-pizza/public/images/menu/{item-id}.webp

Usage:
    python3 execution/generate_menu_images.py
    python3 execution/generate_menu_images.py --start-from 20   # resume from item #20
    python3 execution/generate_menu_images.py --only margarita  # generate one specific item
"""

import os
import sys
import time
import json
import argparse
import subprocess
from dotenv import load_dotenv

load_dotenv()

NANO_BANANA_MODEL = "gemini-3-pro-image-preview"
OUTPUT_DIR = "viva-la-pizza/public/images/menu"

STYLE_PREFIX = (
    "Professional editorial food photography. "
    "Shot from a 45-degree overhead angle on a dark rustic wood table surface. "
    "Warm natural side lighting from the left, soft shadows. "
    "Shallow depth of field, creamy bokeh background. "
    "The dish is plated beautifully on a white ceramic plate. "
    "No text, no logos, no watermarks. "
    "Photorealistic, appetizing, high-end restaurant quality. "
)

# All menu items with tailored prompts
MENU_ITEMS = [
    # ─── ENTRADAS ───
    {"id": "bruschetta-viva-la-pizza", "prompt": "Artisan bruschetta on sourdough bread topped with cherry tomatoes, roasted garlic, creamy stracciatella cheese, fresh basil leaves, and a drizzle of olive oil."},
    {"id": "volcan-de-ricotta", "prompt": "A mound of whipped truffle ricotta cheese drizzled with hot honey, served with rustic focaccia bread slices on the side."},
    {"id": "carpaccio-de-res", "prompt": "Thinly sliced raw beef carpaccio arranged in a circle, topped with arugula, basil pesto, almond flakes, shaved parmesan, and balsamic glaze."},
    {"id": "carpaccio-de-salmon", "prompt": "Thinly sliced smoked salmon carpaccio with honey-lemon dressing, capers, black olives, and fresh arugula on a white plate."},
    {"id": "mozzarella-fingers", "prompt": "Golden crispy fried mozzarella sticks, breaded and fried, served with a small bowl of smoky tomato dipping sauce."},
    {"id": "focaccia-paradiso", "prompt": "Artisan focaccia bread topped with prosciutto, stracciatella cheese, fresh arugula, pesto sauce, olive oil, and balsamic glaze."},
    {"id": "focaccia-tradicional", "prompt": "Simple Italian focaccia bread with grated parmesan cheese, oregano, and olive oil, golden and crusty."},
    {"id": "cazuela-de-queso-fundido", "prompt": "A small cast iron skillet with bubbling melted provolone and mozzarella cheese with crispy chistorra sausage, served with focaccia bread."},

    # ─── ENSALADAS ───
    {"id": "ensalada-caprese", "prompt": "Classic caprese salad with cubed fresh tomatoes, mozzarella cheese, fresh basil, pesto sauce, and balsamic glaze."},
    {"id": "burrata-bowl", "prompt": "A large creamy burrata cheese on a bed of arugula, prosciutto, cherry tomatoes, and shaved parmesan, with focaccia on the side."},
    {"id": "ensalada-cesar", "prompt": "Caesar salad with romaine lettuce, crispy bacon bits, parmesan shavings, sourdough croutons, and creamy caesar dressing."},

    # ─── PIZZAS CLÁSICAS ───
    {"id": "margarita", "prompt": "Classic Margherita pizza with tomato sauce, fresh mozzarella, and fresh basil leaves. Perfectly charred crust from a wood-fired oven."},
    {"id": "pepperoni", "prompt": "Pepperoni pizza with mozzarella cheese and premium cup-and-char pepperoni slices. Perfectly charred thin crust."},
    {"id": "jamon", "prompt": "Ham pizza with mozzarella cheese and sliced ham. Italian-style thin crust pizza from a wood-fired oven."},
    {"id": "funghi-especial", "prompt": "Mushroom pizza with mozzarella and sautéed garlic mushrooms. Thin crust, wood-fired, aromatic."},
    {"id": "hawaiana", "prompt": "Hawaiian pizza with mozzarella, ham, fresh pineapple chunks, and a drizzle of honey. Thin crust."},
    {"id": "jamon-y-hongos", "prompt": "Pizza with mozzarella, sliced ham, and mushrooms on a thin Italian-style crust."},

    # ─── PIZZAS PREMIUM HITS ───
    {"id": "viva-la-pizza", "prompt": "Artisan pizza with mozzarella, pepperoni, mushrooms, and a shot glass of hot honey on the side. Thin charred crust."},
    {"id": "the-queen", "prompt": "Premium pizza with mozzarella, premium cup-and-char Ezzo pepperoni, creamy stracciatella, hot honey drizzle, fresh basil, and parmesan shavings."},
    {"id": "mortal-dela", "prompt": "Gourmet pizza topped with mortadella slices, creamy stracciatella, almonds, and pistachio cream drizzle. Italian artisan style."},
    {"id": "tsunami", "prompt": "Fusion sushi pizza with mozzarella, smoked salmon, kani (crab stick), avocado slices, dynamite sauce, and eel sauce drizzle."},
    {"id": "mafiosa", "prompt": "Loaded meat pizza with mozzarella, pepperoni, chorizo, crispy bacon, and a drizzle of secret sauce. Dark and dramatic plating."},
    {"id": "chistorra-4-quesos", "prompt": "Four cheese pizza with crispy chistorra sausage, mozzarella, provolone, pecorino, and parmesan. Bubbling and golden."},
    {"id": "san-francisco", "prompt": "Pizza with mozzarella, pepperoni, bacon, sliced onions, and a shot of basil pesto sauce. Rustic Italian style."},
    {"id": "smoked-salmon", "prompt": "Elegant pizza topped with mozzarella, smoked salmon, fresh arugula, and capers. Light and sophisticated."},
    {"id": "fabi-fabi", "prompt": "Pizza with mozzarella, prosciutto, fresh arugula, and crumbled goat cheese. Elegant Italian style."},
    {"id": "3-carnes", "prompt": "Three-meat pizza with mozzarella, ham, chorizo, pepperoni, and cream cheese. Hearty and loaded."},
    {"id": "trufa-lover", "prompt": "Truffle pizza with mozzarella, provolone, sautéed mushrooms, and white truffle oil drizzle. Earthy and elegant."},
    {"id": "esto-es-pesto", "prompt": "Pesto pizza with mozzarella, diced tomatoes, parmesan, and a generous shot of fresh basil pesto. Vibrant green."},
    {"id": "jamon-bacon-maiz", "prompt": "Pizza with mozzarella, ham, crispy bacon, and sweet corn kernels. Comfort food style."},
    {"id": "combinacion", "prompt": "Loaded combination pizza with mozzarella, ham, mushrooms, pepperoni, bell peppers, onions, and black olives."},
    {"id": "bacon-pollo", "prompt": "Chicken and bacon pizza with mozzarella, grilled chicken pieces, crispy bacon, and melted cheddar cheese."},
    {"id": "sweet-summer", "prompt": "Pizza with mozzarella, caramelized onions, crispy bacon, and swirls of cream cheese. Sweet and savory."},
    {"id": "veggie-al-ajillo", "prompt": "Vegetarian pizza with mozzarella, garlic mushrooms, black olives, and roasted bell peppers. Colorful and fresh."},
    {"id": "pulled-pork", "prompt": "BBQ pulled pork pizza with mozzarella, slow-cooked pulled pork in BBQ sauce, bacon, onions, and melted cheddar."},

    # ─── PIZZAS CON BURRATA ───
    {"id": "serrano-burrata", "prompt": "Pizza topped with mozzarella, prosciutto, arugula, cherry tomatoes, and a whole creamy burrata cheese in the center with pesto drizzle."},
    {"id": "pep-burrata", "prompt": "Pizza with mozzarella, premium cup-and-char pepperoni, fresh basil, and a whole burrata with pesto and parmesan in the center."},
    {"id": "mushroom-burrata", "prompt": "Pizza with mozzarella, garlic sautéed mushrooms, and a whole creamy burrata cheese topped with pesto and parmesan."},
    {"id": "tomato-burrata", "prompt": "Pizza with mozzarella, marinated diced tomatoes, fresh basil, and a whole creamy burrata cheese with pesto drizzle."},

    # ─── PASTAS ───
    {"id": "king-bolognesa", "prompt": "A plate of spaghetti with rich meat bolognese sauce (pomodoro with ground beef). Classic Italian comfort food."},
    {"id": "queen-carbonara", "prompt": "Creamy carbonara pasta with pecorino, egg, cracked black pepper, and crispy bacon. Traditional Roman style."},
    {"id": "al-pesto", "prompt": "Pasta with vibrant green basil pesto sauce and shaved parmesan cheese. Fresh and aromatic."},
    {"id": "fileto-burrata", "prompt": "Pasta in filetto di pomodoro sauce crowned with a whole creamy burrata cheese, fresh basil, and white truffle oil."},
    {"id": "lulilu", "prompt": "Pasta in caramelized onion cream sauce with prosciutto and crispy bacon. Rich and savory."},
    {"id": "don-alfredo", "prompt": "Classic fettuccine alfredo pasta with parmesan, butter, ham slices, and fresh parsley."},
    {"id": "ravioli-de-carne", "prompt": "Meat-filled ravioli in bolognese sauce, topped with melted gratinated mozzarella cheese. Italian comfort food."},
    {"id": "ravioli-de-hongos-porcini", "prompt": "Porcini mushroom ravioli with sautéed wild mushrooms in a red wine reduction sauce. Earthy and elegant."},
    {"id": "ravioli-vlp", "prompt": "Four-cheese ravioli in pomodoro sauce with bechamel and prosciutto. Creamy and indulgent."},
    {"id": "3-salsas", "prompt": "A plate of pasta divided into three sections: bolognese sauce, basil pesto sauce, and filetto di pomodoro sauce. Colorful trio."},

    # ─── SPECIAL DISHES ───
    {"id": "lasana-aka-el-pasticho-de-rafa", "prompt": "A generous portion of lasagna with layers of pasta, bolognese sauce, bechamel, and gratinated mozzarella. Served with garlic bread."},
    {"id": "la-intrusa", "prompt": "A gourmet burger with a thick angus beef patty, double cheddar, mozzarella, crispy bacon, caramelized onions, arugula, and truffle mayo. Served with french fries."},
    {"id": "crispy-chicken-parm", "prompt": "Crispy breaded chicken fillet topped with pomodoro sauce, melted mozzarella and parmesan, served alongside spaghetti."},
    {"id": "steak-and-fries", "prompt": "A perfectly seared beef steak (270g) with a golden crust, served with french fries and a small bowl of garlic aioli."},
    {"id": "honey-salmon", "prompt": "Pan-seared salmon fillet with honey-lemon glaze, served with a fresh mixed green salad."},

    # ─── MENÚ INFANTIL ───
    {"id": "chicken-tenders", "prompt": "Golden crispy chicken tenders for kids, served with french fries. Fun and appetizing."},
    {"id": "cheeseburger", "prompt": "A mini cheeseburger with a small beef patty, melted cheese, served with french fries. Kid-friendly."},
    {"id": "mac-and-cheese", "prompt": "Creamy macaroni and cheese in a small bowl. Comfort food for kids, golden and bubbly."},

    # ─── DIPS ───
    {"id": "garlic-butter", "prompt": "A small ramekin of golden melted garlic butter dip with herbs."},
    {"id": "salsa-mafiosa", "prompt": "A small ramekin of dark red-brown secret sauce dip. Mysterious and appetizing."},
    {"id": "miel-picante", "prompt": "A small glass jar of golden hot honey with red chili flakes visible. Sweet and spicy."},
    {"id": "pomodoro-ahumado", "prompt": "A small ramekin of smoky tomato sauce dip, deep red-orange color."},
    {"id": "ajo-parmesano", "prompt": "A small ramekin of creamy garlic parmesan dip, golden white with herbs."},
    {"id": "salsa-ranch", "prompt": "A small ramekin of creamy white ranch dressing dip with herbs."},

    # ─── POSTRES ───
    {"id": "brownie-con-helado", "prompt": "A warm chocolate brownie with a scoop of vanilla ice cream on top, chocolate sauce drizzle, on a white plate."},
    {"id": "flan-de-coco", "prompt": "A traditional coconut flan dessert with caramel sauce, plated elegantly. Smooth and golden."},
    {"id": "chocolate-chip-cookie-con-helado", "prompt": "A large warm chocolate chip cookie with a scoop of vanilla ice cream melting on top."},

    # ─── BEBIDAS ───
    {"id": "te-viva-la-pizza", "prompt": "An elegant glass of iced herbal tea with a warm amber color, served in a tall glass with ice."},
    {"id": "raspadura-con-limon", "prompt": "A traditional Panamanian raspadura drink with lemon in a tall glass, golden-brown sugarcane color with ice."},
    {"id": "jugo-de-maracuya", "prompt": "A glass of fresh passion fruit juice, vibrant yellow-orange color, with ice and condensation on glass."},
    {"id": "limonada", "prompt": "A tall glass of fresh lemonade with ice, lemon slices, and a sprig of mint. Refreshing and bright."},
    {"id": "jugo-de-naranja", "prompt": "A glass of freshly squeezed orange juice, bright orange, with ice. Natural and vibrant."},
    {"id": "sodas", "prompt": "A variety of colorful soda bottles and glasses on a rustic surface. Coca-Cola, Sprite, and fruit sodas."},
    {"id": "agua", "prompt": "A clear glass bottle of purified water with ice in a glass beside it. Clean and minimalist."},
    {"id": "agua-perrier", "prompt": "A green Perrier sparkling water bottle with a glass of sparkling water with bubbles and ice."},

    # ─── SODAS ARTESANALES ───
    {"id": "mango-pasion", "prompt": "A craft soda bottle and glass with vibrant mango-passion fruit color, golden orange, with ice."},
    {"id": "ginguru", "prompt": "A craft ginger beer bottle and glass, amber golden color with bubbles, artisanal style."},
    {"id": "mansa-cola", "prompt": "An artisanal Panamanian cola bottle and glass, dark caramel color with ice and bubbles."},
    {"id": "napi-colada", "prompt": "A craft piña colada soda bottle and glass, creamy tropical white-yellow color with ice."},
    {"id": "pepimon", "prompt": "A craft cucumber-lemon soda bottle and glass, light green color with ice. Fresh and cool."},

    # ─── CAFÉ ───
    {"id": "espresso", "prompt": "A single shot of espresso in a small white ceramic cup on a saucer. Rich crema on top, dark and intense."},
    {"id": "americano", "prompt": "A cup of americano coffee in a white ceramic mug. Black coffee with a rich aroma."},
    {"id": "capuccino", "prompt": "A cappuccino in a white cup with beautiful latte art foam on top. Warm and inviting."},
    {"id": "latte", "prompt": "A latte in a tall glass with creamy steamed milk and a thin layer of foam. Smooth and milky."},
    {"id": "macchiato", "prompt": "An espresso macchiato in a small white cup, espresso with a dot of frothed milk on top."},

    # ─── CÓCTELES ───
    {"id": "mojito", "prompt": "A classic mojito cocktail in a tall glass with fresh mint, lime wedges, rum, and crushed ice."},
    {"id": "margarita-coctel", "prompt": "A classic margarita cocktail in a salt-rimmed glass with a lime wedge. Frozen or on the rocks."},
    {"id": "moscow-mule", "prompt": "A Moscow mule cocktail in a copper mug with ginger beer, vodka, lime, and crushed ice."},
    {"id": "aperol", "prompt": "An Aperol spritz cocktail in a wine glass with orange slice, prosecco, and ice. Bright orange color."},
    {"id": "gin-tonic", "prompt": "A gin and tonic in a large balloon glass with ice, juniper berries, and a citrus peel garnish."},
    {"id": "sangria", "prompt": "A glass of red sangria with fresh fruit pieces (oranges, apples, berries) in a wine glass with ice."},

    # ─── CERVEZAS ───
    {"id": "balboa", "prompt": "A cold Panamanian beer in a glass with a golden amber color, condensation on the glass, and foam head."},
    {"id": "atlas-golden", "prompt": "A golden premium Panamanian beer in a tall glass with a crisp foam head and condensation."},
    {"id": "panama", "prompt": "A cold light beer in a glass with golden color, foam head, and water droplets on the glass."},
    {"id": "corona", "prompt": "A Corona beer bottle with a lime wedge in the neck, served with a glass of golden beer and ice."},
    {"id": "modelo", "prompt": "A Modelo Especial beer in a glass, rich golden color with a perfect foam head."},
    {"id": "casa-bruja", "prompt": "A craft beer from Panama in a tulip glass, amber-copper color with a creamy foam head. Artisanal."},
    {"id": "central", "prompt": "A Panamanian craft beer in a glass, rich amber color with foam. Artisanal brewing style."},

    # ─── VINOS ───
    {"id": "copa-de-vino", "prompt": "A glass of red wine in an elegant wine glass, deep ruby color, on a dark rustic wood surface."},
    {"id": "botella-de-vino", "prompt": "An elegant wine bottle with a glass of red wine. Dark label, deep ruby color, sophisticated setting."},
]


def generate_image(client, prompt, output_path, retries=2):
    """Generate a single image from a text prompt using Nano Banana Pro."""
    from google.genai import types

    full_prompt = STYLE_PREFIX + prompt

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=full_prompt)],
        )
    ]

    config = types.GenerateContentConfig(
        response_modalities=["IMAGE", "TEXT"],
        temperature=1.0,
    )

    for attempt in range(retries + 1):
        try:
            response = client.models.generate_content(
                model=NANO_BANANA_MODEL,
                contents=contents,
                config=config,
            )

            if response.candidates:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, "inline_data") and part.inline_data:
                        # Save as PNG first, then convert to WebP
                        png_path = output_path.replace(".webp", ".png")
                        with open(png_path, "wb") as f:
                            f.write(part.inline_data.data)

                        # Convert to WebP using sips (macOS built-in)
                        try:
                            subprocess.run(
                                ["sips", "-s", "format", "webp", "-s", "formatOptions", "80", png_path, "--out", output_path],
                                capture_output=True, check=True
                            )
                            os.remove(png_path)
                        except Exception:
                            # Fallback: just keep the PNG renamed as webp
                            os.rename(png_path, output_path)

                        return output_path

            if attempt < retries:
                print(f"    No image returned, retrying ({attempt + 1}/{retries})...")
                time.sleep(3)
            else:
                print(f"    [FAIL] No image generated after {retries + 1} attempts")
                return None

        except Exception as e:
            if attempt < retries:
                print(f"    Error: {e}, retrying ({attempt + 1}/{retries})...")
                time.sleep(3)
            else:
                print(f"    [FAIL] {e}")
                return None

    return None


def main():
    parser = argparse.ArgumentParser(description="Generate Viva la Pizza menu images")
    parser.add_argument("--start-from", type=int, default=0,
                        help="Start from item index (0-based)")
    parser.add_argument("--only", type=str, default=None,
                        help="Generate only this item ID")
    args = parser.parse_args()

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not found in .env")
        sys.exit(1)

    from google import genai
    client = genai.Client(api_key=api_key)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Filter items
    if args.only:
        items = [m for m in MENU_ITEMS if m["id"] == args.only]
        if not items:
            print(f"Error: Item '{args.only}' not found")
            sys.exit(1)
    else:
        items = MENU_ITEMS[args.start_from:]

    print(f"Generating {len(items)} menu images using Nano Banana Pro...")
    print(f"Output: {OUTPUT_DIR}/")
    print()

    success = 0
    failed = 0
    skipped = 0

    for i, item in enumerate(items):
        global_idx = args.start_from + i if not args.only else 0
        output_path = os.path.join(OUTPUT_DIR, f"{item['id']}.webp")

        # Skip if already exists
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            print(f"[{global_idx + 1}] {item['id']} — already exists, skipping")
            skipped += 1
            continue

        print(f"[{global_idx + 1}/{len(MENU_ITEMS)}] {item['id']}...")

        result = generate_image(client, item["prompt"], output_path)
        if result:
            size_kb = os.path.getsize(result) / 1024
            print(f"    ✓ Saved ({size_kb:.0f} KB)")
            success += 1
        else:
            print(f"    ✗ FAILED")
            failed += 1

        # Rate limit buffer
        if i < len(items) - 1:
            time.sleep(2.5)

    print()
    print(f"Done! {success} generated, {failed} failed, {skipped} skipped.")
    print(f"Images saved to: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
