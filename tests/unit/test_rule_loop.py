import json
from src.schemas import PatientProfile
from src.workflows.graph import build_graph


class FakeLLMResponse:
    def __init__(self, content):
        self.content = content


class SequentialFakeLLM:
    """第一次给错答案，第二次给正确答案。"""
    def __init__(self, payloads):
        self.payloads = payloads
        self.calls = 0

    def invoke(self, messages):
        payload = self.payloads[min(self.calls, len(self.payloads) - 1)]
        self.calls += 1
        return FakeLLMResponse(json.dumps(payload, ensure_ascii=False))


def test_metformin_egfr28_triggers_rewrite():
    wrong = {
        "answer": "可以使用二甲双胍，但应减量并密切监测。",
        "citations": [
            {"chunk_id": "mock_006",
            "quote": "eGFR <30 mL/min/1.73m² 禁用二甲双胍；eGFR 30~45 应减量并密切监测。"}
        ],
        "plan": {"medications": ["二甲双胍"]},   # 错误方案：使用了二甲双胍
    }
    right = {
        "answer": "eGFR 28 <30，禁用二甲双胍。",
        "citations": [
            {"chunk_id": "mock_006", "quote": "eGFR <30 mL/min/1.73m² 禁用二甲双胍"}
        ],
        "plan": {"medications": []},              # 修正方案：不使用
    }
    llm = SequentialFakeLLM([wrong, right])
    graph = build_graph(llm=llm)
    p = PatientProfile(age=68, bmi=27, egfr=28)
    out = graph.invoke({"query": "eGFR 28 能不能用二甲双胍", "patient": p})
    assert out.get("retry_count", 0) >= 1
    assert "禁用" in out["answer"]