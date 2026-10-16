from typing import TypedDict
from src.schemas import PatientProfile, Citation, GuidelineChunk
from src.rules.schema import Violation

class AgentState(TypedDict, total=False):
    query: str
    patient: PatientProfile | None
    retrieved: list[GuidelineChunk]
    answer: str
    citations: list[Citation]
    verify_ok: bool
    verify_messages: list[str]
    plan: dict | None
    violations: list[Violation]
    retry_count: int
