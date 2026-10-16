from functools import partial
from langgraph.graph import StateGraph, START, END

from src.workflows.nodes import (
    retrieve_node, generate_node, verify_node,
    rule_check_node, rewrite_node,
)
from src.workflows.state import AgentState

MAX_RETRY = 2

def route_after_verify(state: AgentState) -> str:
    if not state.get("verify_ok", True):
        return "end"
    if state.get("patient") is None:
        return "end"          # 没有患者信息，跳过规则
    return "rule_check"

def route_after_rule(state: AgentState) -> str:
    from src.rules.engine import has_hard_violation
    v = state.get("violations", [])
    if has_hard_violation(v) and state.get("retry_count", 0) < MAX_RETRY:
        return "rewrite"
    return "end"

def increment_retry(state: AgentState) -> AgentState:
    state["retry_count"] = state.get("retry_count", 0) + 1
    return state

def build_graph(llm=None):
    g = StateGraph(AgentState)
    g.add_node("retrieve", retrieve_node)
    g.add_node("generate", partial(generate_node, llm=llm))
    g.add_node("verify", verify_node)
    g.add_node("rule_check", rule_check_node)
    g.add_node("rewrite", partial(rewrite_node, llm=llm))
    g.add_node("increment_retry", increment_retry)

    g.add_edge(START, "retrieve")
    g.add_edge("retrieve", "generate")
    g.add_edge("generate", "verify")
    g.add_conditional_edges("verify", route_after_verify, {
        "rule_check": "rule_check",
        "end": END,
    })
    g.add_conditional_edges("rule_check", route_after_rule, {
        "rewrite": "rewrite",
        "end": END,
    })
    g.add_edge("rewrite", "increment_retry")
    g.add_edge("increment_retry", "rule_check")
    

    return g.compile()