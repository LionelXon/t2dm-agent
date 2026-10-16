from typing import TypedDict
from src.schemas import PatientProfile, Citation, GuidelineChunk
from src.rules.schema import Violation


class DietState(TypedDict, total=False):
    patient: PatientProfile
    retrieved: list[GuidelineChunk]
    targets: dict
    meal_plan: dict              # {"meals": [{"name": ..., "items": [{"food":..., "grams":...}]}]}
    nutrition: dict              # compute_meal_nutrition 的结果
    citations: list[Citation]
    answer: str
    violations: list[Violation]
    retry_count: int
    scaled: bool
    scale_factor: float