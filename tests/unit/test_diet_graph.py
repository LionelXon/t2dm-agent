import json
from src.nutrition.food_db import FOOD_DB
from src.schemas import PatientProfile
from src.workflows.diet_graph import build_diet_graph


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


def _balanced_payload():
    return {
        "answer": "参考指南的平衡餐单。",
        "citations": [],
        "meal_plan": {"meals": [
            {"name": "早餐", "items": [
                {"food": "燕麦", "grams": 80},
                {"food": "牛奶", "grams": 250},
                {"food": "鸡蛋", "grams": 50},
                {"food": "核桃", "grams": 20},
                {"food": "苹果", "grams": 150},
            ]},
            {"name": "午餐", "items": [
                {"food": "白米饭", "grams": 300},
                {"food": "鸡胸肉", "grams": 100},
                {"food": "西兰花", "grams": 200},
                {"food": "橄榄油", "grams": 10},
            ]},
            {"name": "晚餐", "items": [
                {"food": "红薯", "grams": 350},
                {"food": "豆腐", "grams": 100},
                {"food": "青菜", "grams": 200},
                {"food": "橄榄油", "grams": 8},
            ]},
        ]},
    }


def test_diet_graph_passes_with_balanced_plan():
    llm = SequentialFakeLLM([_balanced_payload()])
    graph = build_diet_graph(llm=llm)
    p = PatientProfile(
        age=55, sex="male", bmi=28,
        weight_kg=85, height_cm=175,
        activity_level="moderate",
    )
    out = graph.invoke({"patient": p})
    hard = [v for v in out.get("violations", []) if v.severity == "hard"]
    assert hard == [], [v.message for v in hard]


def test_diet_graph_rewrites_on_bad_first_plan():
    bad = {
        "answer": "高碳水餐单",
        "citations": [],
        "meal_plan": {"meals": [
            {"name": "早餐", "items": [{"food": "白米饭", "grams": 500}]},
        ]},
    }
    good = _balanced_payload()
    llm = SequentialFakeLLM([bad, good])
    graph = build_diet_graph(llm=llm)
    p = PatientProfile(
        age=55, sex="male", bmi=28,
        weight_kg=85, height_cm=175,
        activity_level="moderate",
    )
    out = graph.invoke({"patient": p})
    assert out.get("retry_count", 0) >= 1
    hard = [v for v in out.get("violations", []) if v.severity == "hard"]
    assert hard == [], [v.message for v in hard]


def test_diet_graph_rejects_unknown_food():
    bad = {
        "answer": "编造食物",
        "citations": [],
        "meal_plan": {"meals": [
            {"name": "早餐", "items": [{"food": "火箭果", "grams": 100}]},
        ]},
    }
    llm = SequentialFakeLLM([bad])
    graph = build_diet_graph(llm=llm)
    p = PatientProfile(
        age=55, sex="male", bmi=28,
        weight_kg=85, height_cm=175,
        activity_level="moderate",
    )
    out = graph.invoke({"patient": p})
    assert any(v.rule_id == "CDS-NUT-FOOD" for v in out["violations"])