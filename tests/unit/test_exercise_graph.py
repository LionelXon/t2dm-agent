import json
from src.schemas import PatientProfile
from src.workflows.exercise_graph import build_exercise_graph


class FakeResp:
    def __init__(self, content): self.content = content


class SequentialFakeLLM:
    def __init__(self, payloads):
        self.payloads = payloads
        self.calls = 0

    def invoke(self, messages):
        p = self.payloads[min(self.calls, len(self.payloads) - 1)]
        self.calls += 1
        return FakeResp(json.dumps(p, ensure_ascii=False))


def _good_plan():
    return {
        "answer": "常规有氧加抗阻方案。",
        "citations": [],
        "exercise_plan": {"sessions": [
            {"day": "周一", "type": "有氧", "activity": "快走", "minutes": 35, "intensity": "moderate"},
            {"day": "周二", "type": "抗阻", "activity": "哑铃", "minutes": 20, "intensity": "moderate"},
            {"day": "周三", "type": "有氧", "activity": "骑车", "minutes": 35, "intensity": "moderate"},
            {"day": "周四", "type": "抗阻", "activity": "弹力带", "minutes": 20, "intensity": "moderate"},
            {"day": "周五", "type": "有氧", "activity": "快走", "minutes": 35, "intensity": "moderate"},
            {"day": "周六", "type": "有氧", "activity": "游泳", "minutes": 45, "intensity": "moderate"},
        ]},
    }


def test_exercise_good_plan_passes():
    llm = SequentialFakeLLM([_good_plan()])
    graph = build_exercise_graph(llm=llm)
    p = PatientProfile(age=55, sex="male", bmi=28)
    out = graph.invoke({"patient": p})
    hard = [v for v in out.get("violations", []) if v.severity == "hard"]
    assert hard == [], [v.message for v in hard]


def test_exercise_insufficient_aerobic_triggers_rewrite():
    bad = {
        "answer": "有氧不足",
        "citations": [],
        "exercise_plan": {"sessions": [
            {"day": "周一", "type": "有氧", "activity": "快走", "minutes": 20, "intensity": "moderate"},
            {"day": "周二", "type": "抗阻", "activity": "哑铃", "minutes": 20, "intensity": "moderate"},
        ]},
    }
    good = _good_plan()
    llm = SequentialFakeLLM([bad, good])
    graph = build_exercise_graph(llm=llm)
    p = PatientProfile(age=55, sex="male", bmi=28)
    out = graph.invoke({"patient": p})
    assert out.get("retry_count", 0) >= 1


def test_exercise_retinopathy_blocks_moderate():
    bad = _good_plan()  # 全是 moderate
    good = {
        "answer": "低强度方案",
        "citations": [],
        "exercise_plan": {"sessions": [
            {"day": "周一", "type": "有氧", "activity": "散步", "minutes": 30, "intensity": "low"},
            {"day": "周二", "type": "有氧", "activity": "慢走", "minutes": 30, "intensity": "low"},
            {"day": "周三", "type": "有氧", "activity": "慢走", "minutes": 30, "intensity": "low"},
            {"day": "周四", "type": "有氧", "activity": "散步", "minutes": 30, "intensity": "low"},
            {"day": "周五", "type": "有氧", "activity": "慢走", "minutes": 30, "intensity": "low"},
        ]},
    }
    llm = SequentialFakeLLM([bad, good])
    graph = build_exercise_graph(llm=llm)
    p = PatientProfile(age=68, sex="female", bmi=26, complications=["增殖期视网膜病变"])
    out = graph.invoke({"patient": p})
    # 至少重写一次，且重写后不应有 CDS-EXE-004
    assert out.get("retry_count", 0) >= 1
    exe004 = [v for v in out.get("violations", []) if v.rule_id == "CDS-EXE-004"]
    assert exe004 == []