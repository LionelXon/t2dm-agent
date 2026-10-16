from pydantic import BaseModel, Field
from src.schemas import PatientProfile, Citation


class AskRequest(BaseModel):
    query: str
    patient: PatientProfile | None = None


class PlanRequest(BaseModel):
    patient: PatientProfile


class AskResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    verify_ok: bool = True
    verify_messages: list[str] = Field(default_factory=list)
    violations: list[dict] = Field(default_factory=list)
    retry_count: int = 0


class DietResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    meal_plan: dict = Field(default_factory=dict)
    nutrition: dict = Field(default_factory=dict)
    violations: list[dict] = Field(default_factory=list)
    retry_count: int = 0
    scaled: bool = False
    scale_factor: float = 1.0


class ExerciseResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    exercise_plan: dict = Field(default_factory=dict)
    violations: list[dict] = Field(default_factory=list)
    retry_count: int = 0