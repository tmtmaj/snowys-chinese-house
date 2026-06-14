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
git add contents/idiom/{YYYYMMDD}_{slug}/
git commit -m "ep{NN}: add {IDIOM} ({PINYIN}) script"
git push
```
Confirm commit message with user before pushing.

---

## Repository Structure

```
snowys-chinese-house/
  contents/
    idiom/          ← 사자성어 에피소드 (구 scripts/)
      {YYYYMMDD}_{slug}/
        README.md   ← GitHub Pages 링크 포함
        *.md        ← 스크립트
        *.html      ← HTML 뷰어
    word/           ← 단어 학습 카드 에피소드
      card_generator.py
      CLAUDE.md
      ep{NNNN}_{slug}/  ← slug는 영어 하이픈 표기 (예: wang-hong, NOT 网红)
        README.md   ← GitHub Pages 링크 포함
        index.html  ← 카드 뷰어 (이미지 + 나레이션)
        script.html ← 나레이션 스크립트 HTML (복사 버튼 포함)
        script.md   ← 선생님 스크립트 마크다운
        metadata.json
        cards/      ← PNG 카드 (1920×1080)
```

GitHub Pages base: `https://tmtmaj.github.io/snowys-chinese-house/`

---

## Word Episode Generation Workflow

`contents/word/card_generator.py` 로 카드 PNG + HTML 생성.

### 카드 생성 (WSL → Windows 경로 문제 우회)
```bash
# 1. Linux 임시 경로에서 생성
cd /mnt/c/Users/USER/Documents/github/snowys-chinese-house/contents/word
python3 -c "
import sys; sys.path.insert(0, '.')
import card_generator as cg
cg.OUT_DIR = '/tmp/word_cards'
cg.main()
"

# 2. Windows 경로로 복사
DEST="/mnt/c/Users/USER/Documents/github/snowys-chinese-house/contents/word/ep{NNNN}_{slug}"
cp -r /tmp/word_cards/ep{NNNN}_{slug}/. "$DEST/"
```

**주의**: 한자 경로(`ep0001_网红`)에 직접 쓰면 WSL에서 `OSError` 발생 → 반드시 `/tmp/`에서 생성 후 복사.

### 에피소드 데이터 필드
- `slug`: 영어 하이픈 표기 필수 (URL 안전) — 예: `"slug": "wang-hong"`
- `para_labels`: 복습 카드용 단락 설명 (선택)
- `★word★`: 빨간 하이라이트 마커 (학습 단어에만 사용)
- `∨`: 보조 v 마크 (강세/끊기 표시)

### GitHub Pages
- 배포: `.github/workflows/pages.yml` (main 브랜치 push 시 자동)
- 카드 뷰어: `https://tmtmaj.github.io/snowys-chinese-house/contents/word/ep{NNNN}_{slug}/index.html`
- 스크립트: `https://tmtmaj.github.io/snowys-chinese-house/contents/word/ep{NNNN}_{slug}/script.html`

---

## Word Episode Script Styles

단어 에피소드 스크립트는 **반드시 3가지 스타일로** 생성한다.
각 스타일 파일은 `contents/word/ep{NNNN}_{slug}/scripts/` 폴더에 저장.

### 3가지 스타일

| 파일명 | 스타일 | 특징 |
|--------|--------|------|
| `A_friendly-sibling.md` | 친근한 언니/오빠 | 따뜻한 공감, 개인 경험 공유, 격려하는 톤 |
| `B_comedian.md` | 유머러스한 개그맨 | 자기 비하 유머, 농담이 학습 포인트와 자연스럽게 연결 |
| `E_storyteller.md` | 스토리텔러/배우 | 드라마틱한 내러티브, 문법 설명을 이야기 안에 녹임, 무대 지문 활용 |

### ⚠️ 자연스러움 최우선 원칙

**가장 중요한 기준은 자연스러움이다.** 스크립트는 실제 사람이 말하는 것처럼 들려야 한다.

절대 금지:
- 교과서 같은 딱딱한 문장 ("이 단어는 X를 의미합니다")
- 억지로 재미있어 보이려는 개그
- 억지로 힙해 보이려는 슬랭 남용
- 문법 설명이 강의처럼 느껴지는 구조

각 스타일별 자연스러움 기준:
- **A**: 친구가 옆에서 알려주는 느낌. "저도 처음엔 몰랐어요" 같은 공감.
- **B**: 웃음 타이밍이 자연스러워야 함. 억지 개그보다 상황 자체가 웃겨야 함.
- **E**: 이야기 속 인물처럼 말하는 느낌. 무대 지문이 어색하지 않아야 함. 문법 설명이 내러티브 흐름을 끊으면 안 됨.

### 스크립트 구조

모든 3가지 스타일은 동일한 카드 시퀀스를 따르되 톤과 내용이 달라야 한다:
- Opening (00_title.png) → Photo (00b_collage.png)
- 각 단락: 구분카드 → 문장별 1遍+2遍 → 全文 마무리
- 复习: 16~19 카드

---

## General Rules
- Python scripts use `python3` (not `python`)
- JSON with Chinese text: always generate via `json.dump()` in Python to avoid quote-escaping issues
- Idiom episode numbering: check last committed episode in `contents/idiom/` folder, increment by 1
- Word episode numbering: check last committed episode in `contents/word/` folder, increment by 1
- Never commit the sections.json temp file (lives in /tmp/)
- Working directory: `/mnt/c/Users/USER/Documents/github/snowys-chinese-house` (Windows clone via WSL)
- Branch: `main` (master 삭제됨)
