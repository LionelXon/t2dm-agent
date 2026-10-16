from typing import TypedDict
from src.schemas import PatientProfile, Citation, GuidelineChunk
from src.rules.schema import Violation


class ExerciseState(TypedDict, total=False):
    patient: PatientProfile
    retrieved: list[GuidelineChunk]
    targets: dict
    exercise_plan: dict
    citations: list[Citation]
    answer: str
    violations: list[Violation]
    retry_count: int