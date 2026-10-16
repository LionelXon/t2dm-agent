import re
from pathlib import Path

import pymupdf as fitz

from src.schemas import GuidelineChunk


# ---------- 常量 ----------

CHUNK_TARGET = 400
CHUNK_MIN = 40
CHUNK_MAX = 800

NOISE_PATTERNS = [
    r"^·\s*\d+\s*·$",
    r"^中华.*杂志.*年.*月第.*期",
    r"^Chin J .*Vol\..*No\.",
    r"^·\s*规范与指南\s*·$",
    r"^DOI[:：]",
    r"^收稿日期",
    r"^引用本文",
    r"^通信作者[:：]",
]

TOC_DOT = re.compile(r"[………]{2,}")
CHAPTER_PATTERN = re.compile(r"^第[一二三四五六七八九十百]+章[\s　]*([^…]{2,30})$")
SECTION_PATTERN = re.compile(r"^[一二三四五六七八九十]+、[\s　]*([^…]{2,30})$")
KEYPOINT_HEADER = re.compile(r"^要点提示[:：]?\s*(.*)$")
META_PARA = re.compile(r"【(摘要|关键词)】|Corresponding authors")
EVIDENCE_IN_LINE = re.compile(r"[（(]([ABC])[)）]")
SENTENCE_END = ("。", "！", "？", "；")
# 编号后必须跟非数字非空白字符，避免误匹配 10.9% 这类数字
NUMBERED_LINE = re.compile(r"^(\d{1,2})\s*[.、．]\s*(?=[^\d\s])")
TABLE_FIG_LINE = re.compile(r"^[表图]\s*\d+")
# 私有区/控制字符比例高的行视为乱码
PRIVATE_USE = re.compile(r"[\ue000-\uf8ff\U000F0000-\U000FFFFD]")


# ---------- 工具函数 ----------

def _is_noise(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    for pat in NOISE_PATTERNS:
        if re.match(pat, s):
            return True
    if TOC_DOT.search(s):
        return True
    return False


def _looks_like_garbage(line: str) -> bool:
    """私有区字符比例高的行，通常是 PDF 嵌入字体导致。"""
    if len(line) < 3:
        return False
    return len(PRIVATE_USE.findall(line)) / len(line) > 0.3


def _split_into_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[。！？；])", text)
    return [p for p in parts if p]


def _pack_sentences(
    sentences: list[str],
    target: int = CHUNK_TARGET,
    hard_max: int = CHUNK_MAX,
) -> list[str]:
    chunks: list[str] = []
    buf = ""
    for s in sentences:
        if len(s) > hard_max:
            if buf:
                chunks.append(buf)
                buf = ""
            for i in range(0, len(s), hard_max):
                chunks.append(s[i : i + hard_max])
            continue
        if not buf or len(buf) + len(s) <= target:
            buf += s
        else:
            chunks.append(buf)
            buf = s
    if buf:
        chunks.append(buf)
    return chunks


# ---------- 主解析 ----------

def parse_pdf(
    path: str,
    guide_id: str,
    guide_name: str,
    year: int,
    rec_id_pattern: str = "cn_numbered",
    evidence_pattern: str = "cn_level",
) -> list[GuidelineChunk]:
    doc = fitz.open(path)
    chunks: list[GuidelineChunk] = []
    idx = 0

    current_chapter = ""
    current_section = ""
    buffer: list[str] = []
    buffer_page: int | None = None
    in_keypoints = False
    keypoint_buffer: list[str] = []
    keypoint_page: int | None = None
    nonnum_streak = 0
    seen_numbers: set[int] = set()   # ← 新增


    def new_chunk(text: str, page: int, evidence: str | None = None, prefix: str = "c"):
        nonlocal idx
        idx += 1
        label = current_chapter
        if current_section:
            label = f"{current_chapter} / {current_section}".strip(" /")
        chunks.append(GuidelineChunk(
            chunk_id=f"{guide_id}_{prefix}{idx:04d}",
            guide_name=guide_name,
            year=year,
            section=label,
            rec_id=None,
            evidence_level=evidence,
            page=page,
            text=text,
        ))

    def flush_buffer(page: int):
        nonlocal buffer, buffer_page
        text = "".join(buffer).strip()
        buffer = []
        buffer_page = None
        if len(text) < CHUNK_MIN:
            return
        if META_PARA.search(text):
            return
        sentences = _split_into_sentences(text)
        for packed in _pack_sentences(sentences):
            packed = packed.strip()
            if len(packed) >= CHUNK_MIN:
                new_chunk(packed, page)

    def flush_keypoints(page: int):
        nonlocal keypoint_buffer, keypoint_page, in_keypoints, nonnum_streak
        text = "".join(keypoint_buffer).strip()
        keypoint_buffer = []
        keypoint_page = None
        in_keypoints = False
        nonnum_streak = 0
        seen_numbers = set()   # ← 新增
        if len(text) < 40:
            return
        evs = EVIDENCE_IN_LINE.findall(text)
        ev = evs[0] if evs else None
        new_chunk("【要点提示】\n" + text, page, evidence=ev, prefix="kp")

    for page_num, page in enumerate(doc, start=1):
        text = page.get_text("text")
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if _is_noise(line):
                continue

            # 章节标题
            ch = CHAPTER_PATTERN.match(line)
            if ch:
                if in_keypoints:
                    flush_keypoints(keypoint_page or page_num)
                if buffer:
                    flush_buffer(buffer_page or page_num)
                current_chapter = ch.group(1).strip()
                current_section = ""
                continue

            # 小节标题
            sec = SECTION_PATTERN.match(line)
            if sec:
                if in_keypoints:
                    flush_keypoints(keypoint_page or page_num)
                if buffer:
                    flush_buffer(buffer_page or page_num)
                current_section = sec.group(1).strip()
                continue

            # 要点提示块起始
            km = KEYPOINT_HEADER.match(line)
            if km:
                if in_keypoints:
                    flush_keypoints(keypoint_page or page_num)
                if buffer:
                    flush_buffer(buffer_page or page_num)
                in_keypoints = True
                keypoint_page = page_num
                keypoint_buffer = []
                nonnum_streak = 0
                seen_numbers = set()   # ← 新增
                rest = km.group(1).strip()
                if rest:
                    keypoint_buffer.append(rest)
                continue

            # 表格/图标题
            if TABLE_FIG_LINE.match(line):
                if in_keypoints:
                    flush_keypoints(keypoint_page or page_num)
                # 往下按正文处理

            # 要点提示块内容
            if in_keypoints:
                if _looks_like_garbage(line):
                    continue
                m = NUMBERED_LINE.match(line)
                if m:
                    num = int(m.group(1))
                    if num in seen_numbers:
                        # 编号重复，说明这一段的要点提示结束了
                        flush_keypoints(keypoint_page or page_num)
                        # 这一行往下按正文处理
                    else:
                        seen_numbers.add(num)
                        nonnum_streak = 0
                        keypoint_buffer.append(line)
                        if sum(len(x) for x in keypoint_buffer) >= CHUNK_MAX:
                            flush_keypoints(keypoint_page or page_num)
                        continue
                elif len(line) > 80 and line.endswith(SENTENCE_END):
                    flush_keypoints(keypoint_page or page_num)
                elif nonnum_streak < 2:
                    nonnum_streak += 1
                    keypoint_buffer.append(line)
                    continue
                else:
                    flush_keypoints(keypoint_page or page_num)

            # 普通正文
            if buffer_page is None:
                buffer_page = page_num
            buffer.append(line)

            buf_len = sum(len(x) for x in buffer)
            if buf_len >= CHUNK_TARGET:
                joined = "".join(buffer)
                if joined.endswith(SENTENCE_END) or buf_len >= CHUNK_MAX:
                    flush_buffer(buffer_page or page_num)

    # 收尾
    if in_keypoints:
        flush_keypoints(keypoint_page or len(doc))
    if buffer:
        flush_buffer(buffer_page or len(doc))

    return chunks