---
name: chinese-idiom-youtube
description: >
  YouTube content package generator for 小雪的中文屋 (Snowy's Chinese House) —
  a Chinese idiom education channel. Use this skill whenever the user mentions
  a Chinese idiom (成语/사자성어), asks to create a video script, or wants to
  generate channel content. Given any 4-character Chinese idiom, produces:
  (1) a complete Chinese-language video script (.docx) following the channel's
  8-step format, and (2) a full set of images — title card, 4 character cards,
  meaning infographic, and YouTube thumbnail. Always invoke this skill when the
  user asks to create content for their YouTube channel, even if they just say
  "다음 영상 만들어줘" or mention an idiom without specifying output type.
---

# 小雪的中文屋 — YouTube Content Generator

## What this skill produces

For any Chinese 4-character idiom, generate two deliverables:
1. **Script** — a Word document (.docx) in Chinese, following the channel's 8-step structure
2. **Images** — 7 PNG files ready for video editing

Output goes to a folder named `{idiom}/` inside the user's Downloads (or current working directory).

---

## Step 1 — Research the idiom

Before writing anything, research the idiom's:
- **Literal meaning** of each character
- **Extended/metaphorical meaning** as a set phrase
- **Classical origin** (author, work, original quote if it exists)
- **Usage register**: formal/informal? Positive/negative/neutral tone?
- **Common mistakes** or usage restrictions worth noting

### Step 1-A — Web search for origin (use WebSearch tool)

Run these queries in order, stopping when you have sufficient origin data:

1. `"{idiom}" 成语 出处 典故` — primary: finds origin in Chinese sources (Baidu, Zdic)
2. `site:zdic.net "{idiom}"` — 汉典 direct lookup (highest reliability)
3. `"{idiom}" idiom origin classical source` — English cross-check if needed

From search results, extract:
- **Dynasty + author** (e.g., 北宋·苏轼)
- **Work title** (e.g., 《宝绘堂记》)
- **Original quote** from the classical text
- **Modern explanation** of how the quote became the idiom

### Step 1-B — Verify and resolve conflicts

- **2+ sources agree** → adopt that origin
- **Sources conflict** → prefer: zdic.net > 汉典 > 百度百科 > others; use older/more authoritative source
- **No clear origin found** → note "出处不详" and explain as evolved from classical literary imagery

Source reliability ranking:
| Priority | Source | Reason |
|----------|--------|--------|
| 1 | zdic.net (汉典) | Academic, exact original text citations |
| 2 | chengyu.itc.cn | Dedicated idiom database |
| 3 | baike.baidu.com | Detailed commentary, needs verification |
| 4 | en.wikipedia.org | English cross-check only |

Use the verified search results to populate `origin_meta`, `origin_lines`, and `origin_explanation` in sections.json (Step 3).

---

## Step 2 — Generate the script content

Read `references/script_pattern.md` for the full pattern and tone guide.

The script is written **entirely in Chinese (Mandarin)**. Key structural points:

- **Fixed opener**: 大家好，欢迎来到小雪的中文屋。我是小雪，Snowy。
- **Opening hook**: Connect the idiom to something the viewer can relate to — a season, an emotion, a life situation. Keep it warm and natural, not academic.
- **Character analysis**: Analyze each of the 4 characters individually. For each: basic meaning, then 2–3 example compound words — **only use examples whose meaning relates directly to the idiom's theme** (e.g., for 息 in 息息相关, use breathing-related compounds like 气息、叹息、鼻息, not unrelated ones like 消息). Don't just list definitions — build understanding.
- **2+2 split** (if meaningful): If the 4-character idiom splits naturally into two 2-character halves with distinct meanings (e.g., 息息 + 相关), add a ③-B section after the character analysis that explains each half and how they combine.
- **Combined meaning**: Explain the literal meaning first, then the metaphorical/idiomatic meaning. If there are useful near-synonyms, mention 1–2 of them.
- **Classical origin**: If there is one, first briefly introduce the **author and work** (dynasty, name, what kind of text it is) before quoting the original text. This introduction **must be written as trilingual script sentences** (中文 / 拼音 / 영어) — spoken to the viewer as part of the script, NOT as a Korean side-note or blockquote. Write 2–3 sentence blocks: (1) "This idiom comes from X by Y, a Z-dynasty writer." (2) "The work is a collection of… the title means…" (3) "It records the author's thoughts on…". Then quote the original text and explain how it became today's idiom in accessible modern Chinese. Always add a **source link** (e.g., zdic.net) at the bottom of the origin section.
- **Examples**: Give 2 example sentences with full explanations. If the idiom has tonal complexity (e.g., used ironically with a negative word), show that in one example and explain the shift.
- **Usage notes**: What can and can't this idiom describe? Any grammatical constraints? Tone considerations?
- **Fill-in-the-blank quiz**: 2–3 short everyday sentences with `________` where the idiom belongs. Each entry needs `q_cn` (question), `q_en` (English hint), `full_cn` (answer sentence), `full_en` (English answer). Keep sentences short and relatable — daily life, emotions, relationships.
- **Closing hint**: Suggest a real situation where the viewer might try using it.
- **Fixed closer**: 好了，今天就到这里。希望你学到了一点新的中文。如果你喜欢我的内容，欢迎点赞加关注小雪的中文屋。我们下次再见！

Tone throughout: warm, conversational, like a knowledgeable friend. Use 大家 to address viewers directly. Mix sentence lengths. Use rhetorical questions (大家猜到了吗？你学会了吗？) to keep engagement.

---

## Step 3 — Save sections to JSON and run script generator

Every content field uses **trilingual sentence objects**: `{"cn": "中文", "py": "pīnyīn", "en": "English"}`.
Always supply all three fields — the script renderer prints them as colour-coded 中文 / 拼音 / 영어 triplets.

Prepare a `sections.json` file with this structure:

```json
{
  "opening_hook": [{"cn":"...","py":"...","en":"..."}],
  "char_analyses": [
    {"char":"过","pinyin":"guò","lines":[{"cn":"...","py":"...","en":"..."}]},
    {"char":"眼","pinyin":"yǎn","lines":[{"cn":"...","py":"...","en":"..."}]},
    {"char":"云","pinyin":"yún","lines":[{"cn":"...","py":"...","en":"..."}]},
    {"char":"烟","pinyin":"yān","lines":[{"cn":"...","py":"...","en":"..."}]}
  ],
  "combined_meaning": [{"cn":"...","py":"...","en":"..."}],
  "synonyms":         [{"cn":"...","py":"...","en":"..."}],
  "origin_meta": {"author":"北宋·苏轼","work":"《宝绘堂记》"},
  "origin_lines":       [{"cn":"...","py":"...","en":"..."}],
  "origin_explanation": [{"cn":"...","py":"...","en":"..."}],
  "examples": [
    {"lines":[{"cn":"...","py":"...","en":"..."}]},
    {"lines":[{"cn":"...","py":"...","en":"..."}]}
  ],
  "clip_revisit": [{"cn":"...","py":"...","en":"..."}],
  "quiz": [
    {"q_cn": "sentence with ________ where idiom goes", "q_en": "English with ________",
     "full_cn": "complete sentence with idiom", "full_en": "complete English sentence"},
    {"q_cn": "...", "q_en": "...", "full_cn": "...", "full_en": "..."}
  ],
  "usage_note":   [{"cn":"...","py":"...","en":"..."}],
  "closing_hint": [{"cn":"...","py":"...","en":"..."}]
}
```

**Pinyin rules**: use tone marks (ā á ǎ à), include spaces between syllables, keep punctuation as-is. Aim for natural reading flow — not mechanical syllable-by-syllable splits.

Then run the script generator:

```bash
python scripts/generate_script.py \
  --idiom "IDIOM" \
  --pinyin "PINYIN" \
  --sections /tmp/sections.json \
  --output "OUTPUT_DIR/IDIOM_Script.docx"
```

---

## Step 4 — Run image generator

Prepare the 4 character specs as `char,pinyin,meaning_cn,example_usage` strings (comma-separated, no spaces around commas). Then run:

```bash
python scripts/generate_images.py \
  --idiom "IDIOM" \
  --pinyin "PINYIN" \
  --meaning_cn "LITERAL_MEANING_CN" \
  --meaning_ko "MEANING_IN_KOREAN" \
  --chars "过,guò,经过/通过,路过经过掠过" \
          "眼,yǎn,眼睛,过眼=从眼前掠过" \
          "云,yún,云彩,飘忽不定象征无常" \
          "烟,yān,烟雾,转瞬消散不留痕迹" \
  --origin_text "北宋·苏轼《宝绘堂记》" \
  --origin_lines "譬之烟云之过眼，" "百鸟之感耳，" "岂不欣然接之，" "然去而不复念也。" \
  --example1 "那段感情已经是过眼云烟，她早就放下了。" \
  --example1_ko "지난 감정은 이미 스쳐간 구름 같아, 그녀는 놓아줬어." \
  --example2 "人生荣华，不过是过眼云烟。" \
  --example2_ko "인생의 영화는 결국 덧없이 지나갈 뿐." \
  --usage_note "과거의 일에 사용. 달관한 어조. 진행 중인 일에는 어색." \
  --episode EPISODE_NUMBER \
  --output_dir "OUTPUT_DIR/IDIOM_Images"
```

The `meaning_ko` field appears on thumbnail and title card — keep it short (under 22 characters) and natural-sounding in Korean.

---

## Step 5 — Generate Markdown and HTML scripts

Run both script generators using the same `sections.json`:

```bash
# Markdown (for GitHub)
python scripts/generate_markdown.py \
  --idiom "IDIOM" \
  --pinyin "PINYIN" \
  --episode EPISODE_NUMBER \
  --sections /tmp/sections.json \
  --output "/tmp/ep15_IDIOM.md"

# HTML (copy-button version for video editing work)
python scripts/generate_html.py \
  --idiom "IDIOM" \
  --pinyin "PINYIN" \
  --episode EPISODE_NUMBER \
  --sections /tmp/sections.json \
  --output "/tmp/ep15_IDIOM.html"
```

---

## Step 6 — Push to GitHub and deliver

The user's GitHub repo is `https://github.com/tmtmaj/snowys-chinese-house`.
Local clone is at `C:\Users\박정혁\github\snowys-chinese-house`.

Copy output files to the repo and push:

```bash
# Copy files to repo (paths are on the user's Windows machine)
# scripts/markdown/ep{NN}_{IDIOM}.md
# scripts/html/ep{NN}_{IDIOM}.html
# images/{IDIOM}/  (the 7 PNGs)

gh repo clone tmtmaj/snowys-chinese-house   # only needed first time
git -C REPO_PATH add .
git -C REPO_PATH commit -m "ep{NN}: add {IDIOM} ({PINYIN}) script and images"
git -C REPO_PATH push
```

Since `gh` is only available on the user's local machine (not in the sandbox),
generate a ready-to-run PowerShell push script and save it to Downloads alongside the output files.
Name it `push_epNN_IDIOM.ps1`. The user can double-click or run it in PowerShell to push in one step.

### push script template

```powershell
$repo = "$HOME\Documents\snowys-chinese-house"
$idiom = "IDIOM"
$episode = NN

Copy-Item "ep{NN}_$idiom.md"   "$repo\scripts\markdown\" -Force
Copy-Item "ep{NN}_$idiom.html" "$repo\scripts\html\"     -Force
Copy-Item "${idiom}_Images"    "$repo\images\$idiom"     -Recurse -Force

Set-Location $repo
git add .
git commit -m "ep${episode}: add $idiom script and images"
git push
Write-Host "✅ Pushed to GitHub!"
```

---

## Filename convention

Always use `{YYYYMMDD}_{pinyin-slug}` as the base name for all files and folders.
- **Date**: today's date in YYYYMMDD format
- **Pinyin slug**: romanised, hyphenated, no tone marks (e.g. `guo-yan-yun-yan`)
- Never use Chinese characters in filenames — causes Windows encoding errors

| Output | Filename pattern |
|--------|-----------------|
| Markdown | `{YYYYMMDD}_{slug}.md` |
| HTML | `{YYYYMMDD}_{slug}.html` |
| README | `README.md` |
| Word script | `{YYYYMMDD}_{slug}_script.docx` |
| Images folder | `{YYYYMMDD}_{slug}_images/` |
| Push script | `push_{YYYYMMDD}_{slug}.ps1` |

GitHub repo structure:
```
scripts/
  {YYYYMMDD}_{slug}/
    {YYYYMMDD}_{slug}.md
    {YYYYMMDD}_{slug}.html
    README.md
```
All outputs go in the single `scripts/{YYYYMMDD}_{slug}/` folder. No separate images folder.

Example for 过眼云烟 recorded 2026-03-31 → `20260331_guo-yan-yun-yan`

## Step 7 — Deliver to user

**Always create a `README.md`** in the script folder (`scripts/{YYYYMMDD}_{slug}/README.md`) that includes:
- Idiom, pinyin, and Korean meaning summary
- Channel + episode metadata (channel name, episode number, recording date)
- GitHub Pages URL: `https://tmtmaj.github.io/snowys-chinese-house/scripts/{slug}/{slug}.html`
- File list (md, html)

Present these files:
- `{YYYYMMDD}_{slug}.md` — GitHub용 마크다운
- `{YYYYMMDD}_{slug}.html` — 복사 버튼 HTML (브라우저에서 열기)
- `README.md` — 에피소드 요약 및 GitHub Pages 링크 포함
- `push_{YYYYMMDD}_{slug}.ps1` — 실행하면 GitHub에 자동 push

Do NOT generate images unless the user explicitly asks for them.

After presenting, briefly suggest:
- A drama/film clip search keyword that would fit the idiom well
- Any line in the script that may benefit from the user's personal touch

---

## Episode numbering

If the user doesn't specify an episode number, check the GitHub repo's `scripts/markdown/` folder naming for the last episode, then increment by 1. If unavailable, leave as 0.

---

## Font note

Images use `/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf` for Chinese character rendering. This font is pre-installed in the Cowork environment.
