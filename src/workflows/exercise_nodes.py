from src.exercise.assert_ import assert_exercise_plan
from src.nutrition.exercise_target import exercise_targets
from src.retrieval.hybrid_retriever import HybridRetriever
from src.rules.engine import has_hard_violation
from src.schemas import Citation
from src.workflows.exercise_prompts import (
    EXERCISE_SYSTEM_PROMPT,
    build_exercise_rewrite_prompt,
    build_exercise_user_prompt,
)
from src.workflows.exercise_state import ExerciseState
from src.workflows.nodes import extract_json


_retriever: HybridRetriever | None = None


def get_retriever() -> HybridRetriever:
    global _retriever
    if _retriever is None:
        _retriever = HybridRetriever()
    return _retriever


def _patient_summary(patient) -> str:
    parts = [f"年龄 {patient.age}", f"性别 {patient.sex}", f"BMI {patient.bmi}"]
    if patient.complications:
        parts.append("并发症：" + "、".join(patient.complications))
    return "；".join(parts)


def retrieve_node(state: ExerciseState) -> ExerciseState:
    r = get_retriever()
    results = r.search("糖尿病 运动治疗 有氧 抗阻 禁忌", top_k=5)
    state["retrieved"] = [c for c, _ in results]
    return state


def compute_targets_node(state: ExerciseState) -> ExerciseState:
    state["targets"] = exercise_targets(state["patient"])
    return state


def generate_node(state: ExerciseState, llm=None) -> ExerciseState:
    if llm is None:
        from src.workflows.llm import get_llm
        llm = get_llm()
    user = build_exercise_user_prompt(
        _patient_summary(state["patient"]),
        state["targets"],
        state["retrieved"],
    )
    resp = llm.invoke([
        {"role": "system", "content": EXERCISE_SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ])
    text = resp.content if hasattr(resp, "content") else str(resp)
    try:
        data = extract_json(text)
    except Exception as e:
        state["answer"] = f"[LLM 输出无法解析] {e}"
        state["exercise_plan"] = {"sessions": []}
        state["citations"] = []
        return state

    state["answer"] = data.get("answer", "")
    state["exercise_plan"] = data.get("exercise_plan", {"sessions": []})
    state["citations"] = [
        Citation(chunk_id=c.get("chunk_id", ""), quote=c.get("quote", ""), rec_id=None)
        for c in data.get("citations", [])
    ]
    return state


def assert_node(state: ExerciseState) -> ExerciseState:
    state["violations"] = assert_exercise_plan(state["exercise_plan"], state["targets"])
    return state


def rewrite_node(state: ExerciseState, llm=None) -> ExerciseState:
    if llm is None:
        from src.workflows.llm import get_llm
        llm = get_llm()
    user = build_exercise_user_prompt(
        _patient_summary(state["patient"]),
        state["targets"],
        state["retrieved"],
    )
    rewrite = build_exercise_rewrite_prompt(state["violations"])
    resp = llm.invoke([
        {"role": "system", "content": EXERCISE_SYSTEM_PROMPT},
        {"role": "user", "content": user},
        {"role": "user", "content": rewrite},
    ])
    text = resp.content if hasattr(resp, "content") else str(resp)
    try:
        data = extract_json(text)
    except Exception as e:
        state["answer"] = f"[重写失败] {e}"
        return state
    state["answer"] = data.get("answer", "")
    state["exercise_plan"] = data.get("exercise_plan", {"sessions": []})
    state["citations"] = [
        Citation(chunk_id=c.get("chunk_id", ""), quote=c.get("quote", ""), rec_id=None)
        for c in data.get("citations", [])
    ]
    state["violations"] = []
    return state


def increment_retry(state: ExerciseState) -> ExerciseState:
    state["retry_count"] = state.get("retry_count", 0) + 1
    return state