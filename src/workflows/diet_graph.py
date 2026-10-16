from functools import partial
from langgraph.graph import StateGraph, START, END

from src.rules.engine import has_hard_violation
from src.workflows.diet_nodes import (
    retrieve_node,
    compute_targets_node,
    generate_meal_plan_node,
    compute_nutrition_node,
    assert_node,
    rewrite_node,
    increment_retry,
    auto_scale_node,
)
from src.workflows.diet_state import DietState


MAX_RETRY = 2

def route_after_assert(state: DietState) -> str:
    v = state.get("violations", [])
    if has_hard_violation(v) and state.get("retry_count", 0) < MAX_RETRY:
        return "rewrite"
    return "end"

def build_diet_graph(llm=None):
    g = StateGraph(DietState)
    g.add_node("retrieve", retrieve_node)
    g.add_node("targets", compute_targets_node)
    g.add_node("generate", partial(generate_meal_plan_node, llm=llm))
    g.add_node("nutrition", compute_nutrition_node)
    g.add_node("scale", auto_scale_node)
    g.add_node("assert", assert_node)
    g.add_node("rewrite", partial(rewrite_node, llm=llm))
    g.add_node("retry", increment_retry)

    g.add_edge(START, "retrieve")
    g.add_edge("retrieve", "targets")
    g.add_edge("targets", "generate")
    g.add_edge("generate", "nutrition")
    g.add_edge("nutrition", "scale")
    g.add_edge("scale", "assert")
    g.add_conditional_edges("assert", route_after_assert, {
        "rewrite": "rewrite",
        "end": END,
    })
    
    g.add_edge("rewrite", "retry")
    g.add_edge("retry", "nutrition")
    
    return g.compile()