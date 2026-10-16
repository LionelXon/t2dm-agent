from src.eval.metrics import (
    context_recall_at_k,
    context_precision_at_k,
    citation_precision,
    citation_recall,
)

def test_context_recall_all_hit():
    assert context_recall_at_k(["a", "b", "c"], ["a"], 3) == 1.0


def test_context_recall_partial():
    assert context_recall_at_k(["a", "x", "y"], ["a", "b"], 3) == 0.5


def test_context_recall_at_k_limits():
    # gold 在 top-3 之外
    assert context_recall_at_k(["x", "y", "z", "a"], ["a"], 3) == 0.0


def test_context_precision():
    assert context_precision_at_k(["a", "x", "y"], ["a"], 3) == 1 / 3


def test_citation_precision_ok():
    chunk_map = {"c1": {"text": "推荐意见：HbA1c 目标 <7.0%。"}}
    cites = [{"chunk_id": "c1", "quote": "HbA1c 目标 <7.0%"}]
    assert citation_precision(cites, chunk_map) == 1.0


def test_citation_precision_quote_mismatch():
    chunk_map = {"c1": {"text": "原文不含这句"}}
    cites = [{"chunk_id": "c1", "quote": "原文根本没有"}]
    assert citation_precision(cites, chunk_map) == 0.0


def test_citation_recall():
    cites = [{"chunk_id": "c1", "quote": "x"}]
    assert citation_recall(cites, ["c1", "c2"]) == 0.5