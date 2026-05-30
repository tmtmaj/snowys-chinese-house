# 小雪的中文屋 — Project Instructions

## Channel
YouTube channel: 小雪的中文屋 (Snowy's Chinese House)
Host: 小雪 (Snowy)
GitHub: https://github.com/tmtmaj/snowys-chinese-house

---

## Content Generation Workflow

When generating a Chinese idiom episode (via the `chinese-idiom-youtube` skill):

### Step A — Generate (Sonnet)
Sonnet handles all research, sections.json writing, and file generation (docx, md, html, README, ps1).

### Step B — Opus Verification (REQUIRED before commit)
After all files are generated, spawn an Opus agent to review the complete output.
The Opus agent must check and fix ALL of the following:

**Chinese content**
- Pinyin tone marks are correct for every sentence
- Chinese characters are accurate (no wrong homophones, no typos)
- Classical origin quote matches the authoritative source
- Character analysis examples are relevant and on-theme (not random compound words)

**Script quality**
- Opening hook feels warm and relatable, not academic
- Each character analysis builds understanding (not just definitions)
- Origin section introduces author/work before quoting (as trilingual spoken lines)
- Fill-in-the-blank quiz sentences are short and natural
- Usage notes are accurate and include the right contrast with near-synonyms
- Closing hint is specific and actionable

**Structure**
- All 8 script sections are present and complete
- No missing pinyin or English translations
- Episode number is correct (incremented from last committed episode)

The Opus agent fixes issues directly in the generated files (md, html, docx regenerated if needed).
Report a summary of what was changed.

### Step C — Commit & Push
After Opus verification passes, run:
```bash
git add scripts/{YYYYMMDD}_{slug}/
git commit -m "ep{NN}: add {IDIOM} ({PINYIN}) script"
git push
```
Confirm commit message with user before pushing.

---

## General Rules
- Python scripts use `python3` (not `python`)
- JSON with Chinese text: always generate via `json.dump()` in Python to avoid quote-escaping issues
- Episode numbering: check last committed episode in `scripts/` folder, increment by 1
- Never commit the sections.json temp file (lives in /tmp/)
