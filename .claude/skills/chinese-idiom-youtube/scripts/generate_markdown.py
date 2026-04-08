"""
generate_markdown.py — GitHub용 마크다운 스크립트 생성

Usage:
    python generate_markdown.py \
        --idiom "过眼云烟" \
        --pinyin "guò yǎn yún yān" \
        --episode 15 \
        --sections /tmp/sections.json \
        --output scripts/markdown/ep15_过眼云烟.md
"""

import argparse, json

OPENER = [
    {"cn": "大家好，欢迎来到小雪的中文屋。我是小雪，Snowy。",
     "py": "dàjiā hǎo, huānyíng lái dào xiǎo xuě de zhōngwén wū. wǒ shì Xiǎo Xuě, Snowy.",
     "en": "Hello everyone, welcome to Snowy's Chinese House. I'm Xiao Xue, Snowy."}
]
CLIP_CUE = [
    {"cn": "那么今天就教大家一个成语。我们还是先看一段影视片段。",
     "py": "nàme jīntiān jiù jiāo dàjiā yīgè chéngyǔ. wǒmen háishi xiān kàn yīduàn yǐngshì piànduàn.",
     "en": "So today let's learn a Chinese idiom. Let's first watch a short drama clip."}
]
CLOSER = [
    {"cn": "好了，今天就到这里。希望你学到了一点新的中文。",
     "py": "hǎo le, jīntiān jiù dào zhèlǐ. xīwàng nǐ xué dào le yīdiǎn xīn de zhōngwén.",
     "en": "That's all for today. I hope you learned something new in Chinese."},
    {"cn": "如果你喜欢我的内容，欢迎点赞加关注小雪的中文屋。我们下次再见！",
     "py": "rúguǒ nǐ xǐhuān wǒ de nèiróng, huānyíng diǎnzàn jiā guānzhù xiǎo xuě de zhōngwén wū. wǒmen xià cì zàijiàn!",
     "en": "If you enjoy my content, please like and subscribe to Snowy's Chinese House. See you next time!"}
]

def lower_first(s):
    return s[:1].lower() + s[1:] if s else s

def trilingual_block(lines):
    out = []
    for s in lines:
        cn = s.get("cn", "")
        py = lower_first(s.get("py", ""))
        en = s.get("en", "")
        out.append(f"**中文**\n```\n{cn}\n```")
        out.append(f"**拼音**\n```\n{py}\n```")
        out.append(f"**영어**\n```\n{en}\n```")
        out.append("")
    return "\n".join(out)

def build_md(idiom, pinyin, episode, s):
    lines = []

    # Header
    lines.append(f"# {idiom} · ep{episode:02d}")
    lines.append(f"> **{pinyin}**")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ① Opening
    lines.append("## ① 开场白")
    lines.append(trilingual_block(OPENER))
    lines.append(trilingual_block(s.get("opening_hook", [])))
    lines.append(trilingual_block(CLIP_CUE))
    lines.append("> 📽️ *【影视片段】*\n")

    # ② Intro
    lines.append("## ② 成语引出")
    intro = [
        {"cn": f"看完了片段，大家猜到今天的成语了吗？对，就是——{idiom}。{idiom}。{idiom}。",
         "py": "kàn wán le piànduàn, dàjiā cāi dào jīntiān de chéngyǔ le ma? duì, jiù shì——",
         "en": f"After watching, did everyone guess today's idiom? That's right — {idiom}."},
        {"cn": "我们还是先来分析一下每一个字的意思。",
         "py": "wǒmen háishi xiān lái fēnxī yīxià měi yīgè zì de yìsi.",
         "en": "Let's start by analysing the meaning of each character."}
    ]
    lines.append(trilingual_block(intro))

    # ③ Character analysis
    lines.append("## ③ 字义分析")
    for ca in s.get("char_analyses", []):
        lines.append(f"### 【{ca['char']} · {ca['pinyin']}】")
        lines.append(trilingual_block(ca.get("lines", [])))

    # ④ Combined meaning
    lines.append("## ④ 成语整体含义")
    lines.append(trilingual_block(s.get("combined_meaning", [])))
    if s.get("synonyms"):
        lines.append(trilingual_block(s["synonyms"]))

    # ⑤ Origin
    lines.append("## ⑤ 成语来源")
    meta = s.get("origin_meta", {})
    if meta:
        lines.append(f"> 📜 **{meta.get('author','')} · {meta.get('work','')}**\n")
    lines.append(trilingual_block(s.get("origin_lines", [])))
    lines.append(trilingual_block(s.get("origin_explanation", [])))

    # ⑥ Examples
    lines.append("## ⑥ 例句与片段回顾")
    for i, ex in enumerate(s.get("examples", []), 1):
        lines.append(f"**例句 {i}**")
        lines.append(trilingual_block(ex.get("lines", [])))
    revisit_cue = [
        {"cn": "那我们回头再来看一下开头的影视片段——",
         "py": "nà wǒmen huítóu zài lái kàn yīxià kāitóu de yǐngshì piànduàn——",
         "en": "Now let's go back and look at the opening drama clip again——"}
    ]
    lines.append(trilingual_block(revisit_cue))
    lines.append("> 📽️ *【影视片段回放】*\n")
    lines.append(trilingual_block(s.get("clip_revisit", [])))

    # ⑥-B Quiz
    quiz = s.get("quiz", [])
    if quiz:
        lines.append("## ⑥-B 填空练习")
        for i, q in enumerate(quiz, 1):
            lines.append(f"**Q{i}.** {q.get('q_cn', '')}")
            if q.get("q_en"):
                lines.append(f"*{q['q_en']}*")
            lines.append(f"✅ {q.get('full_cn', '')}")
            if q.get("full_en"):
                lines.append(f"*{q['full_en']}*")
            lines.append("")

    # ⑦ Usage
    lines.append("## ⑦ 使用注意")
    lines.append(trilingual_block(s.get("usage_note", [])))

    # ⑧ Closing
    lines.append("## ⑧ 结尾")
    lines.append(trilingual_block(s.get("closing_hint", [])))
    lines.append(trilingual_block(CLOSER))

    lines.append("---")
    lines.append("*✦ 小雪的中文屋 · Snowy's Chinese House ✦*")

    return "\n".join(lines)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--idiom",    required=True)
    p.add_argument("--pinyin",   required=True)
    p.add_argument("--episode",  type=int, default=0)
    p.add_argument("--sections", required=True)
    p.add_argument("--output",   required=True)
    args = p.parse_args()

    with open(args.sections, encoding="utf-8") as f:
        sections = json.load(f)

    md = build_md(args.idiom, args.pinyin, args.episode, sections)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"✅ Markdown saved: {args.output}")
