---
name: word-episode-youtube
description: >
  YouTube word-episode package generator for 小雪的中文屋 (Snowy's Chinese House) —
  the Chinese buzzword/vocabulary learning series (流行词学习系列). Use this skill
  whenever the user gives a single Chinese word or buzzword (단어) and wants a new
  episode, says things like "다음 단어 에피소드 만들어줘", "绿茶로 에피소드 만들어",
  or names a word without specifying output. Given ONE Chinese word, produces the
  complete ep0001/ep0002-style package: 20 PNG cards (+blank+collage), A/B/E
  three-style scripts, shared scripts.js, tabbed index.html/script.html viewers,
  script.md, metadata.json, README with SEO YouTube title/description, thumbnail,
  and ref images. Each episode is fully independent (new protagonist, new story).
---

# 小雪的中文屋 — Word Episode Generator

Given **one Chinese word**, produce the full episode package identical in shape to
`contents/word/ep0001_wang-hong/` and `ep0002_lu-cha/`.

> Working dir: `/mnt/c/Users/USER/Documents/github/snowys-chinese-house`
> Engine: `contents/word/card_generator.py`. Project rules: root `CLAUDE.md` +
> `contents/word/CLAUDE.md`. This skill orchestrates them end-to-end.

Each episode is **completely independent** — do NOT continue the story/characters
from previous episodes. New protagonist, new situation every time.

---

## ✅ Completion checklist (`ep{NNNN}_{slug}/`)

An episode is "done" only when ALL of these exist:

1. `scripts/A_friendly-sibling.md` — friendly-sibling tone
2. `scripts/B_comedian.md` — comedian tone
3. `scripts/E_storyteller.md` — storyteller tone
4. `cards/` — `00_title`, `00b_collage`, `01`–`19`, **`blank.png`**
5. `scripts.js` — A/B/E × all-card narration data + render helpers
6. `index.html` — card viewer, top-right A/B/E tabs (loads scripts.js, default A)
7. `script.html` — narration viewer, same tabs + per-card copy button
8. `script.md` — default (A) script markdown
9. `metadata.json` — card sequence + repeat counts
10. `README.md` — GitHub Pages links + "🎬 YouTube 업로드" section (SEO title/desc)
11. `thumbnail.png` — 1280×720 split-layout thumbnail

---

## Step 1 — Research the word & pick episode number

- Determine: 한자, pinyin (with tone marks), literal meaning, and — for buzzwords —
  the **slang/internet meaning** (this is usually the real teaching point, e.g.
  网红=internet celebrity, 绿茶=sweet-but-scheming).
- Episode number: check `contents/word/` for the last `ep{NNNN}_` folder, +1.
- `slug`: English hyphenated, URL-safe (e.g. `lu-cha`, NOT `绿茶`).

## Step 2 — Write the story (3 paragraphs × 3 sentences)

Invent a fresh, funny, beginner-friendly story that teaches the word naturally.
- Paragraph 1: what the word means. Paragraph 2: introduce a new protagonist +
  situation. Paragraph 3: a twist ending.
- Mark the learning word with `★word★` (red highlight).
- Insert `∨` pause marks per PSC 停顿 rules (see `contents/word/CLAUDE.md`).
- Every sentence needs `cn` / `py` (pinyin w/ tones) / `en`.

## Step 3 — Add the episode dict to card_generator.py

Append a new dict to the `EPISODES` list in `contents/word/card_generator.py`
(copy an existing episode as template). Fields: `word`, `slug`, `pinyin`,
`desc_en`, `search_query` (Pixabay), `collage_images` (placeholder, fixed in
Step 6), `emoji`, `para_labels`, `script` (opening/pN_intro/pN_sX_note/pN_wrap/
closing — Chinese only), `paragraphs`.

## Step 4 — Generate cards (WSL → Windows path workaround)

Generate ONLY the new episode by index (do NOT run `main()` — it regenerates all
episodes and would overwrite ep0001/0002 custom tabbed HTML):

```bash
cd /mnt/c/Users/USER/Documents/github/snowys-chinese-house/contents/word
python3 -c "
import sys; sys.path.insert(0, '.')
import card_generator as cg
cg.OUT_DIR = '/tmp/word_cards'
cg.generate_episode({N}, cg.EPISODES[{N-1}])   # e.g. 3, EPISODES[2]
"
DEST="/mnt/c/.../contents/word/ep{NNNN}_{slug}"
mkdir -p "$DEST" && cp -r /tmp/word_cards/ep{NNNN}_{slug}/. "$DEST/"
```

Never write to a Chinese-character path directly (WSL `OSError`) — build in `/tmp`
then copy. This also downloads ~10 Pixabay CC0 images to `ref/`.

## Step 5 — blank.png + verify cards

```bash
python3 -c "
import sys; sys.path.insert(0,'.'); import card_generator as cg
img,_ = cg.base(); img.save('ep{NNNN}_{slug}/cards/blank.png')
"
```
Visually check `00_title.png` and a sentence card (pinyin tones, ∨ marks, English).

## Step 6 — ⚠️ ref photos = USER-SELECTED (do not auto-confirm)

Pixabay auto-download is only a **candidate pool**. For collage(00b) & thumbnail:
- Show candidates, ask the user to **add their own better images** to `ref/`
  (e.g. `11.png`, `12.png`).
- Ask the user which ref numbers to use, then set `collage_images` and regenerate.
- Do NOT treat collage/thumbnail as "done" before the user confirms.

**When collage photos change, you MUST also update the Photo-card narration** —
edit `scripts.js` `photo` entries (A/B/E all) to match what's actually visible,
then regenerate the A/B/E md + script.md.

## Step 7 — scripts.js (A/B/E shared data)

Copy `ep0001_wang-hong/scripts.js` as template. Keep `STYLES`, `CARDS` (30 entries),
and render helpers identical. Rewrite `NARR.A/B/E` for the new word.
- `s` = learning sentence (bold), `n` = grammar note, `t` = plain narration (`\n` breaks).
- **Naturalness first** — real spoken feel, no textbook stiffness, no forced jokes.
  See "Word Episode Script Styles" in project CLAUDE.md for A/B/E tone rules.

## Step 8 — Tabbed HTML (copy ep0001, swap header only)

```bash
cp ep0001_wang-hong/index.html  ep{NNNN}_{slug}/index.html
cp ep0001_wang-hong/script.html ep{NNNN}_{slug}/script.html
```
Then edit only the `<title>` and the header `word`/`pinyin`/`desc` in both files.
The tab logic + scripts.js loading are already correct.

## Step 9 — Generate A/B/E md + script.md FROM scripts.js

Do NOT hand-type the markdown — generate it from `scripts.js` so data always matches.
Use `references/gen_md.js` (concatenate with scripts.js and run with Node):

```bash
cd ep{NNNN}_{slug}
cat scripts.js ../../../.claude/skills/word-episode-youtube/references/gen_md.js > /tmp/combined.js
node /tmp/combined.js "$(pwd)" "{NNNN}" "{word}"
```
It validates (30 cards, 0 missing) and writes `scripts/A|B|E.md` + `script.md`.

## Step 10 — Thumbnail (1280×720 split layout)

Left kraft panel (~55%): word + pinyin + English (max contrast, big word).
Right (~45%): cover-cropped photos — **same ref images as the collage**. Use
`references/make_thumbnail.py` logic. See "YouTube Thumbnail" in project CLAUDE.md.

## Step 11 — README with SEO title/description

Front-load the word + English meaning in the title; first sentence of description
carries the keyword + what's learned; include timestamps, CTA, 12–15 hashtags
(exact-match first). Follow "YouTube Title & Description SEO" in project CLAUDE.md.
Playlist: `Chinese Buzzwords｜流行词学习系列`.

## Step 12 — Verify, then commit & push (confirm message first)

- Confirm all 11 checklist items exist.
- `git add contents/word/ep{NNNN}_{slug}/ contents/word/card_generator.py`
- Commit `ep{NNNN}: add {word} ({pinyin}) word episode`, confirm with user, push.

---

## Guardrails learned from ep0001/0002
- `main()` regenerates ALL episodes → overwrites custom tabbed HTML. Always
  generate a single episode by index.
- Generator's built-in HTML has NO A/B/E tabs — always overwrite with the
  ep0001-template tabbed versions (Step 8).
- Chinese paths break WSL writes — build in `/tmp`, copy to repo.
- Collage/thumbnail are NOT done until the user picks the photos.
- **Editing a paragraph sentence after cards exist**: the same sentence is baked
  into MULTIPLE cards. Regenerate ALL of them, not just the single sentence card:
  the sentence card (`0N_pX_sY.png`), the paragraph-full card (`05/10/15_pX_full.png`),
  AND the review card (`17/18/19_review_pX.png`). Also patch `metadata.json`
  (it embeds cn/py/en per sentence card). Then update `scripts.js` (s/s2/review) +
  regenerate md. Missing the full/review cards leaves stale text on screen.
