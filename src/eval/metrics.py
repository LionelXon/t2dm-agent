def context_recall_at_k(retrieved_ids: list[str], gold_ids: list[str], k: int) -> float:
    """top-k 中命中 gold 的比例。gold 为空时返回 1.0。"""
    if not gold_ids:
        return 1.0
    top_k = set(retrieved_ids[:k])
    hit = len(top_k & set(gold_ids))
    return hit / len(gold_ids)


def context_precision_at_k(retrieved_ids: list[str], gold_ids: list[str], k: int) -> float:
    """top-k 中属于 gold 的比例。"""
    top_k = retrieved_ids[:k]
    if not top_k:
        return 1.0
    gold_set = set(gold_ids)
    hit = sum(1 for cid in top_k if cid in gold_set)
    return hit / len(top_k)


def citation_precision(citations: list[dict], chunk_map: dict) -> float:
    """引用中：chunk_id 存在 且 quote 是原文子串 的比例。"""
    if not citations:
        return 1.0
    ok = 0
    for c in citations:
        chunk = chunk_map.get(c.get("chunk_id"))
        if chunk is None:
            continue
        if _norm(c.get("quote", "")) in _norm(chunk["text"]):
            ok += 1
    return ok / len(citations)


def citation_recall(citations: list[dict], gold_chunk_ids: list[str]) -> float:
    """gold chunk 中被引用到的比例。"""
    if not gold_chunk_ids:
        return 1.0
    cited = {c.get("chunk_id") for c in citations}
    hit = len(cited & set(gold_chunk_ids))
    return hit / len(gold_chunk_ids)


def _norm(s: str) -> str:
    import re
    return re.sub(r"\s+", "", s or "")