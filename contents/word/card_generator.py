#!/usr/bin/env python3
"""
Word study card generator.
Produces PNG cards per episode: title + per-sentence cards + full-paragraph cards.

Output structure:
  output/
    ep01_网红/
      00_title.png
      01_p1_s1.png  ...
    ep02_xxx/
      ...
"""
from __future__ import annotations
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
import os
import json
import requests

# ── API Keys ───────────────────────────────────────────────────────────────
PIXABAY_API_KEY = "56303475-f2d30f64ac678915a05b68238"

# ── Paths ──────────────────────────────────────────────────────────────────
FONT_CN      = "/mnt/c/Windows/Fonts/NotoSansSC-VF.ttf"   # pinyin / english
FONT_CN_MAIN = "/mnt/c/Windows/Fonts/simkai.ttf"           # Chinese body text
FONT_KR      = "/mnt/c/Windows/Fonts/NotoSansKR-VF.ttf"
FONT_EMOJI   = "/mnt/c/Windows/Fonts/seguiemj.ttf"
OUT_DIR      = os.path.dirname(os.path.abspath(__file__))

# ── Design tokens ──────────────────────────────────────────────────────────
W, H   = 1920, 1080
MARGIN = 140
BG_BASE = (220, 188, 148)  # Warm Sand (light)
DARK    = (42,  26,  10)   # Dark ink (main text)
MID     = (98,  68,  38)   # Warm brown (pinyin)
LIGHT   = (142, 105,  68)  # Muted brown (english / label)
ACCENT  = (190,  80,  30)  # Terracotta (accent)
RED     = (210,  35,  35)  # Pure red (keyword highlight)

BG_IMAGE = "/mnt/c/Users/USER/Desktop/sucai/ce9e0254-6850-41b2-9946-163c8f9ee9ae.png"

# ── Font helpers ───────────────────────────────────────────────────────────
_cn_cache: dict[tuple, ImageFont.FreeTypeFont] = {}
_kr_cache: dict[tuple, ImageFont.FreeTypeFont] = {}

def fnt_cn(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    key = (size, bold)
    if key not in _cn_cache:
        f = ImageFont.truetype(FONT_CN, size)
        if bold:
            try: f.set_variation_by_axes([700])
            except Exception: pass
        _cn_cache[key] = f
    return _cn_cache[key]

def fnt_kr(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    key = (size, bold)
    if key not in _kr_cache:
        f = ImageFont.truetype(FONT_KR, size)
        if bold:
            try: f.set_variation_by_axes([700])
            except Exception: pass
        _kr_cache[key] = f
    return _kr_cache[key]

def is_korean(ch: str) -> bool:
    cp = ord(ch)
    return (0xAC00 <= cp <= 0xD7A3) or (0x1100 <= cp <= 0x11FF) or (0x3130 <= cp <= 0x318F)

def fnt_auto(ch: str, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return fnt_kr(size, bold) if is_korean(ch) else fnt_cn(size, bold)

_cn_main_cache: dict[int, ImageFont.FreeTypeFont] = {}

def fnt_cn_main(size: int) -> ImageFont.FreeTypeFont:
    if size not in _cn_main_cache:
        _cn_main_cache[size] = ImageFont.truetype(FONT_CN_MAIN, size)
    return _cn_main_cache[size]

_emoji_cache: dict[int, ImageFont.FreeTypeFont] = {}

def fnt_emoji(size: int) -> ImageFont.FreeTypeFont:
    if size not in _emoji_cache:
        _emoji_cache[size] = ImageFont.truetype(FONT_EMOJI, size)
    return _emoji_cache[size]

def draw_emoji(draw: ImageDraw.ImageDraw, emoji: str, x: int, y: int, size: int, color=DARK) -> int:
    f = fnt_emoji(size)
    draw.text((x, y), emoji, font=f, fill=color, embedded_color=True)
    return x + (f.getbbox(emoji)[2] - f.getbbox(emoji)[0])

# ── Measurement ────────────────────────────────────────────────────────────

def tw(text: str, f: ImageFont.FreeTypeFont) -> int:
    return f.getbbox(text)[2] - f.getbbox(text)[0]

def th(size: int) -> int:
    bb = fnt_cn(size).getbbox("网Ag")
    return bb[3] - bb[1]

# ── Mixed-script text rendering ────────────────────────────────────────────

def draw_mixed(draw: ImageDraw.ImageDraw, text: str, x: int, y: int, size: int, color: str, bold: bool = False) -> int:
    """Draw text with automatic Korean/Chinese font switching. Returns x after last char."""
    cx = x
    i = 0
    while i < len(text):
        f = fnt_auto(text[i], size, bold)
        j = i + 1
        while j < len(text) and fnt_auto(text[j], size, bold) is f:
            j += 1
        chunk = text[i:j]
        draw.text((cx, y), chunk, font=f, fill=color)
        cx += tw(chunk, f)
        i = j
    return cx

def mixed_width(text: str, size: int, bold: bool = False) -> int:
    total = 0
    i = 0
    while i < len(text):
        f = fnt_auto(text[i], size, bold)
        j = i + 1
        while j < len(text) and fnt_auto(text[j], size, bold) is f:
            j += 1
        total += tw(text[i:j], f)
        i = j
    return total

# ── Segment rendering (for v-mark text) ───────────────────────────────────
# Segment: (text, font, color, y_shift, stroke_width)
Segment = tuple[str, ImageFont.FreeTypeFont, tuple, int, int]

def parse_v(text: str, cn_size: int, v_size: int) -> list[Segment]:
    cf = fnt_cn_main(cn_size)
    vf = fnt_cn(v_size, bold=True)
    v_shift = -(th(v_size) // 3)
    stroke = max(1, cn_size // 60)
    segs: list[Segment] = []
    # Split by ★ first (odd-index parts are red-highlighted)
    star_parts = text.split("★")
    for si, star_part in enumerate(star_parts):
        is_red = (si % 2 == 1)
        if is_red:
            if star_part:
                segs.append((star_part, cf, RED, 0, stroke))
        else:
            # Process ∨ markers within non-highlighted parts
            parts = star_part.split("∨")
            for i, part in enumerate(parts):
                if part:
                    segs.append((part, cf, DARK, 0, stroke))
                if i < len(parts) - 1:
                    segs.append(("v", vf, ACCENT, v_shift, 0))
    return segs

def wrap_segs(segs: list[Segment], max_w: int) -> list[list[Segment]]:
    lines: list[list[Segment]] = []
    line: list[Segment] = []
    cur_w = 0

    for seg in segs:
        text, f, color, y_shift, stroke = seg
        seg_w = tw(text, f)

        if cur_w + seg_w <= max_w:
            line.append(seg)
            cur_w += seg_w
            continue

        # Segment doesn't fit — split character by character
        buf = ""
        for ch in text:
            new_w = tw(buf + ch, f)
            if cur_w + new_w <= max_w:
                buf += ch
            else:
                if buf:
                    line.append((buf, f, color, y_shift, stroke))
                lines.append(line)
                line = []
                cur_w = 0
                buf = ch
        if buf:
            line.append((buf, f, color, y_shift, stroke))
            cur_w += tw(buf, f)

    if line:
        lines.append(line)
    return _fix_orphan_punct(lines)

# 禁则处理: a line must never begin with closing punctuation — pull it up to the
# previous line (hangs past max_w by at most one glyph, absorbed by MARGIN).
_CLOSING = set("。，、！？：；）》」』】〉…”’%")

def _fix_orphan_punct(lines: list[list[Segment]]) -> list[list[Segment]]:
    for i in range(1, len(lines)):
        while lines[i] and lines[i - 1]:
            text, f, color, y_shift, stroke = lines[i][0]
            j = 0
            while j < len(text) and text[j] in _CLOSING:
                j += 1
            if j == 0:
                break
            lines[i - 1].append((text[:j], f, color, y_shift, stroke))
            if text[j:]:
                lines[i][0] = (text[j:], f, color, y_shift, stroke)
                break
            lines[i].pop(0)
    return [ln for ln in lines if ln]

def draw_seg_line(draw: ImageDraw.ImageDraw, segs: list[Segment], x: int, y: int) -> None:
    cx = x
    for text, f, color, y_shift, stroke in segs:
        draw.text((cx, y + y_shift), text, font=f, fill=color,
                  stroke_width=stroke, stroke_fill=color)
        cx += tw(text, f)

def draw_v_text(
    draw: ImageDraw.ImageDraw,
    text: str, x: int, y: int,
    cn_size: int, v_size: int, max_w: int,
) -> int:
    segs = parse_v(text, cn_size, v_size)
    lines = wrap_segs(segs, max_w)
    line_h = th(cn_size) + 14
    for line in lines:
        draw_seg_line(draw, line, x, y)
        y += line_h
    return y

def measure_v(text: str, cn_size: int, v_size: int, max_w: int) -> int:
    segs = parse_v(text, cn_size, v_size)
    lines = wrap_segs(segs, max_w)
    return len(lines) * (th(cn_size) + 14)

def measure_plain(text: str, size: int, max_w: int) -> int:
    return len(wrap_plain_raw(text, size, max_w)) * (th(size) + 8)

def wrap_plain_raw(text: str, size: int, max_w: int) -> list[str]:
    """wrap_plain without bold dependency — used for measurement."""
    words = text.split(" ")
    lines, cur = [], ""
    for w in words:
        test = f"{cur} {w}".strip()
        if mixed_width(test, size, bold=True) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def wrap_plain(text: str, size: int, max_w: int) -> list[str]:
    return wrap_plain_raw(text, size, max_w)

# ── Base card ──────────────────────────────────────────────────────────────

def _make_walnut() -> Image.Image:
    try:
        img = Image.open(BG_IMAGE).convert("RGB").resize((W, H), Image.LANCZOS)
        return img
    except Exception:
        rng = np.random.default_rng(42)
        noise = rng.normal(0, 5, (H, W, 3))
        base_arr = np.array(BG_BASE, dtype=np.float32)
        arr = np.clip(base_arr + noise, 0, 255).astype(np.uint8)
        return Image.fromarray(arr).filter(ImageFilter.GaussianBlur(radius=0.5))

_BG: Image.Image | None = None

def base() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    global _BG
    if _BG is None:
        _BG = _make_walnut()
    img = _BG.copy()
    draw = ImageDraw.Draw(img)
    return img, draw

def label_tr(draw: ImageDraw.ImageDraw, text: str) -> None:
    size = 28
    x = W - MARGIN - mixed_width(text, size, bold=True)
    draw_mixed(draw, text, x, 46, size, LIGHT, bold=True)

# ── Card makers ────────────────────────────────────────────────────────────

def make_title(word: str, pinyin: str, desc_en: str) -> Image.Image:
    img, draw = base()

    y = 360
    wf = fnt_cn(160, bold=True)
    ww = tw(word, wf)
    draw.text(((W - ww) // 2, y), word, font=wf, fill=ACCENT)
    y += th(160) + 28

    pf = fnt_cn(52, bold=True)
    draw.text(((W - tw(pinyin, pf)) // 2, y), pinyin, font=pf, fill=MID)
    y += th(52) + 40

    draw.line([(W // 2 - 120, y + 6), (W // 2 + 120, y + 6)], fill=ACCENT, width=3)
    y += 40

    dw = mixed_width(desc_en, 36, bold=True)
    draw_mixed(draw, desc_en, (W - dw) // 2, y, 36, MID, bold=True)

    return img


def _fit_sentence_sizes(cn: str, pinyin: str, english: str, usable: int, avail_h: int):
    BASE_CN, BASE_V, BASE_PF, BASE_EF = 70, 44, 36, 30
    scale = 1.3
    while scale >= 0.3:
        s = lambda b: max(12, int(b * scale))
        h = (measure_v(cn, s(BASE_CN), s(BASE_V), usable) + 28
             + measure_plain(pinyin, s(BASE_PF), usable) + 28
             + measure_plain(english, s(BASE_EF), usable))
        if h <= avail_h:
            return s(BASE_CN), s(BASE_V), s(BASE_PF), s(BASE_EF)
        scale -= 0.05
    s = lambda b: max(12, int(b * 0.3))
    return s(BASE_CN), s(BASE_V), s(BASE_PF), s(BASE_EF)


def _fit_paragraph_sizes(sentences_cn: list[str], sentences_py: list[str], usable: int, avail_h: int):
    BASE_CN, BASE_V, BASE_PY = 50, 32, 28
    scale = 3.0
    while scale >= 0.3:
        s = lambda b: max(12, int(b * scale))
        h = sum(
            measure_v(cn, s(BASE_CN), s(BASE_V), usable) + 4
            + measure_plain(py, s(BASE_PY), usable) + 20
            for cn, py in zip(sentences_cn, sentences_py)
        )
        if h <= avail_h:
            return s(BASE_CN), s(BASE_V), s(BASE_PY)
        scale -= 0.05
    s = lambda b: max(12, int(b * 0.3))
    return s(BASE_CN), s(BASE_V), s(BASE_PY)


_SECTION_NUMS = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
_SECTION_PY   = ["yī", "èr", "sān", "sì", "wǔ", "liù", "qī", "bā", "jiǔ", "shí"]

def make_section(para_idx: int) -> Image.Image:
    """Paragraph separator card: 第N段"""
    img, draw = base()
    num_cn = _SECTION_NUMS[para_idx - 1]

    main = f"第{num_cn}段"
    en_text = f"Paragraph {para_idx}"

    cy = H // 2 - th(140) - 20
    mf = fnt_cn(140, bold=True)
    mw = tw(main, mf)
    draw.text(((W - mw) // 2, cy), main, font=mf, fill=DARK)

    enw = mixed_width(en_text, 48, bold=True)
    draw_mixed(draw, en_text, (W - enw) // 2, cy + th(140) + 28, 48, MID, bold=True)

    draw.line([(W // 2 - 80, cy - 28), (W // 2 + 80, cy - 28)], fill=ACCENT, width=3)

    return img


def make_review_sep() -> Image.Image:
    """Review separator card: 复习"""
    img, draw = base()

    main = "复习"
    en_text = "Review"

    cy = H // 2 - th(140) - 20
    mf = fnt_cn(140, bold=True)
    mw = tw(main, mf)
    draw.text(((W - mw) // 2, cy), main, font=mf, fill=DARK)

    enw = mixed_width(en_text, 48, bold=True)
    draw_mixed(draw, en_text, (W - enw) // 2, cy + th(140) + 28, 48, DARK, bold=True)

    draw.line([(W // 2 - 80, cy - 28), (W // 2 + 80, cy - 28)], fill=ACCENT, width=3)

    return img


def _fit_review_sizes(all_cn: list[str], usable: int, avail_h: int):
    BASE_CN, BASE_V = 50, 32
    scale = 2.0
    while scale >= 0.3:
        s = lambda b: max(12, int(b * scale))
        h = sum(measure_v(cn, s(BASE_CN), s(BASE_V), usable) for cn in all_cn)
        gap_total = (len(all_cn) - 1) * int(16 * scale)
        if h + gap_total <= avail_h:
            return s(BASE_CN), s(BASE_V), int(16 * scale)
        scale -= 0.05
    s = lambda b: max(12, int(b * 0.3))
    return s(BASE_CN), s(BASE_V), 8


def make_review(paragraphs_cn: list[list[str]], label: str = "") -> Image.Image:
    """Full review card: all sentences in Chinese only, grouped by paragraph."""
    img, draw = base()

    LABEL_H = 0
    TOP = 72
    if label:
        lf = fnt_cn(64, bold=True)
        lw = tw(label, lf)
        lx = (W - lw) // 2
        draw.text((lx, TOP), label, font=lf, fill=DARK)
        LABEL_H = th(64) + 18
        line_y = TOP + LABEL_H - 4
        draw.line([(lx, line_y), (lx + lw, line_y)], fill=ACCENT, width=3)
        LABEL_H += 20

    TOP = TOP + LABEL_H
    usable = W - 2 * MARGIN
    avail_h = H - TOP - MARGIN

    all_cn = [cn for para in paragraphs_cn for cn in para]
    cn_s, v_s, gap = _fit_review_sizes(all_cn, usable, avail_h)

    bar_x = MARGIN - 24
    y = TOP
    for p_i, para in enumerate(paragraphs_cn):
        for cn in para:
            block_h = measure_v(cn, cn_s, v_s, usable)
            draw.rectangle([(bar_x, y), (bar_x + 5, y + block_h)], fill=ACCENT)
            y = draw_v_text(draw, cn, MARGIN, y, cn_size=cn_s, v_size=v_s, max_w=usable)
            y += gap
        if p_i < len(paragraphs_cn) - 1:
            y += gap

    return img


def make_sentence(cn: str, pinyin: str, english: str, label: str) -> Image.Image:
    img, draw = base()

    TOP = 200
    usable = W - 2 * MARGIN
    avail_h = H - TOP - MARGIN

    cn_s, v_s, pf_s, ef_s = _fit_sentence_sizes(cn, pinyin, english, usable, avail_h)

    pf_lines = wrap_plain(pinyin, pf_s, usable)
    ef_lines = wrap_plain(english, ef_s, usable)

    # measure total block height for the left bar
    cn_h  = measure_v(cn, cn_s, v_s, usable)
    pf_h  = len(pf_lines) * (th(pf_s) + 8)
    ef_h  = len(ef_lines) * (th(ef_s) + 8)
    y_end = TOP + cn_h + 28 + pf_h + 28 + ef_h

    # left accent bar grouping the three elements
    bar_x = MARGIN - 24
    draw.rectangle([(bar_x, TOP), (bar_x + 5, y_end)], fill=ACCENT)

    y = TOP
    y = draw_v_text(draw, cn, MARGIN, y, cn_size=cn_s, v_size=v_s, max_w=usable)
    y += 28
    for line in pf_lines:
        draw_mixed(draw, line, MARGIN, y, pf_s, MID, bold=True)
        y += th(pf_s) + 8
    y += 28
    for line in ef_lines:
        draw_mixed(draw, line, MARGIN, y, ef_s, LIGHT, bold=True)
        y += th(ef_s) + 8

    return img


def make_paragraph(sentences_cn: list[str], sentences_py: list[str], label: str) -> Image.Image:
    img, draw = base()

    TOP = 140
    usable = W - 2 * MARGIN
    avail_h = H - TOP - MARGIN

    cn_s, v_s, py_s = _fit_paragraph_sizes(sentences_cn, sentences_py, usable, avail_h)

    bar_x = MARGIN - 24
    y = TOP
    for cn, py in zip(sentences_cn, sentences_py):
        py_lines = wrap_plain(py, py_s, usable)
        block_h = measure_v(cn, cn_s, v_s, usable) + 4 + len(py_lines) * (th(py_s) + 4)
        draw.rectangle([(bar_x, y), (bar_x + 5, y + block_h)], fill=ACCENT)

        y = draw_v_text(draw, cn, MARGIN, y, cn_size=cn_s, v_size=v_s, max_w=usable)
        y += 4
        for line in py_lines:
            draw_mixed(draw, line, MARGIN, y, py_s, MID, bold=True)
            y += th(py_s) + 4
        y += 28

    return img

# ── Episodes ───────────────────────────────────────────────────────────────

EPISODES = [
    {
        "word":    "网红",
        "slug":    "wang-hong",
        "pinyin":  "wǎng hóng",
        "desc_en": "internet celebrity",
        "search_query": "social media influencer live streaming vlogger",
        "collage_images": [11, 12],
        "emoji":   "📱",
        "para_labels": [
            "What is a 网红?",
            "Xiao Li makes his move",
            "The cat takes over",
        ],
        "script": {
            "opening":
                "大家好！今天我们来学一个超级流行的词——网红！\n"
                "网，就是网络、互联网；红，就是出名、有名气。\n"
                "合在一起，网红，就是在网上很有名的人，也就是网络红人！\n"
                "现在中国到处都是网红，连猫和狗都能当网红……\n"
                "到底是怎么回事？我们一起来看看吧！",
            "p1_intro":
                "好，我们先来看第一段，了解一下网红到底是什么。",
            "p1_s1_note":
                "注意这个句型——是什么？\n"
                "\"A是什么\" 就是问 \"A是什么意思\" 或者 \"A是怎样的东西\"。\n"
                "这个句型很常用，大家一定要记住！",
            "p1_s2_note":
                "这里有一个很好用的结构——靠X吃饭。\n"
                "靠，就是依靠；吃饭，就是谋生。\n"
                "靠脸吃饭，靠才艺吃饭，靠搞笑吃饭……\n"
                "大家想靠什么吃饭呢？哈哈！\n"
                "还有，简单来说，这个表达很实用，意思是\"简单地说\"。",
            "p1_s3_note":
                "注意这个强调句型——连……都……\n"
                "连猫和狗都能当网红，意思是：就连猫和狗这样的动物也能当网红！\n"
                "还有一个词——借口，就是理由、托词。\n"
                "你还有什么借口？哈哈，是不是压力很大？",
            "p1_wrap":
                "好，第一段结束！\n"
                "我们知道了网红就是靠脸、靠才艺、靠搞笑吃饭的人，\n"
                "甚至连猫和狗都能当网红。\n"
                "接下来，我们来认识一下主人公小李！",
            "p2_intro":
                "第二段，我们来看看小李是怎么决定当网红的。",
            "p2_s1_note":
                "就是这样——这个表达表示\"正是如此\"或者\"就是这种感觉\"。\n"
                "很口语化，日常生活中经常用到。",
            "p2_s2_note":
                "突然，表示出乎意料、没有预兆。\n"
                "宣布，是一个比较正式的词，表示公开宣告。\n"
                "小李突然宣布——这个组合是不是很有戏剧感？哈哈！",
            "p2_s3_note":
                "打算，表示计划、想要做某件事。\n"
                "比如：你打算做什么？我打算去旅游。\n"
                "补光灯，就是拍照拍视频用的灯，ring light。\n"
                "内容还没想好，但已经买了三个补光灯……这个操作，大家熟不熟悉？哈哈！",
            "p2_wrap":
                "第二段结束！\n"
                "小李下定决心当网红，虽然不知道拍什么，但补光灯已经准备好了。\n"
                "那么结果怎么样呢？我们来看第三段！",
            "p3_intro":
                "第三段，见证奇迹的时刻到了！",
            "p3_s1_note":
                "意外，表示出乎意料。\n"
                "走红，就是变得有名、爆红。\n"
                "粉丝，就是fans，支持者。\n"
                "五十万粉丝——五十万！这可不是一个小数字！",
            "p3_s2_note":
                "猫奴——这个词太有意思了！\n"
                "奴，就是奴隶；猫奴，就是猫的奴隶，形容特别宠猫、为猫服务的人。\n"
                "全职猫奴，就是全职为猫打工……哈哈，小李的梦想和现实差距有点大！",
            "p3_s3_note":
                "秘诀，就是秘密的方法、诀窍。\n"
                "颜值，就是外貌的分数，颜值高就是长得好看。\n"
                "有缘分，表示命中注定的缘分。\n"
                "所以，成为网红的秘诀不是颜值，不是努力，而是……你家有没有一只有缘分的猫！哈哈！",
            "p3_wrap":
                "第三段结束！\n"
                "最后当上网红的，不是小李，而是他的猫。\n"
                "这就是生活！好，接下来我们来复习一下今天学的内容吧！",
            "closing":
                "好，今天我们学了网红这个词，还学了很多实用的表达：\n"
                "靠X吃饭、连……都……、打算、走红、颜值……\n"
                "大家都记住了吗？\n"
                "如果觉得有帮助，请点赞订阅，我们下次见！再见！",
        },
        "paragraphs": [
            [
                {
                    "cn": "★网红★∨是什么？",
                    "py": "Wǎng hóng shì shénme?",
                    "en": "What is a 网红?",
                },
                {
                    "cn": '简单来说，∨就是"靠脸、靠才艺、靠搞笑∨吃饭的人"。',
                    "py": 'Jiǎndān lái shuō, jiùshì "kào liǎn, kào cáiyì, kào gǎoxiào chīfàn de rén".',
                    "en": "Simply put, it's someone who makes a living through looks, talent, or humor.",
                },
                {
                    "cn": "不过现在∨连猫和狗∨都能当★网红★，所以……你还有什么借口？",
                    "py": "Búguò xiànzài lián māo hé gǒu dōu néng dāng wǎng hóng, suǒyǐ…… nǐ hái yǒu shénme jièkǒu?",
                    "en": "But these days even cats and dogs can become 网红, so… what's your excuse?",
                },
            ],
            [
                {
                    "cn": "小李∨就是这样想的。",
                    "py": "Xiǎo Lǐ jiùshì zhèyàng xiǎng de.",
                    "en": "Xiao Li thought exactly this way.",
                },
                {
                    "cn": '有一天∨他突然宣布："我要当★网红★！"',
                    "py": 'Yǒu yītiān tā tūrán xuānbù: "Wǒ yào dāng wǎng hóng!"',
                    "en": 'One day he suddenly announced: "I want to be a 网红!"',
                },
                {
                    "cn": '朋友问他∨打算做什么内容，他想了三秒∨说："还没想好，∨但我已经买了三个补光灯。"',
                    "py": 'Péngyou wèn tā dǎsuàn zuò shénme nèiróng, tā xiǎngle sān miǎo shuō: "Hái méi xiǎng hǎo, dàn wǒ yǐjīng mǎile sān gè bǔguāng dēng."',
                    "en": "His friend asked what content he planned. He thought 3 seconds: \"Haven't decided, but I already bought three ring lights.\"",
                },
            ],
            [
                {
                    "cn": "结果……他的猫∨因为坐在补光灯前睡觉，意外走红，现在有五十万粉丝。",
                    "py": "Jiéguǒ…… tā de māo yīnwèi zuò zài bǔguāng dēng qián shuìjiào, yìwài zǒu hóng, xiànzài yǒu wǔshí wàn fěnsī.",
                    "en": "The result: his cat went viral from sleeping in front of the ring lights, now with 500K followers.",
                },
                {
                    "cn": "小李∨每天帮猫拍视频、剪视频，成了全职猫奴。",
                    "py": "Xiǎo Lǐ měitiān bāng māo pāi shìpín, jiǎn shìpín, chéngle quánzhí māonú.",
                    "en": "Xiao Li films and edits for the cat every day — he became a full-time cat servant.",
                },
                {
                    "cn": "所以说，∨成为★网红★的秘诀∨到底是颜值还是努力？都不是——是你家∨有没有一只有缘分的猫。",
                    "py": "Suǒyǐ shuō, chénwéi wǎng hóng de mìjué dàodǐ shì yánzhí háishi nǔlì? Dōu bùshì—— shì nǐ jiā yǒu méiyǒu yī zhī yǒu yuánfèn de māo.",
                    "en": "So, the real secret to becoming a 网红 — looks or hard work? Neither. It's whether your cat has destiny.",
                },
            ],
        ],
    },
    {
        "word":    "绿茶",
        "slug":    "lu-cha",
        "pinyin":  "lǜ chá",
        "desc_en": "sweet but scheming",
        "search_query": "elegant woman drinking tea cafe portrait",
        "collage_images": [11, 12],
        "emoji":   "🍵",
        "para_labels": [
            "What is 绿茶?",
            "The new coworker Xiao Ya",
            "The year-end twist",
        ],
        "script": {
            "opening":
                "大家好！今天我们来学一个很有意思的词——绿茶！\n"
                "等等，不是你喝的那杯绿茶哦。\n"
                "绿，就是绿色；茶，就是茶叶。\n"
                "但是现在，绿茶常常用来形容一种人——表面清纯，其实心机很重。\n"
                "到底是什么样的人呢？我们一起来看看吧！",
            "p1_intro":
                "好，我们先来看第一段，搞清楚绿茶到底是什么意思。",
            "p1_s1_note":
                "\"A是什么\"，就是问A的意思。\n"
                "大家先猜猜看——这里的绿茶，指的是什么？",
            "p1_s2_note":
                "字面意思，就是文字表面的意思。\n"
                "形容，就是描述、表达某种样子。\n"
                "绿茶字面上是一种茶，但现在更多用来形容人。",
            "p1_s3_note":
                "表面上，就是从外表看起来。\n"
                "清纯善良，就是单纯又善良。\n"
                "心机，指心里的算计；心机很重，就是很会算计。\n"
                "表面清纯、其实心机重——这就是绿茶！",
            "p1_wrap":
                "好，第一段结束！\n"
                "我们知道了，绿茶就是表面清纯善良、其实心机很重的人。\n"
                "那这种人到底长什么样？我们来看一个故事——主人公小雅！",
            "p2_intro":
                "第二段，我们来认识办公室里的新同事，小雅。",
            "p2_s1_note":
                "办公室，就是上班工作的地方。\n"
                "新来了一个女生——故事开始了！",
            "p2_s2_note":
                "轻声细语，形容说话又轻又柔。\n"
                "\"这个我不会，你能教我吗？\"——是不是听起来很可爱、很无辜？\n"
                "注意这种说话方式，等一下你就明白了。",
            "p2_s3_note":
                "方案，就是计划、做事的办法。\n"
                "开会的时候说自己不会，但方案却总是最好的……\n"
                "大家有没有发现哪里不对劲？哈哈！",
            "p2_wrap":
                "第二段结束！\n"
                "小雅嘴上说什么都不会，但其实样样都行。\n"
                "那么到了年底，会发生什么呢？我们来看第三段！",
            "p3_intro":
                "第三段，揭晓答案的时刻到了！",
            "p3_s1_note":
                "年底，就是一年的最后。\n"
                "\"我什么都不懂，全靠大家帮忙～\"\n"
                "全靠，就是完全依靠。\n"
                "这句话，你是不是好像在哪里听过？哈哈！",
            "p3_s2_note":
                "升职，就是职位升高，比如从员工变成经理。\n"
                "说自己什么都不懂，结果升职的却是她——\n"
                "这就是绿茶的厉害之处！",
            "p3_s3_note":
                "装作，就是假装。\n"
                "所以绿茶不是不努力，而是一边努力，一边装作什么都不会。\n"
                "聪明？还是心机？大家自己判断吧，哈哈！",
            "p3_wrap":
                "第三段结束！\n"
                "小雅一边努力，一边装无辜，最后成了最大赢家。\n"
                "这，就是绿茶！好，我们来复习一下今天学的内容吧！",
            "closing":
                "好，今天我们学了绿茶这个词，还学了很多实用的表达：\n"
                "字面意思、形容、清纯善良、心机、装作……\n"
                "大家都记住了吗？\n"
                "下次遇到\"表面清纯、其实心机重\"的人，你就知道怎么形容了！\n"
                "如果觉得有帮助，请点赞订阅，我们下次见！再见！",
        },
        "paragraphs": [
            [
                {
                    "cn": "★绿茶★∨是什么？",
                    "py": "Lǜ chá shì shénme?",
                    "en": "What does 绿茶 mean?",
                },
                {
                    "cn": "字面意思∨是一种茶，∨但现在∨用来形容一种人。",
                    "py": "Zìmiàn yìsi shì yì zhǒng chá, dàn xiànzài yòng lái xíngróng yì zhǒng rén.",
                    "en": "Literally it's a kind of tea, but now it describes a kind of person.",
                },
                {
                    "cn": "表面上∨清纯善良，∨其实∨心机很重。",
                    "py": "Biǎomiàn shàng qīngchún shànliáng, qíshí xīnjī hěn zhòng.",
                    "en": "Sweet and innocent on the surface — but actually very calculating.",
                },
            ],
            [
                {
                    "cn": "办公室∨新来了一个女生，∨叫小雅。",
                    "py": "Bàngōngshì xīn láile yí gè nǚshēng, jiào Xiǎo Yǎ.",
                    "en": "A new girl named Xiao Ya joined the office.",
                },
                {
                    "cn": "她总是∨轻声细语，∨对每个男同事说：\"这个我不会，∨你能教我吗？\"",
                    "py": "Tā zǒngshì qīngshēng-xìyǔ, duì měi gè nán tóngshì shuō: \"Zhège wǒ bú huì, nǐ néng jiāo wǒ ma?\"",
                    "en": "She always speaks softly, telling every male coworker: \"I can't do this, can you teach me?\"",
                },
                {
                    "cn": "可是∨每次开会，∨她的方案∨总是最好的。",
                    "py": "Kěshì měi cì kāihuì, tā de fāng'àn zǒngshì zuì hǎo de.",
                    "en": "But every meeting, her proposal is always the best one.",
                },
            ],
            [
                {
                    "cn": "年底∨她对老板说：\"我什么都不懂，∨全靠大家帮忙～\"",
                    "py": "Niándǐ tā duì lǎobǎn shuō: \"Wǒ shénme dōu bù dǒng, quán kào dàjiā bāngmáng~\"",
                    "en": "At year-end she told the boss: \"I don't understand anything, it's all thanks to everyone~\"",
                },
                {
                    "cn": "结果∨升职的，∨是她。",
                    "py": "Jiéguǒ shēngzhí de, shì tā.",
                    "en": "The result? She's the one who got promoted.",
                },
                {
                    "cn": "所以说，∨★绿茶★不是不努力——∨而是一边努力，∨一边装作什么都不会。",
                    "py": "Suǒyǐ shuō, lǜ chá bú shì bù nǔlì—— érshì yìbiān nǔlì, yìbiān zhuāngzuò shénme dōu bú huì.",
                    "en": "So, a 绿茶 isn't lazy — she works hard while pretending she can't do anything.",
                },
            ],
        ],
    },
    {
        "word":    "内卷",
        "slug":    "nei-juan",
        "pinyin":  "nèi juǎn",
        "desc_en": "pointless rat-race competition",
        "search_query": "office workers overtime tired stress late night computer",
        "collage_images": [1, 11],
        "emoji":   "🌀",
        "para_labels": [
            "What is 内卷?",
            "The overtime spiral",
            "Everyone loses",
        ],
        "script": {
            "opening":
                "大家好！今天我们来学一个很流行的词——内卷！\n"
                "内，就是内部；卷，就是卷进去、绕进去。\n"
                "内卷，现在用来形容一种没有意义的竞争。\n"
                "大家一起拼命努力，最后却谁也没有变得更好。\n"
                "到底是什么意思呢？我们一起来看看吧！",
            "p1_intro":
                "好，我们先来看第一段，搞清楚内卷到底是什么。",
            "p1_s1_note":
                "\"A是什么\"，就是问A的意思。\n"
                "大家先想一想——内卷，指的是什么？",
            "p1_s2_note":
                "一起，就是大家同时；努力，就是很拼、很用功。\n"
                "好处，就是好的结果、得到的利益。\n"
                "大家一起努力，但谁也没得到好处——这就是内卷的关键！",
            "p1_s3_note":
                "这是一个很有名的比喻！\n"
                "看电影的时候，前面的人站起来，你也得站起来，\n"
                "结果大家都站着看，谁也没看得更清楚——这就是内卷！",
            "p1_wrap":
                "好，第一段结束！\n"
                "内卷，就是大家越来越拼，但结果谁也没变好。\n"
                "那这种事，在生活里是怎么发生的？我们来看小明的故事！",
            "p2_intro":
                "第二段，我们来看看小明公司里发生的事。",
            "p2_s1_note":
                "本来，就是原来、一开始。\n"
                "六点下班——多好啊！可是好景不长……",
            "p2_s2_note":
                "为了表现，就是为了让别人看到自己很努力。\n"
                "故意，就是特意、有意地。\n"
                "加班，就是下班时间还继续工作。",
            "p2_s3_note":
                "不敢，就是没有勇气做某事。\n"
                "一个人加班，结果第二天所有人都不敢走了——\n"
                "内卷，就是这样开始的。",
            "p2_wrap":
                "第二段结束！\n"
                "一个人加班，带动了全公司加班。\n"
                "那么最后结果怎么样呢？我们来看第三段！",
            "p3_intro":
                "第三段，看看内卷的最后结果！",
            "p3_s1_note":
                "半夜，就是深夜、很晚的时候。\n"
                "待到半夜——大家都在公司熬到半夜，是不是很夸张？",
            "p3_s2_note":
                "还是，表示情况没有改变。\n"
                "一分钱，形容很少的钱。\n"
                "累了半天，工作没变多，钱也没变多——太惨了！",
            "p3_s3_note":
                "越来越，表示程度不断加深。\n"
                "所以内卷的意思就是：大家越来越累，结果还是一样。\n"
                "听起来是不是很熟悉？哈哈！",
            "p3_wrap":
                "第三段结束！\n"
                "小明和同事们卷了半天，谁也没得到好处。\n"
                "这，就是内卷！好，我们来复习一下今天学的内容吧！",
            "closing":
                "好，今天我们学了内卷这个词，还学了很多实用的表达：\n"
                "努力、好处、故意、加班、越来越……\n"
                "大家都记住了吗？\n"
                "下次看到没有意义的竞争，你就可以说：这也太内卷了！\n"
                "如果觉得有帮助，请点赞订阅，我们下次见！再见！",
        },
        "paragraphs": [
            [
                {
                    "cn": "★内卷★∨是什么？",
                    "py": "Nèi juǎn shì shénme?",
                    "en": "What is 内卷?",
                },
                {
                    "cn": "简单来说，∨就是大家一起努力，∨但谁也没得到好处。",
                    "py": "Jiǎndān lái shuō, jiùshì dàjiā yìqǐ nǔlì, dàn shéi yě méi dédào hǎochù.",
                    "en": "Simply put, everyone works hard together, but no one gets any benefit.",
                },
                {
                    "cn": "就像看电影，∨前面的人∨站起来，∨后面的人∨也得站起来。",
                    "py": "Jiù xiàng kàn diànyǐng, qiánmiàn de rén zhàn qǐlái, hòumiàn de rén yě děi zhàn qǐlái.",
                    "en": "It's like at the movies: the person in front stands up, so everyone behind has to stand up too.",
                },
            ],
            [
                {
                    "cn": "小明的公司∨本来六点下班。",
                    "py": "Xiǎo Míng de gōngsī běnlái liù diǎn xiàbān.",
                    "en": "Xiao Ming's company originally finished work at six.",
                },
                {
                    "cn": "有一天，∨一个同事∨为了表现，∨故意加班到八点。",
                    "py": "Yǒu yìtiān, yí gè tóngshì wèile biǎoxiàn, gùyì jiābān dào bā diǎn.",
                    "en": "One day, a coworker, to show off, deliberately worked overtime until eight.",
                },
                {
                    "cn": "结果第二天，∨所有人∨都不敢走了。",
                    "py": "Jiéguǒ dì-èr tiān, suǒyǒu rén dōu bù gǎn zǒu le.",
                    "en": "As a result, the next day, no one dared to leave.",
                },
            ],
            [
                {
                    "cn": "一个星期后，∨大家都在公司∨待到半夜。",
                    "py": "Yí gè xīngqī hòu, dàjiā dōu zài gōngsī dāi dào bànyè.",
                    "en": "A week later, everyone stayed at the office until midnight.",
                },
                {
                    "cn": "可是工作∨还是那些工作，∨谁也没多赚一分钱。",
                    "py": "Kěshì gōngzuò háishi nàxiē gōngzuò, shéi yě méi duō zhuàn yì fēn qián.",
                    "en": "But the work was still the same work — no one earned a single cent more.",
                },
                {
                    "cn": "所以说，∨★内卷★就是——∨大家越来越累，∨结果还是一样。",
                    "py": "Suǒyǐ shuō, nèi juǎn jiùshì—— dàjiā yuè lái yuè lèi, jiéguǒ háishi yíyàng.",
                    "en": "So, 内卷 means: everyone gets more and more tired, but the result stays the same.",
                },
            ],
        ],
    },
    {
        "word":    "躺平",
        "slug":    "tang-ping",
        "pinyin":  "tǎng píng",
        "desc_en": "opting out of the rat race",
        "search_query": "young man relaxing lying on sofa grass hammock peaceful rest",
        "collage_images": [11, 12],
        "emoji":   "🛋️",
        "para_labels": [
            "What is 躺平?",
            "Xiao Wang gives up the grind",
            "Happier than ever",
        ],
        "script": {
            "opening":
                "大家好！今天我们来学一个超级火的词——躺平！\n"
                "躺，就是躺下来；平，就是平平的。\n"
                "合起来，躺平，字面意思就是平平地躺着。\n"
                "但现在，躺平用来形容一种生活态度——不拼了，不卷了，怎么舒服怎么来。\n"
                "到底是怎么回事呢？我们一起来看看吧！",
            "p1_intro":
                "好，我们先来看第一段，搞清楚躺平到底是什么意思。",
            "p1_s1_note":
                "想不想，就是把\"想\"说成\"想不想\"，用来问你\"要不要\"。\n"
                "比如：你想不想去？你吃不吃？很常用哦。\n"
                "那么——你想不想躺平呢？",
            "p1_s2_note":
                "字面意思，就是文字表面的意思。\n"
                "躺下来，平平地躺着——是不是很好懂？\n"
                "但躺平的真正意思，可不只是躺着哦。",
            "p1_s3_note":
                "不努力、不竞争，就是不再拼命、不跟别人比。\n"
                "怎么舒服怎么来，意思是：怎么舒服就怎么做。\n"
                "这就是躺平的态度——放轻松，别为难自己。",
            "p1_wrap":
                "好，第一段结束！\n"
                "躺平，就是不再拼命竞争，选择轻松的生活。\n"
                "那什么样的人会躺平呢？我们来看小王的故事！",
            "p2_intro":
                "第二段，我们来看看小王为什么决定躺平。",
            "p2_s1_note":
                "工作狂，就是特别拼、特别爱工作的人。\n"
                "加班到最晚，就是每天走得比谁都晚。\n"
                "以前的小王，就是这样一个人。",
            "p2_s2_note":
                "突然，就是一下子、没有预兆。\n"
                "拼了三年，工资还是老样子——\n"
                "老样子，就是没有变化。是不是有点扎心？",
            "p2_s3_note":
                "于是，就是所以、因此。\n"
                "不卷了！我要躺平！\n"
                "小王下定决心，不再跟别人比了。",
            "p2_wrap":
                "第二段结束！\n"
                "小王拼了三年，发现努力没有回报，于是决定躺平。\n"
                "那躺平以后，他过得怎么样呢？我们来看第三段！",
            "p3_intro":
                "第三段，看看躺平之后的小王！",
            "p3_s1_note":
                "准时，就是不早不晚、刚好那个时间。\n"
                "养花、遛狗、睡大觉——\n"
                "睡大觉，就是睡得又久又香。多舒服啊！",
            "p3_s2_note":
                "后悔，就是做了以后觉得不该做。\n"
                "同事担心他后悔，可小王却说——\n"
                "我从来没这么快乐过。是不是很治愈？",
            "p3_s3_note":
                "懒，就是不想动、不想做事。\n"
                "但躺平不是懒！\n"
                "而是不再为了别人的标准，把自己累坏。",
            "p3_wrap":
                "第三段结束！\n"
                "小王躺平以后，反而找到了快乐。\n"
                "这，就是躺平！好，我们来复习一下今天学的内容吧！",
            "closing":
                "好，今天我们学了躺平这个词，还学了很多实用的表达：\n"
                "工作狂、老样子、准时、后悔、睡大觉……\n"
                "大家都记住了吗？\n"
                "累的时候，别忘了：偶尔躺一下，也没关系。\n"
                "如果觉得有帮助，请点赞订阅，我们下次见！再见！",
        },
        "paragraphs": [
            [
                {
                    "cn": "你想不想∨★躺平★？",
                    "py": "Nǐ xiǎng bu xiǎng tǎng píng?",
                    "en": "Do you feel like lying flat (躺平)?",
                },
                {
                    "cn": "别急着回答，∨先看看字面意思：∨躺下来，平平地躺着。",
                    "py": "Bié jí zhe huídá, xiān kànkan zìmiàn yìsi: tǎng xiàlái, píngpíng de tǎng zhe.",
                    "en": "Don't rush to answer — first look at the literal meaning: lie down, lie flat.",
                },
                {
                    "cn": "但现在，∨躺平是指——∨不努力，不竞争，∨怎么舒服怎么来。",
                    "py": "Dàn xiànzài, tǎng píng shì zhǐ—— bù nǔlì, bù jìngzhēng, zěnme shūfu zěnme lái.",
                    "en": "But now, 躺平 means: no striving, no competing — just do whatever's most comfortable.",
                },
            ],
            [
                {
                    "cn": "小王∨以前是个工作狂，∨每天加班到最晚。",
                    "py": "Xiǎo Wáng yǐqián shì gè gōngzuòkuáng, měitiān jiābān dào zuì wǎn.",
                    "en": "Xiao Wang used to be a workaholic, working overtime the latest every day.",
                },
                {
                    "cn": "有一天，∨他突然发现——∨拼了三年，∨工资还是老样子。",
                    "py": "Yǒu yìtiān, tā tūrán fāxiàn—— pīn le sān nián, gōngzī háishì lǎo yàngzi.",
                    "en": "One day he suddenly realized — after grinding for three years, his salary was still the same.",
                },
                {
                    "cn": "于是他决定：∨不卷了，∨我要躺平！",
                    "py": "Yúshì tā juédìng: bù juǎn le, wǒ yào tǎng píng!",
                    "en": "So he decided: no more rat race — I'm going to lie flat!",
                },
            ],
            [
                {
                    "cn": "现在的小王，∨六点准时下班，∨回家养花、遛狗、睡大觉。",
                    "py": "Xiànzài de Xiǎo Wáng, liù diǎn zhǔnshí xiàbān, huí jiā yǎng huā, liù gǒu, shuì dà jiào.",
                    "en": "Now Xiao Wang clocks out at six sharp, goes home to grow flowers, walk the dog, and sleep in.",
                },
                {
                    "cn": "同事问他∨后不后悔，∨他笑着说：∨我从来没这么快乐过。",
                    "py": "Tóngshì wèn tā hòu bu hòuhuǐ, tā xiào zhe shuō: wǒ cónglái méi zhème kuàilè guò.",
                    "en": "When a coworker asked if he regretted it, he smiled: I've never been this happy.",
                },
                {
                    "cn": "所以说，∨★躺平★不是懒，∨而是——∨不再为了别人的标准，∨累坏自己。",
                    "py": "Suǒyǐ shuō, tǎng píng bú shì lǎn, érshì—— bú zài wèile biéren de biāozhǔn, lèi huài zìjǐ.",
                    "en": "So, 躺平 isn't laziness — it's refusing to wear yourself out for someone else's standards.",
                },
            ],
        ],
    },
    {
        "word":    "吃瓜",
        "slug":    "chi-gua",
        "pinyin":  "chī guā",
        "desc_en": "watching the drama unfold",
        "search_query": "watermelon slice summer eating fresh",
        "collage_images": [2, 11],
        "emoji":   "🍉",
        "para_labels": [
            "What is 吃瓜?",
            "Xiao Mei the gossip master",
            "The tables turn",
        ],
        "script": {
            "opening":
                "大家好！今天我们来学一个特别有意思的词——吃瓜！\n"
                "吃，就是吃东西；瓜，就是西瓜的瓜。\n"
                "但是吃瓜合在一起，意思可不是真的吃西瓜哦。\n"
                "现在，吃瓜用来形容——在旁边看热闹、看别人的八卦。\n"
                "到底是怎么回事呢？我们一起来看看吧！",
            "p1_intro":
                "好，我们先来看第一段，搞清楚吃瓜到底是什么意思。",
            "p1_s1_note":
                "最近你吃瓜了吗？就是问你——最近有没有看什么热闹、什么八卦？\n"
                "了吗，是一个很常用的问句结尾，表示\"有没有做\"。\n"
                "比如：你吃饭了吗？你睡了吗？",
            "p1_s2_note":
                "误会，就是理解错了。\n"
                "别误会——别理解错了！\n"
                "这里的瓜，不是真的西瓜，是一个比喻哦。",
            "p1_s3_note":
                "看热闹，就是在旁边看有意思的事。\n"
                "八卦，就是别人的私事、小道消息。\n"
                "在旁边看别人的八卦，这就是吃瓜！",
            "p1_wrap":
                "好，第一段结束！\n"
                "吃瓜，就是在旁边看热闹、看别人的八卦。\n"
                "那什么样的人最爱吃瓜呢？我们来看小美的故事！",
            "p2_intro":
                "第二段，我们来认识一位吃瓜高手——小美。",
            "p2_s1_note":
                "高手，就是特别厉害、特别在行的人。\n"
                "吃瓜高手，就是最会看热闹的人。\n"
                "小美，就是公司里的吃瓜第一名！",
            "p2_s2_note":
                "吵架，就是两个人争吵、闹矛盾。\n"
                "谈恋爱，就是两个人在一起、相爱。\n"
                "公司里的这些事，小美全都知道——真是消息灵通！",
            "p2_s3_note":
                "午休，就是中午休息的时间。\n"
                "板凳，就是小小的凳子。\n"
                "搬个小板凳准备吃瓜——这个画面，是不是特别生动？哈哈！",
            "p2_wrap":
                "第二段结束！\n"
                "小美是公司里的吃瓜高手，什么八卦都逃不过她。\n"
                "可是有一天，发生了一件意想不到的事……我们来看第三段！",
            "p3_intro":
                "第三段，剧情大反转！",
            "p3_s1_note":
                "围在一起，就是大家聚在一块儿。\n"
                "同事们围在一起吃瓜，聊得特别开心——\n"
                "看起来，今天的瓜一定很大！",
            "p3_s2_note":
                "凑过去，就是靠近、走过去。\n"
                "原来，表示发现了真相。\n"
                "主角是她自己——大家聊的八卦，主角竟然就是小美！哈哈，太尴尬了！",
            "p3_s3_note":
                "一时爽，就是那一下子很舒服、很痛快。\n"
                "变成别人的瓜，就是变成别人议论的对象。\n"
                "所以吃瓜的时候，也要小心——说不定哪天，你也会变成别人的瓜！",
            "p3_wrap":
                "第三段结束！\n"
                "爱吃瓜的小美，最后自己变成了那个大瓜。\n"
                "这，就是吃瓜！好，我们来复习一下今天学的内容吧！",
            "closing":
                "好，今天我们学了吃瓜这个词，还学了很多实用的表达：\n"
                "看热闹、八卦、高手、吵架、谈恋爱……\n"
                "大家都记住了吗？\n"
                "下次和朋友聊天，看到有热闹，你就可以说：走，吃瓜去！\n"
                "如果觉得有帮助，请点赞订阅，我们下次见！再见！",
        },
        "paragraphs": [
            [
                {
                    "cn": "最近，∨你★吃瓜★了吗？",
                    "py": "Zuìjìn, nǐ chī guā le ma?",
                    "en": "Have you \"eaten melon\" lately?",
                },
                {
                    "cn": "别误会，∨这里的瓜，∨不是真的西瓜。",
                    "py": "Bié wùhuì, zhèlǐ de guā, bú shì zhēn de xīguā.",
                    "en": "Don't get me wrong — the melon here isn't a real watermelon.",
                },
                {
                    "cn": "★吃瓜★，∨是指在旁边看热闹，∨看别人的八卦。",
                    "py": "Chī guā, shì zhǐ zài pángbiān kàn rènao, kàn biéren de bāguà.",
                    "en": "吃瓜 means watching the excitement from the sidelines — following other people's gossip.",
                },
            ],
            [
                {
                    "cn": "小美∨是公司里的\"★吃瓜★\"高手。",
                    "py": "Xiǎo Měi shì gōngsī lǐ de \"chī guā\" gāoshǒu.",
                    "en": "Xiao Mei is the office's \"melon-eating\" master.",
                },
                {
                    "cn": "谁和谁吵架了，∨谁又谈恋爱了，∨她全都知道。",
                    "py": "Shéi hé shéi chǎojià le, shéi yòu tán liàn'ài le, tā quándōu zhīdào.",
                    "en": "Who fought with whom, who started dating — she knows it all.",
                },
                {
                    "cn": "每天午休，∨她就搬个小板凳，∨准备\"★吃瓜★\"。",
                    "py": "Měitiān wǔxiū, tā jiù bān gè xiǎo bǎndèng, zhǔnbèi \"chī guā\".",
                    "en": "Every lunch break, she pulls up a little stool, ready to \"eat melon\".",
                },
            ],
            [
                {
                    "cn": "有一天，∨同事们围在一起吃瓜，∨聊得特别开心。",
                    "py": "Yǒu yìtiān, tóngshìmen wéi zài yìqǐ chī guā, liáo de tèbié kāixīn.",
                    "en": "One day, coworkers gathered around to eat melon, chatting away happily.",
                },
                {
                    "cn": "小美凑过去一听——∨原来大家聊的八卦，∨主角是她自己！",
                    "py": "Xiǎo Měi còu guòqù yì tīng—— yuánlái dàjiā liáo de bāguà, zhǔjué shì tā zìjǐ!",
                    "en": "Xiao Mei leaned in to listen — turns out the gossip everyone was sharing was about her!",
                },
                {
                    "cn": "所以说，∨★吃瓜★一时爽，∨但有时候，∨你也会变成别人的瓜。",
                    "py": "Suǒyǐ shuō, chī guā yìshí shuǎng, dàn yǒu shíhou, nǐ yě huì biànchéng biéren de guā.",
                    "en": "So, eating melon feels great for a moment — but sometimes, you become someone else's melon too.",
                },
            ],
        ],
    },
    {
        "word":    "画饼",
        "slug":    "hua-bing",
        "pinyin":  "huà bǐng",
        "desc_en": "making empty promises",
        "search_query": "pancake flatbread plate food fresh",
        "collage_images": [12, 11],
        "emoji":   "🫓",
        "para_labels": [
            "What is 画饼?",
            "Xiao Li's boss the 画饼 master",
            "The cake stays a cake",
        ],
        "script": {
            "opening":
                "大家好！今天我们来学一个特别实用的词——画饼！\n"
                "画，就是画画的画；饼，就是大饼的饼。\n"
                "但是画饼合在一起，意思可不是真的画一张饼哦。\n"
                "现在，画饼用来形容——用好听的承诺给你希望，却不兑现。\n"
                "到底是怎么回事呢？我们一起来看看吧！",
            "p1_intro":
                "好，我们先来看第一段，搞清楚画饼到底是什么意思。",
            "p1_s1_note":
                "老板，就是公司里的老大、你的上司。\n"
                "给你画饼，就是给你一个美好的承诺。\n"
                "有没有，是问句，问你\"是不是发生了\"。比如：你有没有吃饭？",
            "p1_s2_note":
                "误会，就是理解错了。\n"
                "别误会——别理解错了！\n"
                "这个饼是画出来的，看得到，吃不到。",
            "p1_s3_note":
                "承诺，就是答应你的话。\n"
                "美好的承诺，就是很好听、很吸引人的话。\n"
                "让你充满希望——听了以后，你觉得未来一片光明！",
            "p1_wrap":
                "好，第一段结束！\n"
                "画饼，就是用好听的承诺，让你充满希望。\n"
                "那什么样的人最爱画饼呢？我们来看小李的老板！",
            "p2_intro":
                "第二段，我们来认识一位画饼大师——小李的老板。",
            "p2_s1_note":
                "大师，就是特别厉害、特别在行的人。\n"
                "画饼大师，就是最会画饼的人。\n"
                "小李的老板，画起饼来，谁都比不过！",
            "p2_s2_note":
                "升职，就是职位往上升；加薪，就是工资增加。\n"
                "买房，就是买房子——这可是打工人最大的梦想。\n"
                "升职加薪、明年买房——这张饼，画得又大又香！",
            "p2_s3_note":
                "两眼放光，就是眼睛一下子亮了，特别激动。\n"
                "恨不得，就是非常想、迫不及待。\n"
                "恨不得天天住在公司——小李被这张饼，喂得干劲十足！",
            "p2_wrap":
                "第二段结束！\n"
                "小李听了老板的承诺，充满了希望。\n"
                "可是一年以后，会怎么样呢？我们来看第三段！",
            "p3_intro":
                "第三段，剧情大反转！",
            "p3_s1_note":
                "拼命，就是特别努力、不要命地干。\n"
                "加班，就是下班后还继续工作。\n"
                "天天加班干了一整年，小李盼的就是年底那一天！",
            "p3_s2_note":
                "拍拍肩，是一个亲切、又想安抚你的动作。\n"
                "\"今年公司不容易\"——这是画饼时最常见的借口。\n"
                "\"明年一定\"——去年也是这么说的呀！",
            "p3_s3_note":
                "终于明白，就是最后才想通。\n"
                "画得再大，也吃不到嘴里——\n"
                "饼画得越大，越好看，可就是一口都吃不着。这，就是画饼！",
            "p3_wrap":
                "第三段结束！\n"
                "老板画的饼，小李等了一年又一年，始终没吃到。\n"
                "这，就是画饼！好，我们来复习一下今天学的内容吧！",
            "closing":
                "好，今天我们学了画饼这个词，还学了很多实用的表达：\n"
                "承诺、升职、加薪、干劲……\n"
                "大家都记住了吗？\n"
                "下次老板又给你画饼，你心里就知道：哦，又是一张饼！\n"
                "如果觉得有帮助，请点赞订阅，我们下次见！再见！",
        },
        "paragraphs": [
            [
                {
                    "cn": "你的老板，∨最近有没有给你★画饼★？",
                    "py": "Nǐ de lǎobǎn, zuìjìn yǒu méiyǒu gěi nǐ huà bǐng?",
                    "en": "Has your boss been \"drawing you a cake\" lately?",
                },
                {
                    "cn": "别误会，∨这个饼，∨不能吃。",
                    "py": "Bié wùhuì, zhège bǐng, bù néng chī.",
                    "en": "Don't get me wrong — this cake, you can't eat.",
                },
                {
                    "cn": "★画饼★，∨是指用美好的承诺，∨让你充满希望。",
                    "py": "Huà bǐng, shì zhǐ yòng měihǎo de chéngnuò, ràng nǐ chōngmǎn xīwàng.",
                    "en": "画饼 means using beautiful promises to fill you with hope.",
                },
            ],
            [
                {
                    "cn": "小李刚进公司时，∨老板就是个\"★画饼★\"大师。",
                    "py": "Xiǎo Lǐ gāng jìn gōngsī shí, lǎobǎn jiùshì ge \"huà bǐng\" dàshī.",
                    "en": "When Xiao Li first joined, his boss was already a \"cake-drawing\" master.",
                },
                {
                    "cn": "\"好好干，∨年底升职加薪，∨明年还带你买房！\"",
                    "py": "\"Hǎohǎo gàn, niándǐ shēngzhí jiāxīn, míngnián hái dài nǐ mǎi fáng!\"",
                    "en": "\"Work hard — year-end promotion and a raise, and next year I'll help you buy a house!\"",
                },
                {
                    "cn": "小李听得两眼放光，∨恨不得天天住在公司。",
                    "py": "Xiǎo Lǐ tīng de liǎng yǎn fàngguāng, hènbudé tiāntiān zhù zài gōngsī.",
                    "en": "Xiao Li's eyes lit up — he could hardly wait to live at the office every day.",
                },
            ],
            [
                {
                    "cn": "他拼命干了一整年，∨天天加班，∨终于盼到了年底。",
                    "py": "Tā pīnmìng gànle yì zhěng nián, tiāntiān jiābān, zhōngyú pàn dàole niándǐ.",
                    "en": "He worked his hardest for a whole year, staying late every day, and finally the year-end he'd longed for arrived.",
                },
                {
                    "cn": "老板拍拍他的肩：∨\"今年公司不容易，∨明年一定给你升！\"",
                    "py": "Lǎobǎn pāipai tā de jiān: \"Jīnnián gōngsī bù róngyì, míngnián yídìng gěi nǐ shēng!\"",
                    "en": "The boss patted his shoulder: \"This year was tough for the company — next year I'll definitely promote you!\"",
                },
                {
                    "cn": "小李终于明白：∨那张\"★饼★\"画得再大，∨也永远吃不到嘴里。",
                    "py": "Xiǎo Lǐ zhōngyú míngbái: nà zhāng \"bǐng\" huà de zài dà, yě yǒngyuǎn chī bu dào zuǐlǐ.",
                    "en": "Xiao Li finally understood: no matter how big that \"cake\" is drawn, you'll never get to eat it.",
                },
            ],
        ],
    },
    {
        "word":    "破防",
        "slug":    "po-fang",
        "pinyin":  "pò fáng",
        "desc_en": "emotionally overwhelmed",
        "search_query": "man crying emotional tears portrait",
        "collage_images": [11, 12],
        "emoji":   "😭",
        "para_labels": [
            "What is 破防?",
            "Xiao Gang the tough guy",
            "One sentence breaks him",
        ],
        "script": {
            "opening":
                "大家好！今天我们来学一个很有感觉的词——破防！\n"
                "破，就是打破的破；防，就是防御的防。\n"
                "破防合在一起，本来是游戏里的词，意思是攻破了防御。\n"
                "现在，破防用来形容——心理防线被击穿，情绪一下子绷不住了。\n"
                "到底是怎么回事呢？我们一起来看看吧！",
            "p1_intro":
                "好，我们先来看第一段，搞清楚破防到底是什么意思。",
            "p1_s1_note":
                "有没有过，就是问你以前有没有发生过。\n"
                "突然，就是一下子、没有准备。\n"
                "突然破防——情绪一下子就上来了，你有过这种时候吗？",
            "p1_s2_note":
                "原来，表示这个词最早的来历。\n"
                "游戏里，攻破对方的防御，就叫破防。\n"
                "所以破防这个词，最早是从游戏里来的。",
            "p1_s3_note":
                "心理防线，就是我们心里那道\"我很坚强\"的墙。\n"
                "击穿，就是一下子打穿。\n"
                "绷不住，就是忍不住了——这就是破防！",
            "p1_wrap":
                "好，第一段结束！\n"
                "破防，就是心理防线被击穿，情绪绷不住了。\n"
                "那什么样的人最容易破防呢？我们来看小刚的故事！",
            "p2_intro":
                "第二段，我们来认识一个\"从不流泪\"的人——小刚。",
            "p2_s1_note":
                "一米八，就是身高一米八，很高。\n"
                "大个子，就是个子很高的人。\n"
                "从来不流泪——小刚看起来，是个特别坚强的人。",
            "p2_s2_note":
                "坚强，就是很勇敢、不容易被打倒。\n"
                "他常说：什么都不能让我破防。\n"
                "意思是——没有什么能让他掉眼泪。",
            "p2_s3_note":
                "直到，表示情况要发生变化了。\n"
                "有一天，他接到了妈妈的电话。\n"
                "接电话，就是拿起电话，和别人通话。",
            "p2_wrap":
                "第二段结束！\n"
                "小刚这么坚强，说什么都不能让他破防。\n"
                "可是这个电话，会发生什么呢？我们来看第三段！",
            "p3_intro":
                "第三段，剧情大反转！",
            "p3_s1_note":
                "只说了一句，就是简简单单一句话。\n"
                "天冷了，记得加衣服——这是妈妈最常说的话。\n"
                "加衣服，就是多穿一点，别冻着。",
            "p3_s2_note":
                "就这么简单的一句话，普普通通，一点都不特别。\n"
                "可小刚，突然就破防了。\n"
                "眼泪，一下子就忍不住了。",
            "p3_s3_note":
                "原来，表示他终于明白了。\n"
                "最坚强的人，也会被最普通的爱击穿。\n"
                "轻轻击穿——不用大事，一句关心，就够了。",
            "p3_wrap":
                "第三段结束！\n"
                "再坚强的小刚，也被妈妈一句话轻轻打动了。\n"
                "这，就是破防！好，我们来复习一下今天学的内容吧！",
            "closing":
                "好，今天我们学了破防这个词，还学了很多实用的表达：\n"
                "坚强、防线、情绪、加衣服……\n"
                "大家都记住了吗？\n"
                "下次看到特别感动的画面，你就可以说：我破防了！\n"
                "如果觉得有帮助，请点赞订阅，我们下次见！再见！",
        },
        "paragraphs": [
            [
                {
                    "cn": "你有没有过，∨突然★破防★的时候？",
                    "py": "Nǐ yǒu méiyǒu guò, tūrán pò fáng de shíhou?",
                    "en": "Have you ever suddenly \"broken down\"?",
                },
                {
                    "cn": "★破防★，∨原来是游戏里的词，∨意思是攻破了防御。",
                    "py": "Pò fáng, yuánlái shì yóuxì lǐ de cí, yìsi shì gōngpòle fángyù.",
                    "en": "破防 was originally a gaming word — it means breaking through someone's defenses.",
                },
                {
                    "cn": "现在，∨★破防★是指心理防线被击穿，∨情绪绷不住了。",
                    "py": "Xiànzài, pò fáng shì zhǐ xīnlǐ fángxiàn bèi jīchuān, qíngxù bēng bù zhù le.",
                    "en": "Now, 破防 means your emotional defenses are pierced, and your feelings can't hold back.",
                },
            ],
            [
                {
                    "cn": "小刚∨是个一米八的大个子，∨从来不流泪。",
                    "py": "Xiǎo Gāng shì ge yì mǐ bā de dà gèzi, cónglái bù liúlèi.",
                    "en": "Xiao Gang is a 1.8-meter-tall big guy who never cries.",
                },
                {
                    "cn": "他常说：∨\"我这么坚强，∨什么都不能让我★破防★。\"",
                    "py": "Tā cháng shuō: \"Wǒ zhème jiānqiáng, shénme dōu bùnéng ràng wǒ pò fáng.\"",
                    "en": "He often says: \"I'm so tough, nothing can make me break down.\"",
                },
                {
                    "cn": "直到有一天，∨他接到了妈妈的电话。",
                    "py": "Zhídào yǒu yìtiān, tā jiēdàole māma de diànhuà.",
                    "en": "Until one day, he got a phone call from his mom.",
                },
            ],
            [
                {
                    "cn": "妈妈只说了一句：∨\"天冷了，∨记得加衣服。\"",
                    "py": "Māma zhǐ shuōle yí jù: \"Tiān lěng le, jìde jiā yīfu.\"",
                    "en": "His mom said just one thing: \"It's getting cold — remember to wear more.\"",
                },
                {
                    "cn": "就这么简单的一句话，∨小刚突然就★破防★了。",
                    "py": "Jiù zhème jiǎndān de yí jù huà, Xiǎo Gāng tūrán jiù pò fáng le.",
                    "en": "Just this one simple sentence, and Xiao Gang suddenly broke down.",
                },
                {
                    "cn": "原来，∨最坚强的人，∨也会被最普通的爱∨轻轻击穿。",
                    "py": "Yuánlái, zuì jiānqiáng de rén, yě huì bèi zuì pǔtōng de ài qīngqīng jīchuān.",
                    "en": "It turns out, even the toughest person can be gently pierced by the most ordinary love.",
                },
            ],
        ],
    },
    {
        "word":    "显眼包",
        "slug":    "xian-yan-bao",
        "pinyin":  "xiǎn yǎn bāo",
        "desc_en": "the attention-grabber",
        "search_query": "colorful balloons party celebration crowd",
        "collage_images": [11, 12],
        "emoji":   "🤩",
        "para_labels": [
            "What is 显眼包?",
            "Xiao Pang the standout",
            "Not showing off — spreading joy",
        ],
        "script": {
            "opening":
                "大家好！今天我们来学一个特别可爱的词——显眼包！\n"
                "显眼，就是特别引人注意；包，是对某种人的可爱叫法。\n"
                "显眼包合在一起，可不是一个真的包哦。\n"
                "现在，显眼包用来形容——走到哪都要成为焦点的人。\n"
                "到底是怎么回事呢？我们一起来看看吧！",
            "p1_intro":
                "好，我们先来看第一段，搞清楚显眼包到底是什么意思。",
            "p1_s1_note":
                "不管在哪，就是无论在什么地方。\n"
                "学校、公司、朋友聚会……总有那么一个。\n"
                "想一想，你身边最爱表现的那个人，是谁呢？",
            "p1_s2_note":
                "显眼，就是特别引人注意、一眼就能看到。\n"
                "包，本来是包裹的包，这里是对某种人的可爱叫法。\n"
                "比如：淘气包、开心包——都是这么来的。",
            "p1_s3_note":
                "焦点，就是大家目光集中的地方。\n"
                "走到哪都要成为焦点——就是特别爱表现。\n"
                "这样的人，就是显眼包！",
            "p1_wrap":
                "好，第一段结束！\n"
                "显眼包，就是走到哪都要成为焦点的人。\n"
                "那谁是显眼包高手呢？我们来看小胖的故事！",
            "p2_intro":
                "第二段，我们来认识我朋友里的头号显眼包——小胖。",
            "p2_s1_note":
                "头号，就是第一名、最厉害的那个。\n"
                "在我们这群朋友里，小胖最爱抢镜。\n"
                "走到哪，他都是最热闹、最引人注意的那一个！",
            "p2_s2_note":
                "安安静静，就是很安静、不出声。\n"
                "比耶，就是拍照时手比出一个V。\n"
                "别人安静拍照，他偏要跳起来——这画面，太显眼了！",
            "p2_s3_note":
                "聚会，就是大家聚在一起玩。\n"
                "逗得全场哈哈大笑，就是把所有人都逗笑了。\n"
                "有小胖在，气氛永远不会冷——真是个开心果！",
            "p2_wrap":
                "第二段结束！\n"
                "小胖走到哪，哪里就最热闹、最显眼。\n"
                "可是，这样的显眼包，大家喜欢吗？我们来看第三段！",
            "p3_intro":
                "第三段，剧情大反转！",
            "p3_s1_note":
                "有人说，就是有一些人觉得。\n"
                "出风头，就是爱表现、爱抢镜。\n"
                "确实，有人觉得显眼包太爱出风头了。",
            "p3_s2_note":
                "气氛尴尬，就是场面很冷、大家都不说话。\n"
                "盼着，就是很期待、很希望。\n"
                "一到这种时候，大家反而都盼着小胖出现！",
            "p3_s3_note":
                "出风头，就是爱表现、爱抢镜。\n"
                "原来，表示大家终于明白了。\n"
                "显眼包不是为了自己出风头，是想让大家开心——这就是他的可爱！",
            "p3_wrap":
                "第三段结束！\n"
                "原来小胖的显眼，是想让大家开心。\n"
                "这，就是显眼包！好，我们来复习一下今天学的内容吧！",
            "closing":
                "好，今天我们学了显眼包这个词，还学了很多实用的表达：\n"
                "显眼、焦点、出风头、气氛……\n"
                "大家都记住了吗？\n"
                "下次看到那个最活跃、最爱表现的朋友，你就可以说：你真是个显眼包！\n"
                "如果觉得有帮助，请点赞订阅，我们下次见！再见！",
        },
        "paragraphs": [
            [
                {
                    "cn": "不管在哪，∨总有一个★显眼包★。",
                    "py": "Bùguǎn zài nǎ, zǒng yǒu yí ge xiǎn yǎn bāo.",
                    "en": "No matter where you are, there's always an \"attention-grabber\".",
                },
                {
                    "cn": "显眼，∨就是特别引人注意；∨包，∨是对某种人的可爱叫法。",
                    "py": "Xiǎn yǎn, jiùshì tèbié yǐn rén zhùyì; bāo, shì duì mǒu zhǒng rén de kě'ài jiàofǎ.",
                    "en": "显眼 means very eye-catching; 包 is a cute way to name a type of person.",
                },
                {
                    "cn": "★显眼包★，∨就是那个走到哪，∨都要成为焦点的人。",
                    "py": "Xiǎn yǎn bāo, jiùshì nà ge zǒu dào nǎ, dōu yào chéngwéi jiāodiǎn de rén.",
                    "en": "A 显眼包 is the one who becomes the center of attention wherever they go.",
                },
            ],
            [
                {
                    "cn": "我们这群朋友里，∨小胖就是头号★显眼包★。",
                    "py": "Wǒmen zhè qún péngyou lǐ, Xiǎo Pàng jiùshì tóuhào xiǎn yǎn bāo.",
                    "en": "In our group of friends, Xiao Pang is the number-one attention-grabber.",
                },
                {
                    "cn": "别人拍照都安安静静，∨他偏要跳起来比耶。",
                    "py": "Biéren pāizhào dōu ān'ānjìngjìng, tā piān yào tiào qǐlái bǐ yē.",
                    "en": "Others pose quietly for photos, but he insists on jumping up flashing a \"V\".",
                },
                {
                    "cn": "聚会上，∨他一个人∨就能逗得全场哈哈大笑。",
                    "py": "Jùhuì shàng, tā yí ge rén jiù néng dòude quánchǎng hāhā dàxiào.",
                    "en": "At a gathering, he alone can get the whole room laughing out loud.",
                },
            ],
            [
                {
                    "cn": "有人说，∨★显眼包★太爱出风头了。",
                    "py": "Yǒu rén shuō, xiǎn yǎn bāo tài ài chū fēngtóu le.",
                    "en": "Some say the 显眼包 loves the spotlight too much.",
                },
                {
                    "cn": "可是每次气氛尴尬，∨大家都盼着小胖出现。",
                    "py": "Kěshì měi cì qìfēn gāngà, dàjiā dōu pànzhe Xiǎo Pàng chūxiàn.",
                    "en": "But whenever the mood gets awkward, everyone hopes Xiao Pang will show up.",
                },
                {
                    "cn": "原来，∨★显眼包★不是爱出风头，∨是想让大家开心。",
                    "py": "Yuánlái, xiǎn yǎn bāo bú shì ài chū fēngtóu, shì xiǎng ràng dàjiā kāixīn.",
                    "en": "It turns out, the 显眼包 doesn't crave the spotlight — they just want to make everyone happy.",
                },
            ],
        ],
    },
    {
        "word":    "撒狗粮",
        "slug":    "sa-gou-liang",
        "pinyin":  "sā gǒu liáng",
        "desc_en": "couples flaunting their love",
        "search_query": "happy couple in love romantic",
        "collage_images": [11, 2],
        "emoji":   "🐶",
        "para_labels": [
            "What is 撒狗粮?",
            "A-Ming the single dog",
            "The tables turn",
        ],
        "script": {
            "opening":
                "大家好！今天我们来学一个特别有意思的词——撒狗粮！\n"
                "撒，就是撒东西的撒；狗粮，就是狗吃的粮食。\n"
                "但撒狗粮合在一起，可不是真的喂狗哦。\n"
                "现在，撒狗粮用来形容——情侣当众秀恩爱，让单身的人很\"受伤\"。\n"
                "到底是怎么回事呢？我们一起来看看吧！",
            "p1_intro":
                "好，我们先来看第一段，搞清楚撒狗粮到底是什么意思。",
            "p1_s1_note":
                "被，表示被别人怎么样了。\n"
                "你被撒狗粮了吗？就是问你——有没有被别人秀恩爱\"喂\"到？\n"
                "是不是很形象？我们接着看。",
            "p1_s2_note":
                "喂狗，就是给狗喂东西吃。\n"
                "当众，就是在大家面前；秀恩爱，就是故意表现两个人多相爱。\n"
                "情侣在大家面前秀恩爱，这就是撒狗粮！",
            "p1_s3_note":
                "单身，就是没有男朋友或女朋友。\n"
                "单身的人，常被开玩笑叫做\"单身狗\"。\n"
                "狗要吃狗粮，所以秀恩爱，就成了\"撒狗粮\"啦！哈哈！",
            "p1_wrap":
                "好，第一段结束！\n"
                "撒狗粮，就是情侣当众秀恩爱。\n"
                "那谁最爱撒狗粮，谁又是那只可怜的单身狗呢？我们来看阿明的故事！",
            "p2_intro":
                "第二段，我们来认识火锅局上唯一的单身狗——阿明。",
            "p2_s1_note":
                "火锅局，就是一群朋友一起吃火锅的聚会。\n"
                "唯一，就是只有这么一个。\n"
                "一桌人就他一个单身，阿明这单身狗，当得太不容易了！",
            "p2_s2_note":
                "旁边，就是坐在他身边。\n"
                "那对情侣，就是那一对男女朋友。\n"
                "你喂我一口，我喂你一口——就在阿明眼前，甜到发齁！",
            "p2_s3_note":
                "夹起一片肉，就是用筷子夹起一片肉。\n"
                "默默，就是不出声、静静地。\n"
                "别人互相喂，阿明只能喂自己——这画面，太惨了！哈哈！",
            "p2_wrap":
                "第二段结束！\n"
                "一顿火锅，阿明被喂了满满一肚子狗粮。\n"
                "可是，故事会一直这样吗？我们来看第三段！",
            "p3_intro":
                "第三段，剧情大反转！",
            "p3_s1_note":
                "可是，表示情况要变了。\n"
                "带了个女孩来，就是带了女朋友一起来。\n"
                "这只单身狗阿明，终于脱单啦！",
            "p3_s2_note":
                "夹菜，就是给别人夹菜；盛汤，就是给别人盛汤。\n"
                "疯狂，就是特别夸张、停不下来。\n"
                "昨天还嫌弃别人，今天自己撒得比谁都欢！",
            "p3_s3_note":
                "嫌弃，就是看不上、觉得受不了。\n"
                "撒起来最狠，就是秀恩爱秀得最厉害。\n"
                "原来，最嫌弃狗粮的人，撒起来最狠——真是太真实了！哈哈！",
            "p3_wrap":
                "第三段结束！\n"
                "曾经的单身狗阿明，现在成了撒狗粮高手。\n"
                "这，就是撒狗粮！好，我们来复习一下今天学的内容吧！",
            "closing":
                "好，今天我们学了撒狗粮这个词，还学了很多实用的表达：\n"
                "单身狗、秀恩爱、火锅局、脱单……\n"
                "大家都记住了吗？\n"
                "下次看到情侣秀恩爱，你就可以说：哎呀，又被撒狗粮了！\n"
                "如果觉得有帮助，请点赞订阅，我们下次见！再见！",
        },
        "paragraphs": [
            [
                {
                    "cn": "你被★撒狗粮★了吗？",
                    "py": "Nǐ bèi sā gǒu liáng le ma?",
                    "en": "Have you been \"fed dog food\" lately?",
                },
                {
                    "cn": "★撒狗粮★，∨不是真的喂狗，∨是情侣当众秀恩爱。",
                    "py": "Sā gǒu liáng, bú shì zhēn de wèi gǒu, shì qínglǚ dāngzhòng xiù ēn'ài.",
                    "en": "撒狗粮 isn't really feeding dogs — it's couples flaunting their love in public.",
                },
                {
                    "cn": "因为单身的人，∨常被叫做\"单身狗\"呀！",
                    "py": "Yīnwèi dānshēn de rén, cháng bèi jiàozuò \"dānshēn gǒu\" ya!",
                    "en": "Because single people are often jokingly called \"single dogs\"!",
                },
            ],
            [
                {
                    "cn": "阿明，∨是我们火锅局上唯一的\"单身狗\"。",
                    "py": "Ā Míng, shì wǒmen huǒguō jú shàng wéiyī de \"dānshēn gǒu\".",
                    "en": "A-Ming is the only \"single dog\" at our hotpot night.",
                },
                {
                    "cn": "旁边那对情侣，∨你喂我一口，∨我喂你一口。",
                    "py": "Pángbiān nà duì qínglǚ, nǐ wèi wǒ yì kǒu, wǒ wèi nǐ yì kǒu.",
                    "en": "The couple beside him — you feed me a bite, I feed you a bite.",
                },
                {
                    "cn": "阿明夹起一片肉，∨只能默默喂给自己。",
                    "py": "Ā Míng jiā qǐ yí piàn ròu, zhǐ néng mòmò wèi gěi zìjǐ.",
                    "en": "A-Ming picks up a slice of meat, and can only quietly feed himself.",
                },
            ],
            [
                {
                    "cn": "可是这次火锅局，∨阿明带了个女孩来。",
                    "py": "Kěshì zhè cì huǒguō jú, Ā Míng dàile ge nǚhái lái.",
                    "en": "But at this hotpot night, A-Ming brought a girl along.",
                },
                {
                    "cn": "只见他忙着夹菜、盛汤，∨疯狂★撒狗粮★。",
                    "py": "Zhǐ jiàn tā mángzhe jiā cài, chéng tāng, fēngkuáng sā gǒu liáng.",
                    "en": "There he was, busily picking food and ladling soup — madly scattering dog food.",
                },
                {
                    "cn": "原来，∨最嫌弃狗粮的人，∨撒起来最狠。",
                    "py": "Yuánlái, zuì xiánqì gǒu liáng de rén, sā qǐlái zuì hěn.",
                    "en": "Turns out, the one who complained most about dog food scatters it the hardest.",
                },
            ],
        ],
    },
    {
        "word":    "智商税",
        "slug":    "zhi-shang-shui",
        "pinyin":  "zhì shāng shuì",
        "desc_en": "IQ tax - money wasted being gullible",
        "search_query": "online shopping",
        "collage_images": [1, 15],
        "emoji":   "🧾",
        "para_labels": [
            "What is 智商税?",
            "Xiao Mei's 2000-yuan gadget",
            "The tax gets passed on",
        ],
        "script": {
            "opening":
                "大家好！今天我们来学一个特别有意思的词——智商税！\n"
                "智商，就是一个人聪明的程度；税，就是交给国家的钱。\n"
                "但智商税合在一起，可不是真的要交税哦。\n"
                "现在，智商税用来形容——因为不懂、太容易相信，多花的那笔冤枉钱。\n"
                "到底是怎么回事呢？我们一起来看看吧！",
            "p1_intro":
                "好，我们先来看第一段，搞清楚智商税到底是什么意思。",
            "p1_s1_note":
                "交，就是交钱、交作业的交。\n"
                "你交过智商税吗？就是问你——有没有花过让自己后悔的钱？\n"
                "是不是有点扎心？我们接着看。",
            "p1_s2_note":
                "真的税，是交给国家的，比如买东西的时候要交的税。\n"
                "冤枉钱，就是本来不用花、白白花掉的钱。\n"
                "多花的那一部分，就是智商税！",
            "p1_s3_note":
                "值，就是值得、配得上这个价钱。\n"
                "还是，表示心里知道，但最后仍然这么做了。\n"
                "东西不值，你还是买了——这不就等于给自己的智商交税吗？哈哈！",
            "p1_wrap":
                "好，第一段结束！\n"
                "智商税，就是因为太容易相信，多花的那笔冤枉钱。\n"
                "那什么样的东西最爱收智商税呢？我们来看小美的故事！",
            "p2_intro":
                "第二段，我们来认识买了\"睡眠神器\"的小美。",
            "p2_s1_note":
                "神器，就是特别厉害、好像什么都能解决的东西。\n"
                "两千块，就是两千块钱，一点都不便宜吧？\n"
                "一个睡觉用的小东西，要两千块——听起来就不太对劲！",
            "p2_s2_note":
                "广告，就是商家用来宣传的话。\n"
                "戴上，就是把东西戴在身上。\n"
                "三分钟就能睡着？这话说得也太满了吧！",
            "p2_s3_note":
                "结果，表示事情和原来想的不一样。\n"
                "越……越……，表示一个变化带来另一个变化。\n"
                "越戴越精神——花两千块，买了个提神的东西，哈哈！",
            "p2_wrap":
                "第二段结束！\n"
                "两千块的睡眠神器，让小美越戴越睡不着。\n"
                "这笔智商税，交得太惨了。可是，故事还没完！我们来看第三段！",
            "p3_intro":
                "第三段，剧情大反转！",
            "p3_s1_note":
                "生气，就是不高兴、心里有火。\n"
                "挂到网上，就是放到网上去卖。\n"
                "把它挂到网上——这是把字句，表示把某个东西怎么样了，很常用哦！",
            "p3_s2_note":
                "没想到，表示结果完全出乎意料。\n"
                "买走了，就是买下来带走了。\n"
                "两千块买的东西，两千块又卖出去了——小美这一波不亏！",
            "p3_s3_note":
                "原来，表示突然明白了一件事。\n"
                "转手，就是转给别人、再卖出去。\n"
                "智商税不会消失，它只会换一个人来交——太真实了！哈哈！",
            "p3_wrap":
                "第三段结束！\n"
                "小美交的智商税，最后被别人接走了。\n"
                "这，就是智商税！好，我们来复习一下今天学的内容吧！",
            "closing":
                "好，今天我们学了智商税这个词，还学了很多实用的表达：\n"
                "冤枉钱、神器、越……越……、没想到、转手……\n"
                "大家都记住了吗？\n"
                "下次看到贵得离谱的东西，你就可以说：这不就是智商税吗！\n"
                "如果觉得有帮助，请点赞订阅，我们下次见！再见！",
        },
        "paragraphs": [
            [
                {
                    "cn": "你交过★智商税★吗？",
                    "py": "Nǐ jiāoguo zhì shāng shuì ma?",
                    "en": "Have you ever paid the \"IQ tax\"?",
                },
                {
                    "cn": "★智商税★，∨不是真的税，∨是你多花的冤枉钱。",
                    "py": "Zhì shāng shuì, bú shì zhēn de shuì, shì nǐ duō huā de yuānwang qián.",
                    "en": "智商税 isn't a real tax — it's the extra money you wasted.",
                },
                {
                    "cn": "东西不值那个价，∨你还是买了，∨这就是给智商交税。",
                    "py": "Dōngxi bù zhí nàge jià, nǐ háishi mǎi le, zhè jiù shì gěi zhìshāng jiāo shuì.",
                    "en": "The thing isn't worth the price, but you bought it anyway — that's paying tax on your own IQ.",
                },
            ],
            [
                {
                    "cn": "小美买了一个\"睡眠神器\"，∨花了两千块。",
                    "py": "Xiǎo Měi mǎi le yí ge \"shuìmián shénqì\", huā le liǎng qiān kuài.",
                    "en": "Xiao Mei bought a \"magic sleep gadget\" for two thousand yuan.",
                },
                {
                    "cn": "广告说，∨戴上它，∨三分钟就能睡着。",
                    "py": "Guǎnggào shuō, dài shàng tā, sān fēnzhōng jiù néng shuìzháo.",
                    "en": "The ad said: put it on and you'll fall asleep in three minutes.",
                },
                {
                    "cn": "结果她戴上以后，∨越戴越精神。",
                    "py": "Jiéguǒ tā dài shàng yǐhòu, yuè dài yuè jīngshen.",
                    "en": "But after she put it on, the longer she wore it the wider awake she got.",
                },
            ],
            [
                {
                    "cn": "小美很生气，∨决定把它挂到网上卖掉。",
                    "py": "Xiǎo Měi hěn shēngqì, juédìng bǎ tā guà dào wǎngshàng mài diào.",
                    "en": "Xiao Mei was furious and decided to list it online and sell it off.",
                },
                {
                    "cn": "没想到，∨真的有人花两千块买走了。",
                    "py": "Méi xiǎngdào, zhēn de yǒu rén huā liǎng qiān kuài mǎi zǒu le.",
                    "en": "To her surprise, someone really did pay two thousand and take it away.",
                },
                {
                    "cn": "小美笑了：∨原来★智商税★，∨是可以转手的。",
                    "py": "Xiǎo Měi xiào le: yuánlái zhì shāng shuì, shì kěyǐ zhuǎnshǒu de.",
                    "en": "Xiao Mei smiled: turns out the IQ tax can be passed on to someone else.",
                },
            ],
        ],
    },
    {
        "word":    "避雷",
        "slug":    "bi-lei",
        "pinyin":  "bì léi",
        "desc_en": "steer clear - a warning to others",
        "search_query": "restaurant food",
        "collage_images": [15, 11],
        "emoji":   "⚡",
        "para_labels": [
            "What is 避雷?",
            "Xiao Wang's bad dinner",
            "The warning backfires",
        ],
        "script": {
            "opening":
                "大家好！今天我们来学一个网上超常见的词——避雷！\n"
                "避，就是躲开；雷，本来是打雷的那个雷。\n"
                "可是在网上，\"雷\"说的是那些花了钱又后悔的东西。\n"
                "所以避雷，就是提醒大家：这个别买，这家别去！\n"
                "我们一起来看看吧！",
            "p1_intro":
                "好，我们先来看第一段，搞清楚避雷到底是什么意思。",
            "p1_s1_note":
                "听说过，就是听别人说起过。\n"
                "你听说过避雷吗？在点评、小红书上，天天都能看到这两个字。\n"
                "我们接着看，它到底是什么意思。",
            "p1_s2_note":
                "我们先说\"踩雷\"。踩，就是一脚踩下去；踩雷，就是踩到了雷。\n"
                "买到难吃的东西、去了很糟的店，我们就说：我踩雷了。\n"
                "比如：这家店我踩雷了；这个别买，我踩过雷。\n"
                "那避雷呢？避，就是躲开。\n"
                "自己踩过，所以提醒别人别踩——这就是避雷。\n"
                "踩雷是自己中招，避雷是提醒别人。",
            "p1_s3_note":
                "雷，就是让人后悔的东西——难吃的店、难看的剧、没用的东西。\n"
                "花了钱，又特别后悔——这就是雷。\n"
                "所以\"避雷\"这两个字，是真心话，也是好心。",
            "p1_wrap":
                "好，第一段结束！\n"
                "避雷，就是提醒别人别踩雷。\n"
                "那到底什么样的东西算雷呢？我们来看小王的故事！",
            "p2_intro":
                "第二段，我们来认识一个刚刚踩过雷的人——小王。",
            "p2_s1_note":
                "餐厅，就是吃饭的地方。\n"
                "照片拍得特别好看——注意这个\"得\"，用来说做得怎么样。\n"
                "拍得好看、说得好听、跑得快……都是这个用法。",
            "p2_s2_note":
                "一……就……，表示前面的事一发生，后面马上跟着发生。\n"
                "菜一上来，他就后悔了——中间几乎没有时间。\n"
                "这个句型特别常用！",
            "p2_s3_note":
                "默默，就是不出声、静静地。\n"
                "写下两个字——哪两个字？避雷。\n"
                "这两个字，是他今天最真诚的评价。哈哈！",
            "p2_wrap":
                "第二段结束！\n"
                "小王踩了雷，于是写下\"避雷\"两个字。\n"
                "可是接下来发生的事，完全出乎他的意料！我们来看第三段！",
            "p3_intro":
                "第三段，剧情大反转！",
            "p3_s1_note":
                "帖，就是网上发的帖子。\n"
                "一夜之间，就是一个晚上的时间，形容变化特别快。\n"
                "火了，就是突然变得特别受欢迎。\n"
                "避雷帖火了——这可不是小王想要的结果。",
            "p3_s2_note":
                "吓跑，就是被吓得跑掉、不敢来了。\n"
                "不但……反而……，表示结果和你以为的正好相反。\n"
                "比如：他不但不生气，反而笑了。\n"
                "好奇，就是很想知道。\n"
                "到底有多难吃——大家想知道的不是好不好吃，是有多难吃！",
            "p3_s3_note":
                "天天，就是每天；排队，就是排成一队等着。\n"
                "老板还想谢谢小王——为什么呢？\n"
                "因为这条避雷帖，等于给他做了一次免费广告。\n"
                "本来是劝退，结果成了宣传——太真实了！哈哈！",
            "p3_wrap":
                "第三段结束！\n"
                "小王的避雷帖，最后帮那家店招来了客人。\n"
                "这，就是避雷！好，我们来复习一下今天学的内容吧！",
            "closing":
                "好，今天我们学了避雷这个词，还学了很多实用的表达：\n"
                "踩雷、拍得好看、一……就……、火了、排队……\n"
                "大家都记住了吗？\n"
                "下次看到不靠谱的东西，你就可以说一句：避雷！\n"
                "如果觉得有帮助，请点赞订阅，我们下次见！再见！",
        },
        "paragraphs": [
            [
                {
                    "cn": "你听说过★避雷★吗？",
                    "py": "Nǐ tīngshuōguo bì léi ma?",
                    "en": "Have you heard of 避雷?",
                },
                {
                    "cn": "★避雷★，∨不是躲开打雷，∨是提醒别人别踩雷。",
                    "py": "Bì léi, bú shì duǒkāi dǎléi, shì tíxǐng biéren bié cǎi léi.",
                    "en": "避雷 isn't about dodging lightning — it's warning others not to get burned.",
                },
                {
                    "cn": "雷，∨就是那些花了钱、∨又特别后悔的东西。",
                    "py": "Léi, jiù shì nàxiē huā le qián, yòu tèbié hòuhuǐ de dōngxi.",
                    "en": "A 雷 is something you paid for and deeply regretted.",
                },
            ],
            [
                {
                    "cn": "小王看到一家餐厅，∨照片拍得特别好看。",
                    "py": "Xiǎo Wáng kàndào yì jiā cāntīng, zhàopiàn pāi de tèbié hǎokàn.",
                    "en": "Xiao Wang found a restaurant whose photos looked amazing.",
                },
                {
                    "cn": "可是菜一上来，∨他就后悔了。",
                    "py": "Kěshì cài yí shànglái, tā jiù hòuhuǐ le.",
                    "en": "But the moment the food arrived, he regretted it.",
                },
                {
                    "cn": "他默默拿出手机，∨写下两个字：★避雷★。",
                    "py": "Tā mòmò ná chū shǒujī, xiě xià liǎng ge zì: bì léi.",
                    "en": "He quietly took out his phone and wrote two words: steer clear.",
                },
            ],
            [
                {
                    "cn": "没想到，∨那条★避雷★帖，∨一夜之间火了。",
                    "py": "Méi xiǎngdào, nà tiáo bì léi tiě, yíyè zhījiān huǒ le.",
                    "en": "Unexpectedly, that warning post went viral overnight.",
                },
                {
                    "cn": "大家不但没被吓跑，∨反而更好奇了：∨到底有多难吃？",
                    "py": "Dàjiā búdàn méi bèi xiàpǎo, fǎn'ér gèng hàoqí le: dàodǐ yǒu duō nán chī?",
                    "en": "Instead of being scared off, everyone got even more curious — exactly how bad is it?",
                },
                {
                    "cn": "现在那家店天天排队，∨老板还想谢谢小王。",
                    "py": "Xiànzài nà jiā diàn tiāntiān páiduì, lǎobǎn hái xiǎng xièxie Xiǎo Wáng.",
                    "en": "Now that place has a line every day — and the owner wants to thank Xiao Wang.",
                },
            ],
        ],
    },
    {
        "word":    "恋爱脑",
        "slug":    "lian-ai-nao",
        "pinyin":  "liàn ài nǎo",
        "desc_en": "love brain - romance over everything",
        "search_query": "couple in love",
        "collage_images": [15, 16],
        "emoji":   "💘",
        "para_labels": [
            "What is 恋爱脑?",
            "Three hours of talking her down",
            "One phone call",
        ],
        "script": {
            "opening":
                "大家好！今天我们来学一个又好笑、又有点心疼的词——恋爱脑！\n"
                "恋爱，就是谈恋爱；脑，就是脑子。\n"
                "恋爱脑，就是一谈恋爱，脑子里就只剩下对方。\n"
                "朋友约你，你说没空；朋友劝你，你也听不进去。\n"
                "到底有多夸张呢？我们一起来看看吧！",
            "p1_intro":
                "好，我们先来看第一段，搞清楚恋爱脑到底是什么意思。",
            "p1_s1_note":
                "身边，就是你周围、你认识的人里面。\n"
                "你身边有恋爱脑吗？想一想你的朋友。\n"
                "……要是想不出来，那可能就是你自己哦。哈哈！",
            "p1_s2_note":
                "一……就……，表示前面的事一发生，后面马上跟着发生。\n"
                "一谈恋爱，脑子里就只剩下对方。\n"
                "剩下，就是别的都没有了，只留下这一个。\n"
                "对方，就是另外那个人，这里指男朋友或者女朋友。",
            "p1_s3_note":
                "排在后面，就是位置往后放，变得不重要了。\n"
                "朋友、工作、自己，全都排在后面——\n"
                "最重要的那个位置，只留给一个人。\n"
                "这就是恋爱脑。",
            "p1_wrap":
                "好，第一段结束！\n"
                "恋爱脑，就是脑子里只剩下对方。\n"
                "那到底能夸张到什么程度呢？\n"
                "我给大家讲一个我闺蜜的故事——",
            "p2_intro":
                "第二段，我们来认识我的闺蜜——小林。",
            "p2_s1_note":
                "闺蜜，就是关系特别好的女性朋友，什么话都能说的那种。\n"
                "标准的，就是特别典型、一点都不夸张。\n"
                "标准的恋爱脑——这个评价，可不是随便给的。",
            "p2_s2_note":
                "吵架，就是两个人闹得很不愉快，大声地争。\n"
                "哭着说——注意这个\"着\"，表示一边哭，一边说。\n"
                "笑着回答、跑着过来，都是这个用法。\n"
                "一定要分手——听起来特别坚决，对吧？",
            "p2_s3_note":
                "劝，就是希望别人别这么做、听自己的话。\n"
                "劝了她三个小时——\"了三个小时\"放在后面，表示做了多长时间。\n"
                "嘴都说干了，就是话说得太多，嘴巴都干了。\n"
                "这是中文里特别形象的说法。",
            "p2_wrap":
                "第二段结束！\n"
                "闺蜜哭着要分手，我劝了整整三个小时。\n"
                "眼看就要劝好了……我们来看第三段！",
            "p3_intro":
                "第三段。接下来发生的一件小事，让我那三个小时，全白说了。",
            "p3_s1_note":
                "正，表示动作正在进行。\n"
                "说到一半，就是话才说了一半，还没说完。\n"
                "我正说到一半——最关键的时候，电话来了。\n"
                "大家猜猜，接下来会发生什么？",
            "p3_s2_note":
                "接起电话，就是拿起电话开始通话。\n"
                "一下子，表示变化非常快，就在一瞬间。\n"
                "声音一下子就变甜了——刚才还在哭，现在声音甜得不行。\n"
                "恋爱脑的变脸速度，就是这么快。",
            "p3_s3_note":
                "和好，就是吵架以后又变回好情侣。\n"
                "你别生气啊——注意，这句话是对我说的。\n"
                "我劝了三个小时，她和好只用了三分钟。\n"
                "最后还要反过来哄我——这就是恋爱脑！哈哈！",
            "p3_wrap":
                "第三段结束！\n"
                "三个小时的劝，输给了三分钟的电话。\n"
                "这，就是恋爱脑！好，我们来复习一下今天学的内容吧！",
            "closing":
                "好，今天我们学了恋爱脑这个词，还学了很多实用的表达：\n"
                "闺蜜、吵架、哭着说、劝、一下子、和好……\n"
                "大家都记住了吗？\n"
                "下次闺蜜哭着说要分手，你就知道了——先别急着劝。哈哈！\n"
                "如果觉得有帮助，请点赞订阅，我们下次见！再见！",
        },
        "paragraphs": [
            [
                {
                    "cn": "你身边有★恋爱脑★吗？",
                    "py": "Nǐ shēnbiān yǒu liàn ài nǎo ma?",
                    "en": "Is there a \"love brain\" in your life?",
                },
                {
                    "cn": "★恋爱脑★，∨就是一谈恋爱，∨脑子里就只剩下对方。",
                    "py": "Liàn ài nǎo, jiù shì yì tán liàn'ài, nǎozi lǐ jiù zhǐ shèngxià duìfāng.",
                    "en": "恋爱脑 means the moment you fall in love, there's nothing left in your head but them.",
                },
                {
                    "cn": "朋友、工作、自己，∨全都排在后面。",
                    "py": "Péngyou, gōngzuò, zìjǐ, quán dōu pái zài hòumiàn.",
                    "en": "Friends, work, yourself — all pushed to the back of the line.",
                },
            ],
            [
                {
                    "cn": "我的闺蜜小林，∨是个标准的★恋爱脑★。",
                    "py": "Wǒ de guīmì Xiǎo Lín, shì ge biāozhǔn de liàn ài nǎo.",
                    "en": "My best friend Xiao Lin is a textbook 恋爱脑.",
                },
                {
                    "cn": "昨天她和男朋友吵架，∨哭着说一定要分手。",
                    "py": "Zuótiān tā hé nán péngyou chǎojià, kūzhe shuō yídìng yào fēnshǒu.",
                    "en": "Yesterday she fought with her boyfriend and said through tears that she'd definitely break up.",
                },
                {
                    "cn": "我劝了她三个小时，∨嘴都说干了。",
                    "py": "Wǒ quàn le tā sān ge xiǎoshí, zuǐ dōu shuō gān le.",
                    "en": "I talked her through it for three hours, until my mouth went dry.",
                },
            ],
            [
                {
                    "cn": "我正说到一半，∨男朋友的电话来了。",
                    "py": "Wǒ zhèng shuō dào yíbàn, nán péngyou de diànhuà lái le.",
                    "en": "I was only halfway through when the boyfriend's call came in.",
                },
                {
                    "cn": "她接起电话，∨声音一下子就变甜了。",
                    "py": "Tā jiē qǐ diànhuà, shēngyīn yíxiàzi jiù biàn tián le.",
                    "en": "She picked up, and her voice turned sweet in an instant.",
                },
                {
                    "cn": "三分钟后她说：∨我们和好了，∨你别生气啊。",
                    "py": "Sān fēnzhōng hòu tā shuō: wǒmen héhǎo le, nǐ bié shēngqì a.",
                    "en": "Three minutes later she said: we made up — don't be mad, okay?",
                },
            ],
        ],
    },
    {
        "word":    "摸鱼",
        "slug":    "mo-yu",
        "pinyin":  "mō yú",
        "desc_en": "slacking off at work",
        "search_query": "office desk computer",
        "collage_images": [3, 7],
        "emoji":   "🐟",
        "para_labels": [
            "What is 摸鱼?",
            "Xiao Zhang, the master",
            "The boss has seen it too",
        ],
        "script": {
            "opening":
                "大家好！今天我们来学一个上班族最爱的词——摸鱼！\n"
                "摸，就是用手去摸；鱼，就是水里的鱼。\n"
                "可是摸鱼合在一起，跟钓鱼、抓鱼一点关系都没有。\n"
                "它说的是——上班的时候偷懒，看起来在忙，其实在玩。\n"
                "你今天摸鱼了吗？我们一起来看看吧！",
            "p1_intro":
                "好，我们先来看第一段，搞清楚摸鱼到底是什么意思。",
            "p1_s1_note":
                "摸鱼，在这里是一个动词，可以直接说：我今天摸鱼了。\n"
                "你今天摸鱼了吗？——这是上班族之间的暗号。哈哈！\n"
                "我们接着看，它到底是什么意思。",
            "p1_s2_note":
                "上班的时候，就是在工作的时间里。\n"
                "偷懒，就是该做的事不好好做，躲起来休息。\n"
                "所以摸鱼，不是真的去水里摸鱼，是在上班时间偷懒。",
            "p1_s3_note":
                "看起来，就是从外面看，好像是这样。\n"
                "其实，用来说出真实的情况。\n"
                "看起来……其实……，这两个词经常一起用，特别好用。\n"
                "一个字都没写——\"一……都没……\"表示完全没有、一点也没有。\n"
                "比如：一句话都没说、一口都没吃。",
            "p1_wrap":
                "好，第一段结束！\n"
                "摸鱼，就是上班的时候偷懒。\n"
                "那摸鱼的最高境界是什么样的呢？我们来看小张的故事！",
            "p2_intro":
                "第二段，我们来认识公司里的摸鱼高手——小张。",
            "p2_s1_note":
                "同事，就是在同一个公司上班的人。\n"
                "公认的，就是大家都同意、都这么认为。\n"
                "高手，就是某件事做得特别厉害的人。\n"
                "公认的摸鱼高手——这个称号，全公司都服气。哈哈！",
            "p2_s2_note":
                "永远，就是一直、从来都是这样。\n"
                "开着，表示窗口一直是打开的状态。\n"
                "窗口，就是电脑上打开的那个页面。\n"
                "一个表格，一个电视剧——一个给老板看，一个给自己看。\n"
                "这就是摸鱼的基本配置！",
            "p2_s3_note":
                "一过来，就是刚一走过来。\n"
                "不用看，就是连看都不用看。\n"
                "切回，就是换回到原来那一个。\n"
                "不用看就能切回表格——这已经不是技术了，这是本能。",
            "p2_wrap":
                "第二段结束！\n"
                "一个表格，一个电视剧，老板一来就切换。\n"
                "小张的摸鱼技术，堪称完美。\n"
                "可是昨天，他失手了。我们来看第三段！",
            "p3_intro":
                "第三段。小张的摸鱼生涯，昨天遇到了最大的一次考验。",
            "p3_s1_note":
                "正，表示动作正在进行。\n"
                "看得入迷，就是看得太投入，别的都忘了。\n"
                "注意这个\"得\"，用来说做到什么程度。\n"
                "悄悄，就是不出声、不让别人发现。\n"
                "一个看得入迷，一个悄悄靠近——危险！",
            "p3_s2_note":
                "吓得手都抖了——吓得，表示被吓到了什么程度。\n"
                "手都抖了，就是手一直在发抖。\n"
                "半天，在这里不是十二个小时，是\"很长时间\"的意思。\n"
                "半天没切换成功——越紧张，越切不回去。哈哈！",
            "p3_s3_note":
                "笑着说——注意这个\"着\"，表示一边笑，一边说。\n"
                "这集，就是电视剧的这一集。\n"
                "早看过了，就是很久以前就已经看过了。\n"
                "\"过\"表示以前有过这个经历：我看过、我去过、我吃过。\n"
                "老板早就看过了——那老板是什么时候看的呢？哈哈！",
            "p3_wrap":
                "第三段结束！\n"
                "小张以为自己被抓了，\n"
                "结果发现——老板早就看过那部剧了。\n"
                "原来公司里最大的摸鱼高手，是老板！\n"
                "好，我们来复习一下今天学的内容吧！",
            "closing":
                "好，今天我们学了摸鱼这个词，还学了很多实用的表达：\n"
                "偷懒、看起来……其实……、一……都没……、公认的、半天、早看过了……\n"
                "大家都记住了吗？\n"
                "不过要提醒一句：摸鱼可以，别被老板抓到哦。\n"
                "……当然，如果老板也在摸鱼，那就没事了。哈哈！\n"
                "如果觉得有帮助，请点赞订阅，我们下次见！再见！",
        },
        "paragraphs": [
            [
                {
                    "cn": "你今天★摸鱼★了吗？",
                    "py": "Nǐ jīntiān mō yú le ma?",
                    "en": "Did you slack off at work today?",
                },
                {
                    "cn": "★摸鱼★，∨不是真的去摸鱼，∨是上班的时候偷懒。",
                    "py": "Mō yú, bú shì zhēn de qù mō yú, shì shàngbān de shíhou tōulǎn.",
                    "en": "摸鱼 isn't really catching fish — it's goofing off on company time.",
                },
                {
                    "cn": "看起来在忙，∨其实一个字都没写。",
                    "py": "Kàn qǐlái zài máng, qíshí yí ge zì dōu méi xiě.",
                    "en": "Looks busy, but actually hasn't written a single word.",
                },
            ],
            [
                {
                    "cn": "我同事小张，∨是公司里公认的★摸鱼★高手。",
                    "py": "Wǒ tóngshì Xiǎo Zhāng, shì gōngsī lǐ gōngrèn de mō yú gāoshǒu.",
                    "en": "My coworker Xiao Zhang is the office's undisputed slacking-off champion.",
                },
                {
                    "cn": "他的电脑上永远开着两个窗口：∨一个表格，∨一个电视剧。",
                    "py": "Tā de diànnǎo shàng yǒngyuǎn kāizhe liǎng ge chuāngkǒu: yí ge biǎogé, yí ge diànshìjù.",
                    "en": "Two windows are always open on his computer: one spreadsheet, one TV drama.",
                },
                {
                    "cn": "老板一过来，∨他不用看就能切回表格。",
                    "py": "Lǎobǎn yí guòlái, tā bú yòng kàn jiù néng qiē huí biǎogé.",
                    "en": "The second the boss walks over, he can flip back to the spreadsheet without even looking.",
                },
            ],
            [
                {
                    "cn": "昨天下午，∨他正看得入迷，∨老板悄悄站到了他身后。",
                    "py": "Zuótiān xiàwǔ, tā zhèng kàn de rùmí, lǎobǎn qiāoqiāo zhàn dào le tā shēnhòu.",
                    "en": "Yesterday afternoon, he was completely absorbed — and the boss quietly came up behind him.",
                },
                {
                    "cn": "小张吓得手都抖了，∨半天没切换成功。",
                    "py": "Xiǎo Zhāng xià de shǒu dōu dǒu le, bàntiān méi qiēhuàn chénggōng.",
                    "en": "Xiao Zhang's hands shook so badly that he couldn't manage to switch for ages.",
                },
                {
                    "cn": "老板笑着说：∨这集我早看过了，∨结局挺好的。",
                    "py": "Lǎobǎn xiàozhe shuō: zhè jí wǒ zǎo kànguo le, jiéjú tǐng hǎo de.",
                    "en": "The boss said with a smile: I watched this episode ages ago — the ending's pretty good.",
                },
            ],
        ],
    },
    # 다음 에피소드는 여기에 추가
]

# ── Script & Metadata ──────────────────────────────────────────────────────

_CN_NUMS = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]

def _cn_clean(text: str) -> str:
    return text.replace("∨", "").replace("★", "")

def generate_script(ep_num: int, ep: dict) -> str:
    word, pinyin, desc_en = ep["word"], ep["pinyin"], ep["desc_en"]
    sc = ep.get("script", {})
    lines = []

    lines.append(f"# EP{ep_num:04d} 《{word}》 Script\n")
    lines.append(f"> Word: {word} ({pinyin}) = {desc_en}\n")
    lines.append("---\n")

    lines.append("## 🎬 Opening\n")
    lines.append("📌 `00_title.png`\n")
    lines.append(sc.get("opening",
        f"大家好！今天我们来学一个词——{word}！"))
    lines.append("\n---\n")

    n = 1
    for p_i, para in enumerate(ep["paragraphs"], 1):
        cn_num = _CN_NUMS[p_i - 1]
        lines.append(f"## 📖 第{cn_num}段\n")
        lines.append(f"📌 `{n:02d}_p{p_i}_sep.png`\n")
        lines.append(sc.get(f"p{p_i}_intro", f"好，我们来看第{cn_num}段。"))
        lines.append("\n\n---\n")
        n += 1

        for s_i, s in enumerate(para, 1):
            clean = _cn_clean(s["cn"])
            lines.append(f"### 句子 {p_i}-{s_i}（第一遍）\n")
            lines.append(f"📌 `{n:02d}_p{p_i}_s{s_i}.png`\n")
            lines.append(f"**{clean}**\n")
            note = sc.get(f"p{p_i}_s{s_i}_note", "")
            if note:
                lines.append(f"💡 {note}\n")
            lines.append(f"### 句子 {p_i}-{s_i}（第二遍）\n")
            lines.append(f"📌 `{n:02d}_p{p_i}_s{s_i}.png`\n")
            lines.append(f"好，我们再来一遍——**{clean}**\n")
            lines.append("---\n")
            n += 1

        lines.append(f"### 第{cn_num}段 全文\n")
        lines.append(f"📌 `{n:02d}_p{p_i}_full.png`\n")
        lines.append(sc.get(f"p{p_i}_wrap", f"好，我们把第{cn_num}段完整地读一遍。"))
        lines.append("\n\n---\n")
        n += 1

    lines.append("## 📚 复习\n")
    lines.append(f"📌 `{n:02d}_review_sep.png`\n")
    lines.append("好，现在我们来复习一下今天学的内容。\n")
    n += 1
    lines.append(f"📌 `{n:02d}_review_full.png`\n")
    lines.append(sc.get("closing",
        f"今天我们学了{word}这个词。大家都记住了吗？我们下次见！再见！"))

    return "\n".join(lines)


def generate_html(ep_num: int, ep: dict, has_collage: bool = False) -> str:
    word, pinyin, desc_en = ep["word"], ep["pinyin"], ep["desc_en"]
    sc = ep.get("script", {})

    def para_text(text: str) -> str:
        return "".join(f"<p>{line}</p>" for line in text.strip().split("\n") if line.strip())

    def card_block(png: str, badge: str, badge_class: str, narration: str, note: str = "") -> str:
        note_html = f'<div class="note">{para_text(note)}</div>' if note else ""
        return f"""
<div class="card-block">
  <div class="card-img-wrap">
    <img src="cards/{png}" alt="{png}">
    <span class="badge {badge_class}">{badge}</span>
  </div>
  <div class="narration">{para_text(narration)}{note_html}</div>
</div>"""

    blocks = []
    if has_collage:
        blocks.append(card_block("00b_collage.png", "Preview", "badge-open", ""))
    blocks.append(card_block("00_title.png", "Opening", "badge-open",
        sc.get("opening", f"大家好！今天我们来学一个词——{word}！")))

    n = 1
    for p_i, para in enumerate(ep["paragraphs"], 1):
        cn_num = _CN_NUMS[p_i - 1]
        blocks.append(f'<h2 class="section-title">第{cn_num}段</h2>')
        blocks.append(card_block(f"{n:02d}_p{p_i}_sep.png", f"第{cn_num}段", "badge-sec",
            sc.get(f"p{p_i}_intro", f"好，我们来看第{cn_num}段。")))
        n += 1

        for s_i, s in enumerate(para, 1):
            clean = _cn_clean(s["cn"])
            note = sc.get(f"p{p_i}_s{s_i}_note", "")
            blocks.append(card_block(f"{n:02d}_p{p_i}_s{s_i}.png",
                "第一遍", "badge-first",
                f"<strong>{clean}</strong>", note))
            blocks.append(card_block(f"{n:02d}_p{p_i}_s{s_i}.png",
                "第二遍", "badge-second",
                f"好，我们再来一遍——{clean}"))
            n += 1

        blocks.append(card_block(f"{n:02d}_p{p_i}_full.png", "全文", "badge-full",
            sc.get(f"p{p_i}_wrap", f"好，我们把第{cn_num}段完整地读一遍。")))
        n += 1

    blocks.append(f'<h2 class="section-title">复习</h2>')
    blocks.append(card_block(f"{n:02d}_review_sep.png", "复习", "badge-review",
        "好，现在我们来复习一下今天学的内容。"))
    n += 1
    for p_i in range(1, len(ep["paragraphs"]) + 1):
        blocks.append(card_block(f"{n:02d}_review_p{p_i}.png", f"复习 {p_i}", "badge-review",
            sc.get("closing", f"今天我们学了{word}。大家都记住了吗？我们下次见！再见！") if p_i == len(ep["paragraphs"]) else ""))
        n += 1

    body = "\n".join(blocks)

    return f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>EP{ep_num:04d} 《{word}》</title>
<style>
  :root {{
    --bg: #f0e4cc; --bg2: #e8d8b8; --ink: #2a1a0a;
    --mid: #6e4a26; --accent: #be501e; --card-shadow: rgba(0,0,0,.15);
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--ink); font-family: 'Noto Serif SC', serif;
         max-width: 960px; margin: 0 auto; padding: 24px 16px 64px; }}
  header {{ text-align: center; padding: 40px 0 32px; border-bottom: 2px solid var(--accent); margin-bottom: 32px; }}
  header .word {{ font-size: 3.5rem; font-weight: 700; color: var(--accent); letter-spacing: .05em; }}
  header .pinyin {{ font-size: 1.4rem; color: var(--mid); margin-top: 8px; }}
  header .desc {{ font-size: 1rem; color: var(--mid); margin-top: 6px; opacity: .8; }}
  .section-title {{ font-size: 1.6rem; color: var(--accent); margin: 40px 0 16px;
                    padding-bottom: 6px; border-bottom: 1px solid #c8a878; }}
  .card-block {{ display: flex; gap: 20px; background: var(--bg2); border-radius: 12px;
                 padding: 16px; margin-bottom: 16px; box-shadow: 0 2px 8px var(--card-shadow); }}
  .card-img-wrap {{ position: relative; flex-shrink: 0; width: 280px; }}
  .card-img-wrap img {{ width: 100%; border-radius: 8px; display: block; }}
  .badge {{ position: absolute; top: 8px; left: 8px; font-size: .72rem; font-weight: 700;
            padding: 3px 10px; border-radius: 20px; color: #fff; }}
  .badge-open   {{ background: #5a7a3a; }}
  .badge-sec    {{ background: #4a6090; }}
  .badge-first  {{ background: var(--accent); }}
  .badge-second {{ background: #7a5030; }}
  .badge-full   {{ background: #4a6090; }}
  .badge-review {{ background: #3a6060; }}
  .narration {{ flex: 1; display: flex; flex-direction: column; justify-content: center; gap: 8px;
               font-size: 1.25rem; line-height: 1.9; font-weight: 700; }}
  .narration p {{ margin: 0; }}
  .note {{ margin-top: 12px; padding: 10px 14px; background: rgba(0,0,0,.06);
           border-left: 3px solid var(--accent); border-radius: 4px;
           font-size: 1.05rem; color: var(--mid); font-weight: 600; }}
  @media (max-width: 600px) {{
    .card-block {{ flex-direction: column; }}
    .card-img-wrap {{ width: 100%; }}
  }}
</style>
</head>
<body>
<header>
  <div class="word">{word}</div>
  <div class="pinyin">{pinyin}</div>
  <div class="desc">{desc_en}</div>
</header>
{body}
</body>
</html>"""


def generate_script_html(ep_num: int, ep: dict, has_collage: bool = False) -> str:
    word, pinyin, desc_en = ep["word"], ep["pinyin"], ep["desc_en"]
    sc = ep.get("script", {})

    def block(badge: str, badge_cls: str, card_ref: str, narration: str, note: str = "") -> str:
        note_html = f'<div class="note">{note.replace(chr(10), "<br>")}</div>' if note else ""
        nar_html = narration.replace("\n", "<br>")
        return f"""<div class="block">
  <div class="meta"><span class="badge {badge_cls}">{badge}</span><span class="card-ref">📌 {card_ref}</span></div>
  <div class="narration">{nar_html}{note_html}</div>
  <button class="copy-btn" onclick="copyText(this)">복사</button>
</div>"""

    blocks = []
    if has_collage:
        blocks.append(block("Preview", "b-open", "00b_collage.png", ""))
    blocks.append(block("Opening", "b-open", "00_title.png",
        sc.get("opening", f"大家好！今天我们来学一个词——{word}！")))

    n = 1
    for p_i, para in enumerate(ep["paragraphs"], 1):
        cn_num = _CN_NUMS[p_i - 1]
        blocks.append(f'<h2 class="sec">第{cn_num}段</h2>')
        blocks.append(block(f"第{cn_num}段", "b-sec", f"{n:02d}_p{p_i}_sep.png",
            sc.get(f"p{p_i}_intro", f"好，我们来看第{cn_num}段。")))
        n += 1
        for s_i, s in enumerate(para, 1):
            clean = _cn_clean(s["cn"])
            note = sc.get(f"p{p_i}_s{s_i}_note", "")
            blocks.append(block("第一遍", "b-first", f"{n:02d}_p{p_i}_s{s_i}.png",
                clean, note))
            blocks.append(block("第二遍", "b-second", f"{n:02d}_p{p_i}_s{s_i}.png",
                f"好，我们再来一遍——{clean}"))
            n += 1
        blocks.append(block("全文", "b-full", f"{n:02d}_p{p_i}_full.png",
            sc.get(f"p{p_i}_wrap", f"好，我们把第{cn_num}段完整地读一遍。")))
        n += 1

    blocks.append('<h2 class="sec">复习</h2>')
    blocks.append(block("复习", "b-review", f"{n:02d}_review_sep.png",
        "好，现在我们来复习一下今天学的内容。"))
    n += 1
    for p_i in range(1, len(ep["paragraphs"]) + 1):
        blocks.append(block(f"复习 {p_i}", "b-review", f"{n:02d}_review_p{p_i}.png",
            sc.get("closing", f"今天我们学了{word}。大家都记住了吗？我们下次见！再见！") if p_i == len(ep["paragraphs"]) else ""))
        n += 1

    body = "\n".join(blocks)
    return f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>EP{ep_num:04d} {word} Script</title>
<style>
:root{{--bg:#f0e4cc;--bg2:#e8d8b8;--ink:#2a1a0a;--mid:#6e4a26;--acc:#be501e}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--ink);font-family:'Noto Serif SC',serif;max-width:860px;margin:0 auto;padding:24px 16px 64px}}
header{{text-align:center;padding:36px 0 28px;border-bottom:2px solid var(--acc);margin-bottom:28px}}
header .word{{font-size:3rem;font-weight:700;color:var(--acc)}}
header .pinyin{{font-size:1.3rem;color:var(--mid);margin-top:6px}}
header .desc{{font-size:.95rem;color:var(--mid);opacity:.8;margin-top:4px}}
.sec{{font-size:1.5rem;color:var(--acc);margin:36px 0 14px;padding-bottom:4px;border-bottom:1px solid #c8a878}}
.block{{background:var(--bg2);border-radius:10px;padding:14px 16px;margin-bottom:12px;position:relative}}
.meta{{display:flex;align-items:center;gap:10px;margin-bottom:8px}}
.badge{{font-size:.7rem;font-weight:700;padding:2px 9px;border-radius:20px;color:#fff}}
.b-open{{background:#5a7a3a}}.b-sec{{background:#4a6090}}
.b-first{{background:var(--acc)}}.b-second{{background:#7a5030}}
.b-full{{background:#4a6090}}.b-review{{background:#3a6060}}
.card-ref{{font-size:.8rem;color:var(--mid);opacity:.7}}
.narration{{font-size:1.05rem;line-height:1.85;white-space:pre-wrap}}
.note{{margin-top:10px;padding:8px 12px;background:rgba(0,0,0,.06);border-left:3px solid var(--acc);border-radius:4px;font-size:.9rem;color:var(--mid);white-space:pre-wrap}}
.copy-btn{{position:absolute;top:10px;right:12px;font-size:.75rem;padding:3px 10px;border:1px solid var(--acc);border-radius:6px;background:transparent;color:var(--acc);cursor:pointer}}
.copy-btn:active{{background:var(--acc);color:#fff}}
</style>
</head>
<body>
<header>
  <div class="word">{word}</div>
  <div class="pinyin">{pinyin}</div>
  <div class="desc">{desc_en}</div>
</header>
{body}
<script>
function copyText(btn){{
  const block=btn.closest('.block');
  const text=[...block.querySelectorAll('.narration,.note')].map(e=>e.innerText).join('\\n');
  navigator.clipboard.writeText(text).then(()=>{{btn.textContent='✓';setTimeout(()=>btn.textContent='복사',1500)}});
}}
</script>
</body>
</html>"""


# ── Reference image downloader ────────────────────────────────────────────

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

def download_ref_images(word: str, desc_en: str, ep_dir: str, count: int = 10, search_query: str = "") -> None:
    """Search Pixabay for copyright-free images and download to ep_dir/ref/."""
    import io

    ref_dir = os.path.join(ep_dir, "ref")
    os.makedirs(ref_dir, exist_ok=True)

    query = search_query if search_query else desc_en
    print(f"  Searching Pixabay: '{query}'")

    try:
        api_url = (
            f"https://pixabay.com/api/"
            f"?key={PIXABAY_API_KEY}"
            f"&q={requests.utils.quote(query)}"
            f"&image_type=photo"
            f"&per_page={min(count + 5, 50)}"
            f"&safesearch=true"
        )
        resp = requests.get(api_url, timeout=10, headers=_HEADERS)
        resp.raise_for_status()
        hits = resp.json().get("hits", [])
    except Exception as e:
        print(f"  [검색 실패] {e}")
        return

    downloaded = 0
    for hit in hits:
        if downloaded >= count:
            break
        url = hit.get("webformatURL", "")
        if not url:
            continue
        try:
            img_resp = requests.get(url, timeout=8, headers=_HEADERS)
            if img_resp.status_code != 200:
                continue
            data = img_resp.content
            Image.open(io.BytesIO(data)).verify()  # validate image
            fname = f"{downloaded + 1:02d}.jpg"
            fpath = os.path.join(ref_dir, fname)
            with open(fpath, "wb") as f:
                f.write(data)
            downloaded += 1
            tags = hit.get("tags", "")[:50]
            print(f"  ref/{fname}  [{tags}]")
        except Exception:
            continue

    print(f"  → ref/ : {downloaded}장 다운로드 완료 (Pixabay CC0)\n")


def _rounded_border(img: Image.Image, radius: int = 28, border: int = 10) -> Image.Image:
    """Apply rounded corners and a white border to an RGBA image."""
    w, h = img.size
    bw, bh = w + 2 * border, h + 2 * border

    bg = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bg)
    bd.rounded_rectangle([0, 0, bw - 1, bh - 1], radius=radius + border,
                         fill=(255, 255, 255, 255))

    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=255)

    rgba = img.convert("RGBA")
    rgba.putalpha(mask)
    bg.paste(rgba, (border, border), rgba)
    return bg


def _crop_to_ratio(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    iw, ih = img.size
    tr = target_w / target_h
    cr = iw / ih
    if cr > tr:
        nw = int(ih * tr)
        img = img.crop(((iw - nw) // 2, 0, (iw + nw) // 2, ih))
    else:
        nh = int(iw / tr)
        img = img.crop((0, (ih - nh) // 2, iw, (ih + nh) // 2))
    return img.resize((target_w, target_h), Image.LANCZOS)


def make_collage(image_paths: list[str], word: str, pinyin: str) -> Image.Image:
    """Make a collage card supporting 2–4 images with slight overlap and tilt."""
    canvas, _ = base()
    canvas = canvas.convert("RGBA")

    PAD     = 70
    LABEL_H = 100
    aw = W - 2 * PAD   # available width
    ah = H - 2 * PAD - LABEL_H  # available height
    n = min(len(image_paths), 4)

    # (center_x, center_y, cell_w, cell_h, angle_deg)
    if n == 2:
        cw = int(aw * 0.46); ch = int(ah * 0.82)
        offset_y = int(ah * 0.08)
        specs = [
            (W // 2 - int(cw * 0.47), PAD + ah // 2 - offset_y, cw, ch, -3),
            (W // 2 + int(cw * 0.47), PAD + ah // 2 + offset_y, cw, ch,  3),
        ]
    elif n == 3:
        cw_c = int(aw * 0.52); ch_c = int(ah * 0.88)
        cw_s = int(aw * 0.44); ch_s = int(ah * 0.78)
        specs = [
            (W // 2 - int(aw * 0.28), PAD + ah // 2, cw_s, ch_s, -7),
            (W // 2,                   PAD + ah // 2, cw_c, ch_c,  0),
            (W // 2 + int(aw * 0.28), PAD + ah // 2, cw_s, ch_s,  7),
        ]
    else:  # 4
        cw = int(aw * 0.52); ch = int(ah * 0.52)
        specs = [
            (W // 2 - int(cw * 0.30), PAD + int(ah * 0.28), cw, ch, -3),
            (W // 2 + int(cw * 0.30), PAD + int(ah * 0.28), cw, ch,  3),
            (W // 2 - int(cw * 0.30), PAD + int(ah * 0.72), cw, ch,  3),
            (W // 2 + int(cw * 0.30), PAD + int(ah * 0.72), cw, ch, -3),
        ]

    safe_top    = PAD // 2
    safe_bottom = H - PAD - LABEL_H - 15  # never let photo touch the label

    for path, (cx, cy, cw, ch, angle) in zip(image_paths[:n], specs):
        try:
            cell = Image.open(path).convert("RGBA")
            cell = _crop_to_ratio(cell, cw, ch)
            cell = _rounded_border(cell, radius=28, border=10)
            if angle:
                cell = cell.rotate(angle, expand=True, resample=Image.BICUBIC,
                                   fillcolor=(0, 0, 0, 0))
            lw, lh = cell.size
            px = cx - lw // 2
            py = cy - lh // 2
            # clamp: never below safe_bottom, never above safe_top
            py = max(safe_top, min(py, safe_bottom - lh))
            px = max(0, min(px, W - lw))
            # safe composite (handles edge pixels near boundary)
            sx0 = max(0, -px); sy0 = max(0, -py)
            sx1 = min(lw, W - px); sy1 = min(lh, H - py)
            if sx1 > sx0 and sy1 > sy0:
                canvas.alpha_composite(cell.crop((sx0, sy0, sx1, sy1)),
                                       (max(0, px), max(0, py)))
        except Exception:
            continue

    img = canvas.convert("RGB")
    draw = ImageDraw.Draw(img)

    # bottom word label with semi-transparent backing
    label_y = H - PAD - LABEL_H + 18
    wf = fnt_cn(52, bold=True)
    pf = fnt_cn(34, bold=True)
    total_w = tw(word, wf) + 20 + tw(pinyin, pf)
    lx = (W - total_w) // 2
    draw.text((lx, label_y), word, font=wf, fill=ACCENT)
    draw.text((lx + tw(word, wf) + 20, label_y + 10), pinyin, font=pf, fill=MID)

    return img


# ── Main ───────────────────────────────────────────────────────────────────

def generate_episode(ep_num: int, ep: dict) -> None:
    word = ep["word"]
    slug = ep.get("slug", word)
    ep_id  = f"ep{ep_num:04d}_{slug}"
    ep_dir = os.path.join(OUT_DIR, ep_id)
    cards_dir = os.path.join(ep_dir, "cards")
    os.makedirs(cards_dir, exist_ok=True)

    download_ref_images(ep["word"], ep["desc_en"], ep_dir,
                        search_query=ep.get("search_query", ""))

    cards: list[tuple[str, Image.Image]] = []
    meta_seq: list[dict] = []

    def add(name: str, img: Image.Image, entry: dict) -> None:
        cards.append((name, img))
        meta_seq.append({"file": f"cards/{name}.png", **entry})

    add("00_title", make_title(word, ep["pinyin"], ep["desc_en"]),
        {"type": "title", "repeat": 1})

    n = 1
    for p_i, para in enumerate(ep["paragraphs"], 1):
        add(f"{n:02d}_p{p_i}_sep", make_section(p_i),
            {"type": "section", "para": p_i, "repeat": 1})
        n += 1
        for s_i, s in enumerate(para, 1):
            add(f"{n:02d}_p{p_i}_s{s_i}",
                make_sentence(s["cn"], s["py"], s["en"], f"P{p_i}·{s_i}"),
                {"type": "sentence", "para": p_i, "sent": s_i, "repeat": 2,
                 "cn": _cn_clean(s["cn"]), "py": s["py"], "en": s["en"]})
            n += 1
        add(f"{n:02d}_p{p_i}_full",
            make_paragraph([s["cn"] for s in para], [s["py"] for s in para], f"P{p_i}"),
            {"type": "paragraph_full", "para": p_i, "repeat": 1})
        n += 1

    add(f"{n:02d}_review_sep", make_review_sep(),
        {"type": "review_sep", "repeat": 1})
    n += 1
    for p_i, para in enumerate(ep["paragraphs"], 1):
        add(f"{n:02d}_review_p{p_i}",
            make_review([[s["cn"] for s in para]]),
            {"type": "review_full", "para": p_i, "repeat": 1})
        n += 1

    for name, img in cards:
        path = os.path.join(cards_dir, f"{name}.png")
        img.save(path, "PNG")
        print(f"  {name}.png")

    # collage card from selected ref images
    has_collage = False
    collage_sel = ep.get("collage_images", [])
    if collage_sel:
        ref_dir = os.path.join(ep_dir, "ref")
        try:
            all_ref = sorted(f for f in os.listdir(ref_dir) if not f.startswith("."))
            paths = []
            for idx_1 in collage_sel:
                idx = idx_1 - 1
                if 0 <= idx < len(all_ref):
                    paths.append(os.path.join(ref_dir, all_ref[idx]))
            if paths:
                collage_img = make_collage(paths, ep["word"], ep["pinyin"])
                collage_img.save(os.path.join(cards_dir, "00b_collage.png"), "PNG")
                has_collage = True
                print("  00b_collage.png")
        except Exception as e:
            print(f"  [collage skip] {e}")

    meta = {
        "episode": ep_num, "id": ep_id,
        "word": word, "pinyin": ep["pinyin"], "desc_en": ep["desc_en"],
        "total_cards": len(cards),
        "sequence": meta_seq,
    }
    meta_path = os.path.join(ep_dir, "metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"  → {meta_path}")

    script_path = os.path.join(ep_dir, "script.md")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(generate_script(ep_num, ep))
    print(f"  → {script_path}")

    html_path = os.path.join(ep_dir, "index.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(generate_html(ep_num, ep, has_collage=has_collage))
    print(f"  → {html_path}")

    script_html_path = os.path.join(ep_dir, "script.html")
    with open(script_html_path, "w", encoding="utf-8") as f:
        f.write(generate_script_html(ep_num, ep, has_collage=has_collage))
    print(f"  → {script_html_path}\n")


def generate_collage_card(ep_num: int, ep: dict, selected: list[int]) -> None:
    """Generate collage card from selected ref image numbers (1-based).

    Example:
        generate_collage_card(1, EPISODES[0], selected=[2, 5, 7, 9])
    """
    slug  = ep.get("slug", ep["word"])
    ep_id = f"ep{ep_num:04d}_{slug}"
    ep_dir = os.path.join(OUT_DIR, ep_id)
    ref_dir = os.path.join(ep_dir, "ref")

    # resolve selected numbers to actual files
    all_ref = sorted(f for f in os.listdir(ref_dir) if not f.startswith("."))
    paths: list[str] = []
    for n in selected[:4]:
        idx = n - 1
        if 0 <= idx < len(all_ref):
            paths.append(os.path.join(ref_dir, all_ref[idx]))

    if len(paths) < 2:
        print("  [오류] ref/ 에서 최소 2장 이상 찾을 수 없습니다.")
        return

    img = make_collage(paths, ep["word"], ep["pinyin"])

    cards_dir = os.path.join(ep_dir, "cards")
    out_path  = os.path.join(cards_dir, "00b_collage.png")
    img.save(out_path, "PNG")
    print(f"  → {out_path}")


def main() -> None:
    for i, ep in enumerate(EPISODES, 1):
        print(f"[ep{i:04d}] {ep['word']}")
        generate_episode(i, ep)


if __name__ == "__main__":
    main()
