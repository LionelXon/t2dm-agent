from src.retrieval.hybrid_retriever import HybridRetriever


def test_retrieve_hba1c_elderly():
    r = HybridRetriever()
    results = r.search("老年患者 HbA1c 目标应该放宽到多少", top_k=3)
    texts = [c.text for c, _ in results]
    assert any("7.0%~8.0%" in t or "7.0%-8.0%" in t for t in texts)


def test_retrieve_metformin_egfr():
    r = HybridRetriever()
    results = r.search("eGFR 28 能不能用二甲双胍", top_k=3)
    texts = [c.text for c, _ in results]
    assert any("eGFR <30" in t and "禁用" in t for t in texts)


def test_retrieve_exercise():
    r = HybridRetriever()
    results = r.search("每周运动多少分钟", top_k=3)
    texts = [c.text for c, _ in results]
    assert any("150 分钟" in t for t in texts)