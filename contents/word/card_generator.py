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
    v_shift = (th(cn_size) - th(v_size)) // 2
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
    return lines

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


def generate_html(ep_num: int, ep: dict) -> str:
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
                f"**{clean}**", note))
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
    blocks.append(card_block(f"{n:02d}_review_full.png", "全文复习", "badge-review",
        sc.get("closing", f"今天我们学了{word}。大家都记住了吗？我们下次见！再见！")))

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
               font-size: 1rem; line-height: 1.8; }}
  .narration p {{ margin: 0; }}
  .note {{ margin-top: 12px; padding: 10px 14px; background: rgba(0,0,0,.06);
           border-left: 3px solid var(--accent); border-radius: 4px;
           font-size: .9rem; color: var(--mid); }}
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


def generate_script_html(ep_num: int, ep: dict) -> str:
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

    blocks = [block("Opening", "b-open", "00_title.png",
        sc.get("opening", f"大家好！今天我们来学一个词——{word}！"))]

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


# ── Main ───────────────────────────────────────────────────────────────────

def generate_episode(ep_num: int, ep: dict) -> None:
    word = ep["word"]
    slug = ep.get("slug", word)
    ep_id  = f"ep{ep_num:04d}_{slug}"
    ep_dir = os.path.join(OUT_DIR, ep_id)
    cards_dir = os.path.join(ep_dir, "cards")
    os.makedirs(cards_dir, exist_ok=True)

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
        f.write(generate_html(ep_num, ep))
    print(f"  → {html_path}")

    script_html_path = os.path.join(ep_dir, "script.html")
    with open(script_html_path, "w", encoding="utf-8") as f:
        f.write(generate_script_html(ep_num, ep))
    print(f"  → {script_html_path}\n")


def main() -> None:
    for i, ep in enumerate(EPISODES, 1):
        print(f"[ep{i:04d}] {ep['word']}")
        generate_episode(i, ep)


if __name__ == "__main__":
    main()
