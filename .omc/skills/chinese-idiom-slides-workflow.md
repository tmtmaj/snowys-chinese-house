# Chinese Idiom Slides HTML Generator

## The Insight
성어 영상 스크립트(.md)가 있으면, 브라우저에서 바로 열 수 있는 슬라이드 HTML을 생성할 수 있다.
크라프트 종이 배경 + 병음 루비 텍스트 + 키보드 네비게이션으로 참고 영상(惺惺相惜 ep17) 스타일을 재현.

## Why This Matters
- Pillow(Python)로 이미지 생성 시 한자 폰트 누락, 레이아웃 불일치 문제 발생
- HTML/CSS + Google Fonts(Noto Serif SC)를 쓰면 브라우저가 한자를 완벽하게 렌더링
- 각 슬라이드를 스크린샷하면 영상 제작용 이미지로 바로 활용 가능

## Recognition Pattern
사용자가 다음 중 하나를 요청할 때:
- "slides.html 만들어줘"
- "슬라이드 만들어줘"
- "영상 이미지 만들어줘"
- 특정 에피소드 폴더명(예: 20260413_hua-she-tian-zu)을 언급하며 슬라이드 요청

## The Approach

### 1. 스크립트 파악
`scripts/{episode}/{episode}.md` 읽기 → 성어, 병음, 뜻, 유래, 예문, 填空, 使用注意 추출

### 2. 참고 영상 디자인 토큰
```
배경:  #c9a86c  (크라프트 종이)
주 텍스트: #1a0d00
병음/강조: #8B1500  (진한 빨강)
라벨:  #4a3010
폰트:  'Noto Serif SC' (Google Fonts)
슬라이드 크기: 1280 × 720px (16:9)
```

### 3. 슬라이드 구성 (13장 기본)
| # | 슬라이드 |
|---|---------|
| 1 | 타이틀 — 한자 대형 + 병음 |
| 2 | 成语意思 — 글자별 분해 (char-table) |
| 3 | 字面意思 & 引申义 |
| 4 | 成语由来 — 출처 서적 |
| 5 | 故事 ① — 배경/설정 |
| 6 | 故事 ② — 결말/교훈 |
| 7 | 近义词 & 反义词 |
| 8 | 例句 一 |
| 9 | 例句 二 |
| 10 | 填空练习 (빈칸) |
| 11 | 填空练习 (정답) |
| 12 | 使用注意 |
| 13 | Outro — 感谢收看 + 点赞/关注 |

### 4. 핵심 CSS 패턴

**병음 루비** (한자 위 병음):
```html
<ruby>画蛇添足<rt>huà shé tiān zú</rt></ruby>
```

**글자별 분해 테이블**:
```html
<div class="char-row">
  <div class="char-block">
    <div class="char-py">huà</div>
    <div class="char-hanzi">画</div>
  </div>
  <div class="char-defs">
    <div class="def-line"><span class="def-n">①</span> 뜻 <span class="def-en">English</span></div>
  </div>
</div>
```

**키보드 네비게이션**:
```js
document.addEventListener('keydown', e => {
  if (e.key === 'ArrowRight' || e.key === 'ArrowDown') go(1);
  if (e.key === 'ArrowLeft'  || e.key === 'ArrowUp')   go(-1);
});
```

### 5. 저장 위치
```
scripts/{episode}/slides.html
```

## Example
`scripts/20260413_hua-she-tian-zu/slides.html` — 画蛇添足 ep22 슬라이드 참고
