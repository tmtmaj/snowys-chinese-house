"""
generate_images.py — 小雪的中文屋 image generator

Usage:
    python generate_images.py \
        --idiom "过眼云烟" \
        --pinyin "guò yǎn yún yān" \
        --meaning_cn "转瞬即逝，像云烟一样从眼前飘过" \
        --meaning_ko "눈앞을 스쳐가는 구름과 연기처럼 덧없이 사라지는 것" \
        --chars '过,guò,经过/通过,路过经过掠过' \
                '眼,yǎn,眼睛,过眼=从眼前掠过' \
                '云,yún,云彩,飘忽不定象征无常' \
                '烟,yān,烟雾,转瞬消散不留痕迹' \
        --episode 15 \
        --output_dir ./output

Produces:
    01_title_card.png        — opening title card
    02_char_X.png ... (×4)  — individual character cards
    06_meaning_infographic.png — meaning + origin + example
    07_thumbnail.png         — YouTube thumbnail (1280×720)
"""

import argparse
import os
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf"

def load_font(size):
    return ImageFont.truetype(FONT_PATH, size)

def gradient_bg(draw, w, h, top_color, bot_color):
    for i in range(h):
        r = int(top_color[0] + (bot_color[0] - top_color[0]) * i / h)
        g = int(top_color[1] + (bot_color[1] - top_color[1]) * i / h)
        b = int(top_color[2] + (bot_color[2] - top_color[2]) * i / h)
        draw.line([(0, i), (w, i)], fill=(r, g, b))

def centered_text(draw, text, font, y, w, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    x = (w - (bbox[2] - bbox[0])) // 2
    draw.text((x, y), text, font=font, fill=fill)

# ── Title card ─────────────────────────────────────────────────────────────
def make_title_card(idiom, pinyin, meaning_ko, out_dir):
    W, H = 1280, 720
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    gradient_bg(draw, W, H, (10, 20, 45), (25, 45, 90))

    draw.rectangle([0, 0, W, 8], fill=(80, 160, 220))

    centered_text(draw, idiom, load_font(160), 100, W, (255, 255, 255))
    centered_text(draw, pinyin, load_font(42), 310, W, (130, 200, 255))
    draw.line([(W//2 - 200, 375), (W//2 + 200, 375)], fill=(80, 160, 220), width=2)
    centered_text(draw, meaning_ko, load_font(28), 395, W, (200, 225, 255))
    centered_text(draw, "小雪的中文屋 · Snowy's Chinese House", load_font(20), H - 55, W, (100, 140, 180))

    draw.rectangle([0, H - 8, W, H], fill=(80, 160, 220))
    img.save(f"{out_dir}/01_title_card.png")
    print(f"  ✓ title_card")

# ── Character cards ─────────────────────────────────────────────────────────
CARD_PALETTES = [
    ((30, 80, 140), (80, 160, 220)),
    ((100, 40, 100), (180, 100, 200)),
    ((20, 90, 70), (60, 180, 130)),
    ((120, 60, 20), (220, 140, 60)),
]

def make_char_card(char, pinyin, meaning_cn, example, idx, out_dir):
    W, H = 640, 640
    bg_dark, bg_light = CARD_PALETTES[idx % len(CARD_PALETTES)]
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    gradient_bg(draw, W, H, bg_dark, tuple(min(255, c + 40) for c in bg_dark))

    # Number badge
    draw.ellipse([W - 70, 20, W - 20, 70], fill=tuple(min(255, c + 80) for c in bg_dark))
    draw.text((W - 54, 27), f"#{idx+1}", font=load_font(26), fill=(255, 255, 255))

    # Character
    centered_text(draw, char, load_font(260), 60, W, (255, 255, 255))

    draw.line([(W//2 - 120, 352), (W//2 + 120, 352)], fill=(255, 255, 255), width=2)
    centered_text(draw, pinyin, load_font(44), 365, W, (220, 240, 255))
    centered_text(draw, meaning_cn, load_font(28), 430, W, (200, 220, 255))
    centered_text(draw, example, load_font(22), 480, W, (170, 200, 230))

    bar = tuple(min(255, c + 60) for c in bg_light)
    draw.rectangle([0, H - 10, W, H], fill=bar)
    img.save(f"{out_dir}/0{idx+2}_char_{char}.png")
    print(f"  ✓ char_{char}")

# ── Meaning infographic ─────────────────────────────────────────────────────
def make_meaning_card(idiom, pinyin, meaning_cn, meaning_ko,
                      origin_text, origin_lines, example1, example1_ko,
                      example2, example2_ko, usage_note, out_dir):
    W, H = 1280, 720
    img = Image.new("RGB", (W, H), (245, 247, 250))
    draw = ImageDraw.Draw(img)

    f_title  = load_font(52)
    f_sub    = load_font(36)
    f_body   = load_font(24)
    f_label  = load_font(20)
    f_small  = load_font(18)

    # Header
    draw.rectangle([0, 0, W, 90], fill=(15, 50, 100))
    draw.text((50, 20), idiom, font=f_title, fill=(255, 255, 255))
    draw.text((430, 38), pinyin, font=f_sub, fill=(130, 190, 255))
    draw.text((W - 330, 35), "小雪的中文屋", font=f_body, fill=(100, 150, 200))

    def panel(x0, y0, x1, y1, hdr_color, hdr_text):
        draw.rectangle([x0, y0, x1, y1], fill=(255, 255, 255))
        draw.rectangle([x0, y0, x1, y0 + 40], fill=hdr_color)
        draw.text((x0 + 10, y0 + 8), hdr_text, font=f_body, fill=(255, 255, 255))

    # Left — meaning
    panel(30, 110, 390, 500, (30, 100, 180), "📖  字面含义")
    draw.text((40, 162), meaning_cn[:12], font=f_body, fill=(30, 50, 80))
    draw.text((40, 197), meaning_cn[12:] if len(meaning_cn) > 12 else "", font=f_body, fill=(30, 50, 80))
    draw.line([(40, 240), (370, 240)], fill=(220, 230, 240), width=1)
    draw.text((40, 255), "→ " + meaning_ko, font=f_small, fill=(80, 100, 140))

    # Middle — origin
    panel(410, 110, 860, 500, (60, 130, 80), "📜  成语来源")
    draw.text((420, 160), origin_text, font=f_label, fill=(80, 110, 90))
    draw.line([(420, 195), (840, 195)], fill=(220, 235, 225), width=1)
    y = 210
    for line in origin_lines[:4]:
        draw.text((420, y), line, font=f_body, fill=(40, 80, 55))
        y += 38

    # Right — examples
    panel(880, 110, W - 30, 500, (150, 60, 40), "💬  例句")
    draw.text((890, 160), example1, font=f_body, fill=(80, 40, 30))
    draw.text((890, 200), "→ " + example1_ko, font=f_small, fill=(140, 90, 80))
    draw.line([(890, 240), (W - 50, 240)], fill=(240, 220, 215), width=1)
    draw.text((890, 255), example2, font=f_body, fill=(80, 40, 30))
    draw.text((890, 295), "→ " + example2_ko, font=f_small, fill=(140, 90, 80))

    # Bottom usage note
    draw.rectangle([0, 510, W, 590], fill=(245, 245, 250))
    draw.text((50, 527), "⚠️  사용주의: ", font=f_label, fill=(100, 80, 130))
    draw.text((190, 529), usage_note, font=f_small, fill=(80, 70, 100))
    draw.rectangle([0, H - 40, W, H], fill=(15, 50, 100))
    centered_text(draw, "小雪的中文屋 · Snowy's Chinese House", f_small, H - 30, W, (150, 190, 230))

    img.save(f"{out_dir}/06_meaning_infographic.png")
    print(f"  ✓ meaning_infographic")

# ── Thumbnail ────────────────────────────────────────────────────────────────
def make_thumbnail(idiom, pinyin, meaning_ko, episode, out_dir):
    W, H = 1280, 720
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    gradient_bg(draw, W, H, (8, 12, 50), (20, 25, 75))

    # Atmospheric glow
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.ellipse([400, 100, 900, 600], fill=(60, 100, 200, 18))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Episode badge
    draw.rounded_rectangle([50, 40, 240, 95], radius=12, fill=(80, 160, 220))
    draw.text((68, 52), f"Idiom #{episode}", font=load_font(28), fill=(255, 255, 255))

    # Idiom (with shadow)
    f_big = load_font(200)
    bbox = draw.textbbox((0, 0), idiom, font=f_big)
    tx = (W - (bbox[2] - bbox[0])) // 2
    draw.text((tx + 4, 154), idiom, font=f_big, fill=(0, 25, 70))   # shadow
    draw.text((tx, 150), idiom, font=f_big, fill=(255, 255, 255))

    centered_text(draw, pinyin, load_font(46), 378, W, (130, 200, 255))

    # Korean meaning pill
    f_ko = load_font(32)
    bbox2 = draw.textbbox((0, 0), meaning_ko, font=f_ko)
    tw = bbox2[2] - bbox2[0]
    px = (W - tw) // 2
    draw.rounded_rectangle([px - 24, 435, px + tw + 24, 488], radius=8, fill=(10, 30, 70))
    draw.rounded_rectangle([px - 24, 435, px + tw + 24, 488], radius=8, outline=(80, 160, 220), width=2)
    draw.text((px, 447), meaning_ko, font=f_ko, fill=(200, 230, 255))

    centered_text(draw, "小雪的中文屋", load_font(22), H - 58, W, (100, 150, 200))
    draw.rectangle([0, H - 8, W, H], fill=(80, 160, 220))

    img.save(f"{out_dir}/07_thumbnail.png")
    print(f"  ✓ thumbnail")

# ── CLI entry point ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--idiom",       required=True)
    p.add_argument("--pinyin",      required=True)
    p.add_argument("--meaning_cn",  required=True)
    p.add_argument("--meaning_ko",  required=True)
    p.add_argument("--chars",       nargs=4, required=True,
                   help="4 items: 'char,pinyin,meaning,example'")
    p.add_argument("--origin_text", default="")
    p.add_argument("--origin_lines", nargs="*", default=[])
    p.add_argument("--example1",    default="")
    p.add_argument("--example1_ko", default="")
    p.add_argument("--example2",    default="")
    p.add_argument("--example2_ko", default="")
    p.add_argument("--usage_note",  default="")
    p.add_argument("--episode",     type=int, default=0)
    p.add_argument("--output_dir",  default="./output")
    args = p.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    print(f"Generating images for: {args.idiom}")

    make_title_card(args.idiom, args.pinyin, args.meaning_ko, args.output_dir)

    for i, char_spec in enumerate(args.chars):
        parts = char_spec.split(",", 3)
        make_char_card(*parts, i, args.output_dir)

    make_meaning_card(
        args.idiom, args.pinyin, args.meaning_cn, args.meaning_ko,
        args.origin_text, args.origin_lines,
        args.example1, args.example1_ko,
        args.example2, args.example2_ko,
        args.usage_note, args.output_dir
    )
    make_thumbnail(args.idiom, args.pinyin, args.meaning_ko, args.episode, args.output_dir)
    print(f"\n✅ All images saved to {args.output_dir}")
