#!/usr/bin/env python3
"""make_thumbnail.py — generate a 1280x720 split-layout YouTube thumbnail.

Left kraft panel: word + pinyin + English (max contrast).
Right: cover-cropped photos (use the SAME ref images as the collage).

Run from contents/word/ so `import card_generator` works:
    python3 .../make_thumbnail.py <ep_dir> <word> <pinyin> <desc_en> <ref1> [ref2]

Examples:
    python3 make_thumbnail.py ep0002_lu-cha 绿茶 "lǜ chá" "sweet but scheming" ref/12.png ref/11.png
    (2 refs = top/bottom split; 1 ref = full-height single photo)
"""
import sys
sys.path.insert(0, ".")
import card_generator as cg
from PIL import Image, ImageDraw

TW, TH = 1280, 720
SEAM = 700          # photo panel starts at x=700
GAP = 0             # no gap between stacked photos


def cover(path, w, h):
    im = Image.open(path).convert("RGB")
    sw, sh = im.size
    s = max(w / sw, h / sh)
    nw, nh = round(sw * s), round(sh * s)
    im = im.resize((nw, nh), Image.LANCZOS)
    l, t = (nw - w) // 2, (nh - h) // 2
    return im.crop((l, t, l + w, t + h))


def main():
    ep_dir, word, pinyin, desc_en = sys.argv[1:5]
    refs = sys.argv[5:7]
    pw, ph = TW - SEAM, TH

    canvas = cg._make_walnut().resize((TW, TH), Image.LANCZOS).convert("RGB")

    if len(refs) >= 2:
        half = (ph - GAP) // 2
        canvas.paste(cover(f"{ep_dir}/{refs[0]}", pw, half), (SEAM, 0))
        canvas.paste(cover(f"{ep_dir}/{refs[1]}", pw, ph - half - GAP), (SEAM, half + GAP))
    else:
        canvas.paste(cover(f"{ep_dir}/{refs[0]}", pw, ph), (SEAM, 0))

    draw = ImageDraw.Draw(canvas)
    if len(refs) >= 2:
        half = (ph - GAP) // 2
        draw.rectangle([SEAM, half, TW, half + GAP], fill=cg.BG_BASE)

    # seam: gradient shadow + accent line
    shadow = Image.new("RGBA", (60, TH), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    for i in range(60):
        sd.line([(i, 0), (i, TH)], fill=(0, 0, 0, int(90 * (1 - i / 60))))
    canvas.paste(shadow.convert("RGB"), (SEAM, 0), shadow)
    draw.rectangle([SEAM - 5, 0, SEAM - 1, TH], fill=cg.ACCENT)

    # left text block
    cx = SEAM // 2
    wf = cg.fnt_cn(230, bold=True)
    ww, wh = cg.tw(word, wf), cg.th(230)
    wy = 150
    draw.text((cx - ww // 2, wy), word, font=wf, fill=cg.ACCENT)
    y = wy + wh + 30
    pf = cg.fnt_cn(80, bold=True)
    draw.text((cx - cg.tw(pinyin, pf) // 2, y), pinyin, font=pf, fill=cg.MID)
    y += cg.th(80) + 28
    draw.line([(cx - 130, y), (cx + 130, y)], fill=cg.ACCENT, width=4)
    y += 34
    ef = cg.fnt_cn(46, bold=True)
    draw.text((cx - cg.tw(desc_en, ef) // 2, y), desc_en, font=ef, fill=cg.MID)

    out = f"{ep_dir}/thumbnail.png"
    canvas.save(out)
    print("saved", out, canvas.size)


if __name__ == "__main__":
    main()
