from fastapi.testclient import TestClient

from src.api.main import app
from src.api.deps import get_ask_graph, get_diet_graph, get_exercise_graph
from src.schemas import Citation


class FakeGraph:
    def __init__(self, out):
        self.out = out

    def invoke(self, state):
        return self.out


def test_healthz():
    client = TestClient(app)
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_ask_basic():
    fake = FakeGraph({
        "answer": "老年患者 HbA1c 可放宽至 7.0%~8.0%。",
        "citations": [Citation(chunk_id="mock_003", quote="放宽至 7.0%~8.0%")],
        "verify_ok": True,
        "verify_messages": [],
        "violations": [],
        "retry_count": 0,
    })
    app.dependency_overrides[get_ask_graph] = lambda: fake
    try:
        client = TestClient(app)
        r = client.post("/ask", json={"query": "老年 HbA1c 目标"})
        assert r.status_code == 200
        body = r.json()
        assert "7.0%~8.0%" in body["answer"]
        assert len(body["citations"]) == 1
        assert body["verify_ok"] is True
    finally:
        app.dependency_overrides.clear()


def test_ask_missing_query_returns_422():
    client = TestClient(app)
    r = client.post("/ask", json={})
    assert r.status_code == 422


def test_diet_with_patient():
    fake = FakeGraph({
        "answer": "参考指南的平衡餐单。",
        "citations": [],
        "meal_plan": {"meals": [{"name": "早餐", "items": [{"food": "燕麦", "grams": 60}]}]},
        "nutrition": {"total": {"kcal": 2000, "carb_ratio": 0.55}},
        "violations": [],
        "retry_count": 0,
        "scaled": True,
        "scale_factor": 1.1,
    })
    app.dependency_overrides[get_diet_graph] = lambda: fake
    try:
        client = TestClient(app)
        r = client.post("/plan/diet", json={
            "patient": {"age": 55, "sex": "male", "bmi": 28, "weight_kg": 85, "height_cm": 175},
        })
        assert r.status_code == 200
        body = r.json()
        assert body["scaled"] is True
        assert body["nutrition"]["total"]["kcal"] == 2000
    finally:
        app.dependency_overrides.clear()


def test_exercise_missing_patient_returns_422():
    client = TestClient(app)
    r = client.post("/plan/exercise", json={})
    assert r.status_code == 422