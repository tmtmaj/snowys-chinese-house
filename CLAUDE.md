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

> **단어 하나를 받으면 아래 전체 패키지가 ep0001(网红)과 동일하게 완성되어야 한다.**
> 각 에피소드는 **완전히 독립**이다 — 이전 에피소드와 스토리·등장인물을 이어갈 필요 없음. 매번 새 주인공·새 상황으로 자유롭게.

### ✅ 완성 산출물 체크리스트 (`ep{NNNN}_{slug}/`)

단어 입력 → 아래가 전부 생성/작성되어야 "완성":

1. `scripts/A_friendly-sibling.md` — 친근 톤 전체 스크립트
2. `scripts/B_comedian.md` — 개그맨 톤 전체 스크립트
3. `scripts/E_storyteller.md` — 스토리텔러 톤 전체 스크립트
   - (3 스타일 규칙·자연스러움 원칙은 아래 "Word Episode Script Styles" 참고)
4. `cards/` — PNG 카드 (00_title, 00b_collage, 01~19, **blank.png** 포함)
5. `scripts.js` — A/B/E × 전 카드 나레이션 공유 데이터 + 렌더 헬퍼 (ep0001 구조 그대로)
6. `index.html` — 카드 뷰어, 우측 상단 A/B/E 전환 탭 (scripts.js 로드, 디폴트 A)
7. `script.html` — 낭독 스크립트 뷰어, 동일 탭 + 카드별 복사 버튼
8. `script.md` — 디폴트(A) 스크립트 마크다운
9. `metadata.json` — 카드 시퀀스 + repeat 횟수
10. `README.md` — GitHub Pages 링크 + **"🎬 YouTube 업로드" 섹션** (제목·설명 코드박스, "YouTube Title & Description SEO" 규칙 적용)

> `blank.png`: 텍스트 없는 빈 배경 카드. `card_generator.base()` 호출 후 저장 (다른 카드와 픽셀 동일).
> `scripts.js`/`index.html`/`script.html`은 ep0001을 템플릿으로 복제 후 데이터만 교체.

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

## YouTube Title & Description SEO

에피소드 업로드용 제목/설명은 각 에피소드 `README.md`의 "🎬 YouTube 업로드" 섹션에 코드박스로 작성한다.
아래는 2026 YouTube SEO 모범 사례 기반 규칙 (idiom·word 공통 적용).

### 제목 (Title)
- **핵심 키워드를 앞 40자 안에 front-load**: 단어/성어 + 영어 의미를 맨 앞에 (예: `网红 (wǎng hóng) = Internet Celebrity`). "Chinese Idiom/Buzzword" 같은 시리즈 브랜드보다 실제 단어·의미의 검색량이 높음.
- **전체 길이 60~70자 권장** (모바일에서 ~60자 후 잘림).
- **학습 결과(outcome) 명시**: `Meaning & Usage`, `Meaning, Origin & Examples` 등.
- **시리즈 번호 + 재생목록 태그 유지** (제목 끝): `| Chinese Buzzword #N`.
- 키워드 스터핑 금지 — 자연스럽게. 낚시 금지 (2026 알고리즘은 high CTR + low watch time 페널티).

### 설명 (Description)
- **첫 1~2문장(첫 25단어)에 핵심 키워드 + 무엇을 배우는지** 명시 (above the fold가 가중치 높음).
- 길이 250자 이상, 영어 + 중국어 병기, 한국어 학습자 타깃 고려.
- **타임스탬프 포함** (시청 지속률 +12%). 카드 구조(Intro/第一段/第二段/第三段/复习) 기반. 업로드 시 실제 시간으로 교체.
- CTA(좋아요·구독) 한 줄.
- **해시태그 12~15개**: 첫 3개가 제목 위에 노출되므로 가장 가치 있는 순서로. 정확매칭(`#网红 #wanghong`) + 카테고리(`#LearnChinese #HSK #ChineseVocabulary`) + 한국어(`#중국어 #중국어공부`).

---

## General Rules
- Python scripts use `python3` (not `python`)
- JSON with Chinese text: always generate via `json.dump()` in Python to avoid quote-escaping issues
- Idiom episode numbering: check last committed episode in `contents/idiom/` folder, increment by 1
- Word episode numbering: check last committed episode in `contents/word/` folder, increment by 1
- Never commit the sections.json temp file (lives in /tmp/)
- Working directory: `/mnt/c/Users/USER/Documents/github/snowys-chinese-house` (Windows clone via WSL)
- Branch: `main` (master 삭제됨)
