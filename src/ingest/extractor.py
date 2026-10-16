import re


# ---------- 推荐编号抽取 ----------

def extract_rec_id_cn_numbered(text: str) -> str | None:
    """中国指南常见格式：5.1.2、6.2.1 这类章节号。
    找到文本里第一个形如 x.y.z 或 x.y 的编号。
    """
    m = re.search(r"\b(\d{1,2}(?:\.\d{1,2}){1,3})\b", text)
    return m.group(1) if m else None


def extract_rec_id_ada_lettered(text: str) -> str | None:
    """ADA 常见：Recommendation 5.2、Section 6.1、或者 B 级证据条目。
    先试章节号，再试推荐编号。
    """
    m = re.search(r"(?:Recommendation|Section)\s+(\d+(?:\.\d+)+)", text, re.IGNORECASE)
    if m:
        return m.group(1)
    return extract_rec_id_cn_numbered(text)


REC_ID_EXTRACTORS = {
    "cn_numbered": extract_rec_id_cn_numbered,
    "ada_lettered": extract_rec_id_ada_lettered,
}


# ---------- 证据等级抽取 ----------

def extract_evidence_cn_level(text: str) -> str | None:
    """中国指南：证据等级：A/B/C 或 (A级)、(B级)。
    """
    m = re.search(r"证据(?:等级|级别)[：:]\s*([ABC])", text)
    if m:
        return m.group(1)
    m = re.search(r"[（(]([ABC])[级][)）]", text)
    return m.group(1) if m else None


def extract_evidence_ada_grade(text: str) -> str | None:
    """ADA：Level A/B/C/E 或 Grade A/B/C。"""
    m = re.search(r"(?:Level|Grade)\s+([ABCE])", text, re.IGNORECASE)
    return m.group(1).upper() if m else None


EVIDENCE_EXTRACTORS = {
    "cn_level": extract_evidence_cn_level,
    "ada_grade": extract_evidence_ada_grade,
}