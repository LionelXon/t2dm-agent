import json
from src.nutrition.calculator import diet_targets
from src.nutrition.plan_assert import assert_diet_plan, compute_meal_nutrition
from src.retrieval.hybrid_retriever import HybridRetriever
from src.rules.engine import has_hard_violation
from src.schemas import Citation
from src.workflows.diet_prompts import (
    DIET_SYSTEM_PROMPT,
    build_diet_rewrite_prompt,
    build_diet_user_prompt,
)
from src.workflows.diet_state import DietState
from src.workflows.nodes import extract_json
from src.nutrition.scale import scale_meal_plan


_retriever: HybridRetriever | None = None

def get_retriever() -> HybridRetriever:
    global _retriever
    if _retriever is None:
        _retriever = HybridRetriever()
    return _retriever

def _patient_summary(patient) -> str:
    parts = [
        f"年龄 {patient.age}",
        f"性别 {patient.sex}",
        f"BMI {patient.bmi}",
    ]
    if patient.weight_kg:
        parts.append(f"体重 {patient.weight_kg}kg")
    if patient.ckd_stage:
        parts.append(f"CKD {patient.ckd_stage} (eGFR {patient.egfr})")
    if patient.complications:
        parts.append("并发症：" + "、".join(patient.complications))
    return "；".join(parts)

def retrieve_node(state: DietState) -> DietState:
    r = get_retriever()
    results = r.search("糖尿病 医学营养治疗 碳水 脂肪 蛋白质 食盐", top_k=5)
    state["retrieved"] = [c for c, _ in results]
    return state

def compute_targets_node(state: DietState) -> DietState:
    state["targets"] = diet_targets(state["patient"])
    return state

def generate_meal_plan_node(state: DietState, llm=None) -> DietState:
    if llm is None:
        from src.workflows.llm import get_llm
        llm = get_llm()
    
    user = build_diet_user_prompt(
        _patient_summary(state["patient"]),
        state["targets"],
        state["retrieved"],
    )
    resp = llm.invoke([
        {"role": "system", "content": DIET_SYSTEM_PROMPT},
        {"role": "user", "content": user}
    ])
    text = resp.content if hasattr(resp, "content") else str(resp)
    
    try:
        data = extract_json(text)
    except Exception as e:
        state["answer"] = f"[LLM 输出无法解析] {e}"
        state["meal_plan"] = {"meals": []}
        state["citations"] = []
        return state
    
    state["answer"] = data.get("answer", "")
    state["meal_plan"] = data.get("meal_plan", {"meals": []})
    state["citations"] = [
        Citation(chunk_id=c.get("chunk_id", ""), quote=c.get("quote", ""), rec_id=None)
        for c in data.get("citations", [])
    ]
    return state

def compute_nutrition_node(state: DietState) -> DietState:
    try:
        state["nutrition"] = compute_meal_nutrition(state["meal_plan"])
    except KeyError as e:
        state["nutrition"] = {"meals": [], "total": {}}
        from src.rules.schema import Violation
        state["violations"] = [Violation(
            rule_id="CDS-NUT-FOOD",
            severity="hard",
            message=f"使用了食物库外的食物：{e}",
            evidence="食物库白名单",
        )]
        return state
    return state

def assert_node(state: DietState) -> DietState:
    if state.get("violations"):
        return state
    state["violations"] = assert_diet_plan(state["nutrition"], state["targets"])
    return state

def auto_scale_node(state: DietState) -> DietState:
    if state.get("violations"):
        return state
    target_kcal = state["targets"]["energy"]["energy_target_kcal"]
    new_plan, scaled, factor = scale_meal_plan(state["meal_plan"], target_kcal)
    if scaled:
        state["meal_plan"] = new_plan
        state["nutrition"] = compute_meal_nutrition(new_plan)
        state["scaled"] = True
        state["scale_factor"] = factor
    else:
        state["scaled"] = False
        state["scale_factor"] = factor
    return state

def rewrite_node(state: DietState, llm=None) -> DietState:
    if llm is None:
        from src.workflows.llm import get_llm
        llm = get_llm()

    user = build_diet_user_prompt(
        _patient_summary(state["patient"]),
        state["targets"],
        state["retrieved"],
    )
    rewrite = build_diet_rewrite_prompt(
        state["violations"],
        nutrition=state.get("nutrition"),
        targets=state.get("targets"),
    )

    resp = llm.invoke([
        {"role": "system", "content": DIET_SYSTEM_PROMPT},
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
    state["meal_plan"] = data.get("meal_plan", {"meals": []})
    state["citations"] = [
        Citation(chunk_id=c.get("chunk_id", ""), quote=c.get("quote", ""), rec_id=None)
        for c in data.get("citations", [])
    ]
    # 清掉旧违规，让 assert_node 重新算
    state["violations"] = []
    return state

def increment_retry(state: DietState) -> DietState:
    state["retry_count"] = state.get("retry_count", 0) + 1
    return state