import json
from src.workflows.graph import build_graph
from src.schemas import PatientProfile
from tests.unit.test_rule_loop import SequentialFakeLLM


class FakeLLMResponse:
    def __init__(self, content: str):
        self.content = content


class FakeLLM:
    def __init__(self, payload: dict):
        self.payload = payload

    def invoke(self, messages):
        return FakeLLMResponse(json.dumps(self.payload, ensure_ascii=False))


def test_graph_end_to_end_with_fake_llm():
    payload = {
        "answer": "老年人 HbA1c 可放宽至 7.0%~8.0%。",
        "citations": [
            {
                "chunk_id": "mock_003",
                "quote": "年龄 ≥65 岁、健康状态差、有低血糖史者，HbA1c 目标可放宽至 7.0%~8.0%。",
            }
        ],
        "plan": {},
    }
    graph = build_graph(llm=FakeLLM(payload))
    out = graph.invoke({"query": "老年患者 HbA1c 目标"})
    assert "7.0%~8.0%" in out["answer"]
    assert out["verify_ok"] is True
    
def test_disabled_metformin_does_not_retrigger():
    """重写后如果 plan 里不再使用二甲双胍，应能正常退出。"""
    wrong = {
        "answer": "可以使用二甲双胍。",
        "citations": [],
        "plan": {"medications": ["二甲双胍"]},
    }
    right = {
        "answer": "eGFR 28 <30，禁用二甲双胍。",
        "citations": [],
        "plan": {"medications": []},
    }
    llm = SequentialFakeLLM([wrong, right])
    graph = build_graph(llm=llm)
    p = PatientProfile(age=68, bmi=27, egfr=28)
    out = graph.invoke({"query": "eGFR 28 能不能用二甲双胍", "patient": p})
    assert out.get("retry_count", 0) == 1
    hard = [v for v in out.get("violations", []) if v.severity == "hard"]
    assert hard == []