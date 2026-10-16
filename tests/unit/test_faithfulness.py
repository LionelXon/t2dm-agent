import json
from src.eval.faithfulness import split_sentences, compute_faithfulness


class FakeResp:
    def __init__(self, content): self.content = content


class FakeJudgeLLM:
    def __init__(self, judgments):
        self.judgments = judgments

    def invoke(self, messages):
        return FakeResp(json.dumps({"judgments": self.judgments}, ensure_ascii=False))


def test_split_sentences():
    s = split_sentences("HbA1c 目标 <7.0%。老年患者可放宽。")
    assert s == ["HbA1c 目标 <7.0%", "老年患者可放宽"]


def test_split_sentences_short_filtered():
    s = split_sentences("好。这是一个完整的句子。")
    assert "好" not in s
    assert "这是一个完整的句子" in s


def test_faithfulness_all_entail():
    llm = FakeJudgeLLM([
        {"idx": 0, "label": "entail", "reason": "ok"},
        {"idx": 1, "label": "entail", "reason": "ok"},
    ])
    chunk_map = {"c1": {"text": "一般成人 HbA1c 目标 <7.0%；老年可放宽。"}}
    citations = [{"chunk_id": "c1", "quote": "一般成人 HbA1c 目标 <7.0%"}]
    out = compute_faithfulness(
        "HbA1c 目标 <7.0%。老年患者放宽。",
        citations, chunk_map, llm,
    )
    assert out["score"] == 1.0


def test_faithfulness_partial():
    llm = FakeJudgeLLM([
        {"idx": 0, "label": "entail"},
        {"idx": 1, "label": "neutral"},
    ])
    chunk_map = {"c1": {"text": "一般成人 HbA1c 目标 <7.0%。"}}
    citations = [{"chunk_id": "c1", "quote": "x"}]
    out = compute_faithfulness(
        "HbA1c 目标 <7.0%。随机加一句。",
        citations, chunk_map, llm,
    )
    assert out["score"] == 0.5


def test_faithfulness_no_citations():
    llm = FakeJudgeLLM([])
    out = compute_faithfulness("HbA1c 目标 <7.0%。", [], {"c1": {"text": "x"}}, llm)
    assert out["score"] == 0.0