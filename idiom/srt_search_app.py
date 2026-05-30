import os
import glob
from typing import List, Dict
from collections import defaultdict

import streamlit as st


SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src_files")


def find_srt_files(base_dir: str) -> List[str]:
    pattern = os.path.join(base_dir, "**", "*.srt")
    return glob.glob(pattern, recursive=True)


def read_text_with_fallback(path: str) -> str:
    """
    Try common encodings for Chinese subtitles.
    Order matters.
    """
    for enc in ("utf-8", "utf-8-sig", "gbk"):
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
        except OSError:
            return ""
    return ""


def parse_srt_blocks(content: str) -> List[Dict]:
    blocks: List[Dict] = []
    current = {"index": None, "time": "", "text_lines": []}

    for line in content.splitlines():
        line = line.strip("\ufeff").rstrip()

        # blank line → end block
        if line == "":
            if current["time"]:
                blocks.append(
                    {
                        "index": current["index"],
                        "time": current["time"],
                        "text": " ".join(current["text_lines"]).strip(),
                    }
                )
            current = {"index": None, "time": "", "text_lines": []}
            continue

        # index
        if current["index"] is None and line.isdigit():
            current["index"] = int(line)
            continue

        # time range
        if current["time"] == "" and "-->" in line:
            current["time"] = line
            continue

        # subtitle text
        current["text_lines"].append(line)

    # last block
    if current["time"]:
        blocks.append(
            {
                "index": current["index"],
                "time": current["time"],
                "text": " ".join(current["text_lines"]).strip(),
            }
        )

    return blocks


def search_in_srt_files(keyword: str, ignore_case: bool = True) -> List[Dict]:
    results: List[Dict] = []
    if not keyword:
        return results

    keyword_cmp = keyword.lower() if ignore_case else keyword

    for path in find_srt_files(SRC_DIR):
        content = read_text_with_fallback(path)
        if not content:
            continue

        # file-level prefilter (speed)
        content_cmp = content.lower() if ignore_case else content
        if keyword_cmp not in content_cmp:
            continue

        blocks = parse_srt_blocks(content)
        for b in blocks:
            text_cmp = b["text"].lower() if ignore_case else b["text"]
            if keyword_cmp in text_cmp:
                results.append(
                    {
                        "file": os.path.relpath(path, SRC_DIR),
                        "index": b["index"],
                        "time": b["time"],
                        "text": b["text"],
                    }
                )

    return results


def main():
    st.set_page_config(page_title="SRT 자막 검색기", layout="wide")
    st.title("📄 SRT 자막 블록 검색기")
    st.write("`src_files` 폴더 안의 모든 `.srt` 파일에서 검색어가 포함된 자막 블록을 찾습니다.")

    if not os.path.isdir(SRC_DIR):
        st.error(f"`src_files` 폴더를 찾을 수 없습니다:\n{SRC_DIR}")
        return

    with st.sidebar:
        st.header("🔍 검색 옵션")
        keyword = st.text_input("검색할 단어 / 문장", value="自欺欺人")
        ignore_case = st.checkbox("영문 대소문자 무시", value=True)
        run = st.button("검색 실행")

    if not run:
        st.info("왼쪽에서 검색어를 입력하고 **검색 실행**을 눌러주세요.")
        return

    with st.spinner("검색 중..."):
        results = search_in_srt_files(keyword, ignore_case)

    st.subheader(f"검색 결과: {len(results)}개 블록")

    if not results:
        st.warning("일치하는 자막이 없습니다.")
        return

    grouped = defaultdict(list)
    for r in results:
        grouped[r["file"]].append(r)

    for file, blocks in grouped.items():
        st.markdown(f"### 📁 {file}  \n일치 블록: **{len(blocks)}개**")
        for b in blocks:
            with st.expander(f"#{b['index']} | {b['time']}"):
                st.markdown(f"**시간**: `{b['time']}`")
                st.markdown(f"**내용**: {b['text']}")

    # TXT export (구버전 Streamlit 호환)
    export_lines = []
    for r in results:
        export_lines.append(f"[{r['file']}] #{r['index']} {r['time']}")
        export_lines.append(r["text"])
        export_lines.append("")

    export_text = "\n".join(export_lines)

    st.download_button(
        "검색 결과 TXT 다운로드",
        export_text.encode("utf-8"),
    )


if __name__ == "__main__":
    main()
