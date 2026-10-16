from functools import lru_cache
from src.workflows.graph import build_graph
from src.workflows.diet_graph import build_diet_graph
from src.workflows.exercise_graph import build_exercise_graph


@lru_cache(maxsize=1)
def get_ask_graph():
    return build_graph()


@lru_cache(maxsize=1)
def get_diet_graph():
    return build_diet_graph()


@lru_cache(maxsize=1)
def get_exercise_graph():
    return build_exercise_graph()