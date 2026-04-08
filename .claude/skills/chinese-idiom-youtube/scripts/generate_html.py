"""
generate_html.py — 복사 버튼이 있는 작업용 HTML 스크립트 생성

Usage:
    python generate_html.py \
        --idiom "过眼云烟" \
        --pinyin "guò yǎn yún yān" \
        --episode 15 \
        --sections /tmp/sections.json \
        --output scripts/html/ep15_过眼云烟.html
"""

import argparse, json, html as html_lib

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

def e(text):
    return html_lib.escape(str(text))

def trilingual_rows(lines):
    rows = []
    for s in lines:
        cn = e(s.get("cn", ""))
        py = e(lower_first(s.get("py", "")))
        en = e(s.get("en", ""))
        rows.append(f"""
        <div class="sentence">
          <div class="line cn">
            <span class="label">中文</span>
            <span class="text">{cn}</span>
            <button class="copy-btn" onclick="copyText(this, '{cn}')">복사</button>
          </div>
          <div class="line py">
            <span class="label">拼音</span>
            <span class="text">{py}</span>
            <button class="copy-btn" onclick="copyText(this, '{py}')">복사</button>
          </div>
          <div class="line en">
            <span class="label">영어</span>
            <span class="text">{en}</span>
            <button class="copy-btn" onclick="copyText(this, '{en}')">복사</button>
          </div>
        </div>""")
    return "\n".join(rows)

def section(title, content):
    return f"""
  <section>
    <h2>{e(title)}</h2>
    {content}
  </section>"""

def clip_marker(label="影视片段"):
    return f'<div class="clip-marker">📽️ 【{label}】</div>'

def build_html(idiom, pinyin, episode, s):
    # ── sections ────────────────────────────────────────────
    meta = s.get("origin_meta", {})
    origin_label = f"{meta.get('author','')} · {meta.get('work','')}" if meta else ""

    intro_lines = [
        {"cn": f"看完了片段，大家猜到今天的成语了吗？对，就是——{idiom}。{idiom}。{idiom}。",
         "py": "kàn wán le piànduàn, dàjiā cāi dào jīntiān de chéngyǔ le ma? duì, jiù shì——",
         "en": f"After watching, did everyone guess today's idiom? That's right — {idiom}."},
        {"cn": "我们还是先来分析一下每一个字的意思。",
         "py": "wǒmen háishi xiān lái fēnxī yīxià měi yīgè zì de yìsi.",
         "en": "Let's start by analysing the meaning of each character."}
    ]
    revisit_cue = [
        {"cn": "那我们回头再来看一下开头的影视片段——",
         "py": "nà wǒmen huítóu zài lái kàn yīxià kāitóu de yǐngshì piànduàn——",
         "en": "Now let's go back and look at the opening drama clip again——"}
    ]

    char_html = ""
    for ca in s.get("char_analyses", []):
        char_html += f'<h3 class="char-label">【{e(ca["char"])} · {e(ca["pinyin"])}】</h3>\n'
        char_html += trilingual_rows(ca.get("lines", []))

    examples_html = ""
    for i, ex in enumerate(s.get("examples", []), 1):
        examples_html += f'<p class="ex-label">例句 {i}</p>\n'
        examples_html += trilingual_rows(ex.get("lines", []))

    sections_html = "".join([
        section("① 开场白",
            trilingual_rows(OPENER) +
            trilingual_rows(s.get("opening_hook", [])) +
            trilingual_rows(CLIP_CUE) +
            clip_marker()),

        section("② 成语引出",
            trilingual_rows(intro_lines)),

        section("③ 字义分析", char_html),

        section("④ 成语整体含义",
            trilingual_rows(s.get("combined_meaning", [])) +
            trilingual_rows(s.get("synonyms", []))),

        section(f"⑤ 成语来源 — {origin_label}",
            trilingual_rows(s.get("origin_lines", [])) +
            trilingual_rows(s.get("origin_explanation", []))),

        section("⑥ 例句与片段回顾",
            examples_html +
            trilingual_rows(revisit_cue) +
            clip_marker("影视片段回放") +
            trilingual_rows(s.get("clip_revisit", []))),

        section("⑥-B 填空练习", "".join(
            f'<div class="quiz-item">'
            f'<p class="quiz-q"><span class="quiz-num">Q{i}.</span> {e(q.get("q_cn",""))}</p>'
            + (f'<p class="quiz-hint">{e(q.get("q_en",""))}</p>' if q.get("q_en") else "")
            + f'<p class="quiz-a">✅ {e(q.get("full_cn",""))}</p>'
            + (f'<p class="quiz-hint">{e(q.get("full_en",""))}</p>' if q.get("full_en") else "")
            + '</div>'
            for i, q in enumerate(s.get("quiz", []), 1)
        )) if s.get("quiz") else "",

        section("⑦ 使用注意",
            trilingual_rows(s.get("usage_note", []))),

        section("⑧ 结尾",
            trilingual_rows(s.get("closing_hint", [])) +
            trilingual_rows(CLOSER)),
    ])

    ep_str = f"ep{episode:02d} · " if episode else ""

    return f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{ep_str}{e(idiom)} · 小雪的中文屋</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', 'PingFang SC', sans-serif; background: #f5f7fa; color: #222; }}

  header {{
    background: linear-gradient(135deg, #1a5c9a, #2e86c1);
    color: white; padding: 28px 40px;
  }}
  header h1 {{ font-size: 2.4rem; letter-spacing: 4px; }}
  header .pinyin {{ font-size: 1.1rem; opacity: .8; margin-top: 4px; font-style: italic; }}
  header .meta {{ font-size: .85rem; opacity: .6; margin-top: 6px; }}

  main {{ max-width: 860px; margin: 32px auto; padding: 0 20px 60px; }}

  section {{ background: white; border-radius: 10px; padding: 24px 28px;
             margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,.07); }}
  h2 {{ font-size: 1.05rem; color: #1a5c9a; border-left: 4px solid #2e86c1;
        padding-left: 10px; margin-bottom: 16px; }}
  h3.char-label {{ font-size: 1rem; color: #e67e22; margin: 16px 0 8px; }}
  .ex-label {{ font-size: .9rem; font-weight: bold; color: #e67e22; margin: 14px 0 6px; }}

  .sentence {{ margin-bottom: 14px; }}
  .line {{ display: flex; align-items: baseline; gap: 10px; padding: 5px 0;
           border-bottom: 1px solid #f0f0f0; }}
  .line:last-child {{ border-bottom: none; }}

  .label {{ font-size: .72rem; font-weight: 700; width: 34px; flex-shrink: 0;
            padding: 2px 5px; border-radius: 4px; text-align: center; }}
  .cn .label {{ background: #dbeafe; color: #1e40af; }}
  .py .label {{ background: #ede9fe; color: #5b21b6; }}
  .en .label {{ background: #dcfce7; color: #166534; }}

  .text {{ flex: 1; font-size: .95rem; line-height: 1.5; }}
  .cn .text {{ font-size: 1.05rem; }}
  .py .text {{ font-style: italic; color: #555; font-size: .9rem; }}
  .en .text {{ color: #444; font-size: .9rem; }}

  .copy-btn {{
    flex-shrink: 0; font-size: .7rem; padding: 2px 8px;
    border: 1px solid #ddd; border-radius: 4px; background: #fafafa;
    cursor: pointer; color: #666; transition: all .15s;
  }}
  .copy-btn:hover {{ background: #2e86c1; color: white; border-color: #2e86c1; }}
  .copy-btn.copied {{ background: #22c55e; color: white; border-color: #22c55e; }}

  .quiz-item {{ border-left: 3px solid #2e86c1; padding: 10px 14px; margin-bottom: 14px; background: #f8faff; border-radius: 0 6px 6px 0; }}
  .quiz-q {{ font-size: 1.05rem; margin-bottom: 4px; }}
  .quiz-num {{ font-weight: 700; color: #2e86c1; margin-right: 6px; }}
  .quiz-a {{ font-size: 1rem; color: #166534; font-weight: 600; margin-top: 6px; }}
  .quiz-hint {{ font-size: .85rem; color: #888; font-style: italic; margin: 2px 0; }}

  .clip-marker {{
    background: #fff7ed; border: 1px dashed #f97316;
    border-radius: 6px; padding: 8px 14px;
    color: #c2410c; font-size: .9rem; margin: 10px 0;
  }}

  footer {{ text-align: center; font-size: .8rem; color: #aaa; margin-top: 40px; }}
</style>
</head>
<body>
<header>
  <h1>{e(idiom)}</h1>
  <div class="pinyin">{e(pinyin)}</div>
  <div class="meta">{ep_str}小雪的中文屋 · Snowy's Chinese House</div>
</header>
<main>
{sections_html}
</main>
<footer>✦ 小雪的中文屋 · Snowy's Chinese House ✦</footer>

<script>
function copyText(btn, text) {{
  // unescape HTML entities
  const ta = document.createElement('textarea');
  ta.innerHTML = text;
  const decoded = ta.value;
  navigator.clipboard.writeText(decoded).then(() => {{
    btn.textContent = '✓';
    btn.classList.add('copied');
    setTimeout(() => {{ btn.textContent = '복사'; btn.classList.remove('copied'); }}, 1500);
  }});
}}
</script>
</body>
</html>"""

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

    html_out = build_html(args.idiom, args.pinyin, args.episode, sections)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html_out)
    print(f"✅ HTML saved: {args.output}")
