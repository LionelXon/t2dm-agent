from pydantic import BaseModel, Field
from src.schemas import PatientProfile

class Violation(BaseModel):
    rule_id: str
    severity: str  # hard / soft
    message: str
    evidence: str | None = None  # 指南依据，便于溯源

class RuleResult(BaseModel):
    violations: list[Violation] = Field(default_factory=list)
    
    @property
    def passed(self) -> bool:
        return len(self.violations) == 0


