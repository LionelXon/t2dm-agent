import re

from src.workflows.nodes import extract_json


JUDGE_PROMPT = """你是一名事实核验员。给定【证据】（从临床指南检索到的原文片段）和若干条【陈述】，判断每条陈述是否被证据支持。

label 只能是：
- entail：证据直接支持陈述
- neutral：证据不涉及陈述内容
- contradict：证据与陈述矛盾

严格输出 JSON：
{"judgments": [{"idx": 0, "label": "entail", "reason": "..."}, ...]}

不要输出 JSON 之外的任何文字。
"""


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"[。！？；]", text or "")
    return [p.strip() for p in parts if len(p.strip()) >= 3]


def judge_claims(claims: list[str], evidence: str, llm) -> list[dict]:
    if not claims:
        return []
    prompt = "【证据】\n" + evidence + "\n\n【陈述】\n"
    for i, c in enumerate(claims):
        prompt += f"{i}. {c}\n"
    resp = llm.invoke([
        {"role": "system", "content": JUDGE_PROMPT},
        {"role": "user", "content": prompt},
    ])
    text = resp.content if hasattr(resp, "content") else str(resp)
    try:
        data = extract_json(text)
        return data.get("judgments", [])
    except Exception:
        return [{"idx": i, "label": "neutral", "reason": "parse_failed"} for i in range(len(claims))]


def compute_faithfulness(answer: str, citations: list[dict], chunk_map: dict, llm) -> dict:
    claims = split_sentences(answer)
    if not claims:
        return {"score": 1.0, "claims": [], "judgments": []}

    evidence_texts = []
    for c in citations:
        chunk = chunk_map.get(c.get("chunk_id"))
        if chunk:
            evidence_texts.append(chunk["text"])

    if not evidence_texts:
        return {"score": 0.0, "claims": claims, "judgments": []}

    evidence = "\n".join(evidence_texts)
    judgments = judge_claims(claims, evidence, llm)

    entail = sum(1 for j in judgments if j.get("label") == "entail")
    score = min(entail / len(claims), 1.0) if claims else 1.0
    return {"score": score, "claims": claims, "judgments": judgments}