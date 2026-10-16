import logging
from fastapi import FastAPI, Depends
from src.api.deps import get_ask_graph, get_diet_graph, get_exercise_graph
from src.api.schemas import (
    AskRequest, AskResponse,
    PlanRequest, DietResponse, ExerciseResponse,
)


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("t2dm-agent")

app = FastAPI(title="T2DM Agent", version="0.1.0")


def _violations_to_dicts(violations) -> list[dict]:
    return [
        {"rule_id": v.rule_id, "severity": v.severity, "message": v.message, "evidence": v.evidence}
        for v in violations
    ]


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest, graph=Depends(get_ask_graph)):
    state = {"query": req.query}
    if req.patient is not None:
        state["patient"] = req.patient
    out = graph.invoke(state)
    logger.info("ask query=%r citations=%d retry=%d", req.query, len(out.get("citations", [])), out.get("retry_count", 0))
    return AskResponse(
        answer=out.get("answer", ""),
        citations=out.get("citations", []),
        verify_ok=out.get("verify_ok", True),
        verify_messages=out.get("verify_messages", []),
        violations=_violations_to_dicts(out.get("violations", [])),
        retry_count=out.get("retry_count", 0),
    )


@app.post("/plan/diet", response_model=DietResponse)
def plan_diet(req: PlanRequest, graph=Depends(get_diet_graph)):
    out = graph.invoke({"patient": req.patient})
    logger.info("diet patient age=%d retry=%d scaled=%s", req.patient.age, out.get("retry_count", 0), out.get("scaled", False))
    return DietResponse(
        answer=out.get("answer", ""),
        citations=out.get("citations", []),
        meal_plan=out.get("meal_plan", {}),
        nutrition=out.get("nutrition", {}),
        violations=_violations_to_dicts(out.get("violations", [])),
        retry_count=out.get("retry_count", 0),
        scaled=out.get("scaled", False),
        scale_factor=out.get("scale_factor", 1.0),
    )


@app.post("/plan/exercise", response_model=ExerciseResponse)
def plan_exercise(req: PlanRequest, graph=Depends(get_exercise_graph)):
    out = graph.invoke({"patient": req.patient})
    logger.info("exercise patient age=%d retry=%d", req.patient.age, out.get("retry_count", 0))
    return ExerciseResponse(
        answer=out.get("answer", ""),
        citations=out.get("citations", []),
        exercise_plan=out.get("exercise_plan", {}),
        violations=_violations_to_dicts(out.get("violations", [])),
        retry_count=out.get("retry_count", 0),
    )


@app.get("/healthz")
def healthz():
    return {"ok": True}