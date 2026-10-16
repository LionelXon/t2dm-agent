import json
import re
from json_repair import repair_json
from src.retrieval.hybrid_retriever import HybridRetriever
from src.schemas import Citation, GuidelineChunk
from src.workflows.prompts import SYSTEM_PROMPT, build_user_prompt
from src.workflows.state import AgentState
from src.rules.engine import evaluate_rules, has_hard_violation

_retriever: HybridRetriever | None = None

def get_retriever() -> HybridRetriever:
    global _retriever
    if _retriever is None:
        _retriever = HybridRetriever()
    return _retriever

def extract_json(text: str) -> dict:
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if m:
        text = m.group(1)
    else:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start : end + 1]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return json.loads(repair_json(text))

def retrieve_node(state: AgentState, top_k: int = 3) -> AgentState:
    from src.retrieval.query_rewriter import rewrite_query
    from src.workflows.llm import get_llm
    
    print(f"  [retrieve] query={state['query']!r}", flush=True)
    r = get_retriever()
    print(f"  [retrieve] retriever loaded", flush=True)
    results = r.search(state["query"], top_k=top_k)
    state["retrieved"] = [c for c, _ in results]
    
    # llm = get_llm(temperature=0.0)
    # print(f"  [retrieve] rewriting query...", flush=True)
    # queries = rewrite_query(state["query"], llm)
    # print(f"  [retrieve] rewritten: {queries}", flush=True)
    # queries = [state["query"]] + queries  # 原始 query 也保留
    # print(f"  [retrieve] searching {len(queries)} queries", flush=True)
    # results = r.search_multi(queries, top_k=top_k)
    # print(f"  [retrieve] got {len(results)} results", flush=True)
    # state["retrieved"] = [c for c, _ in results]

    return state

def generate_node(state: AgentState, llm=None) -> AgentState:
    if llm is None:
        from src.workflows.llm import get_llm
        llm = get_llm()
    
    print(f"  [generate] prompt len={len(build_user_prompt(state['query'], state['retrieved']))}", flush=True)    
    user_prompt = build_user_prompt(state["query"], state["retrieved"])
    resp = llm.invoke([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ])
    print(f"  [generate] got response", flush=True)
    text = resp.content if hasattr(resp, "content") else str(resp)
    
    try:
        data = extract_json(text)
    except Exception as e:
        state["answer"] = f"[LLM 输出无法解析为 JSON] {e}\n原始输出：{text[:300]}"
        state["citations"] = []
        return state
    
    state["answer"] = data.get("answer", "")
    state["citations"] = [
        Citation(
            chunk_id=c.get("chunk_id", ""),
            quote=c.get("quote", ""),
            rec_id=None,
        )
        for c in data.get("citations", [])
    ]
    plan = data.get("plan")
    if isinstance(plan, dict):
        # 清掉所有值为 None / 空列表的字段，保持干净
        state["plan"] = {k: v for k, v in plan.items() if v not in (None, [], "")}
    else:
        state["plan"] = {}
        
    return state

def _normalize(s: str) -> str:
    return re.sub(r"\s+", "", s)

def verify_node(state: AgentState) -> AgentState:
    """核对每条 citation 的 chunk_id 存在、quote 是原文子串。"""
    messages: list[str] = []
    chunk_map: dict[str, GuidelineChunk] = {c.chunk_id: c for c in state["retrieved"]}

    ok = True
    for i, cite in enumerate(state["citations"]):
        chunk = chunk_map.get(cite.chunk_id)
        if chunk is None:
            ok = False
            messages.append(f"citation[{i}] chunk_id={cite.chunk_id} 不在检索结果中")
            continue
        if _normalize(cite.quote) not in _normalize(chunk.text):
            ok = False
            messages.append(f"citation[{i}] quote 不是原文子串: {cite.quote[:40]}")

    if not state["citations"] and state["retrieved"]:
        messages.append("答案无引用，但存在检索结果，建议人工复核")

    state["verify_ok"] = ok
    state["verify_messages"] = messages
    return state

def rule_check_node(state: AgentState) -> AgentState:
    patient = state.get("patient")
    if patient is None:
        state["violations"] = []
        return state

    plan = state.get("plan") or {}
    state["violations"] = evaluate_rules(patient, plan)
    return state

def _extract_medications(text: str) -> list[str]:
    meds = []
    if "二甲双胍" in text or "metformin" in text.lower():
        meds.append("二甲双胍")
    return meds

def _extract_weekly_minutes(text: str) -> int | None:
    import re
    m = re.search(r"(\d+)\s*分钟", text)
    return int(m.group(1)) if m else None

def _extract_ratio(text: str, label: str) -> float | None:
    import re
    m = re.search(rf"{label}[^0-9]*(\d{{1,2}})\s*%", text)
    return int(m.group(1)) / 100 if m else None

def _extract_salt(text: str) -> float | None:
    import re
    m = re.search(r"食盐[^0-9]*([\d.]+)\s*g", text)
    return float(m.group(1)) if m else None

def rewrite_node(state: AgentState, llm=None) -> AgentState:
    if llm is None:
        from src.workflows.llm import get_llm
        llm = get_llm()

    violation_text = "\n".join(
        f"- [{v.severity}] {v.rule_id}: {v.message}（依据：{v.evidence}）"
        for v in state.get("violations", [])
    )
    rewrite_prompt = f"""你上一次的回答违反了以下硬规则：
{violation_text}

请依据【指南片段】重新回答，必须严格遵守上述规则。
仍然输出相同 JSON 结构，plan 里只写你实际建议执行的方案。"""

    user_prompt = build_user_prompt(state["query"], state["retrieved"])
    resp = llm.invoke([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
        {"role": "user", "content": rewrite_prompt},
    ])
    text = resp.content if hasattr(resp, "content") else str(resp)

    try:
        data = extract_json(text)
        state["answer"] = data.get("answer", "")
        state["citations"] = [
            Citation(chunk_id=c.get("chunk_id", ""), quote=c.get("quote", ""), rec_id=None)
            for c in data.get("citations", [])
        ]
        plan = data.get("plan")
        if isinstance(plan, dict):
            state["plan"] = {k: v for k, v in plan.items() if v not in (None, [], "")}
    except Exception as e:
        state["answer"] = f"[重写失败] {e}"
    return state
