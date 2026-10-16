from pydantic import BaseModel, Field

class PatientProfile(BaseModel):
    age: int
    sex: str = "male"              # male / female
    bmi: float
    weight_kg: float | None = None
    height_cm: float | None = None
    activity_level: str = "moderate"  # sedentary / light / moderate / active
    hba1c: float | None = None
    egfr: float | None = None
    ckd_stage: str | None = None
    hypoglycemia_history: bool = False
    health_status: str = "good"
    complications: list[str] = Field(default_factory=list)
    
    def resolved_weight_kg(self) -> float | None:
        if self.weight_kg is not None:
            return self.weight_kg
        if self.height_cm is not None:
            return self.bmi * (self.height_cm / 100) ** 2
        return None
    
class GuidelineChunk(BaseModel):
    chunk_id: str
    guide_name: str
    year: int
    section: str
    rec_id: str | None = None
    evidence_level: str | None = None
    page: int | None = None
    text: str
    
class Citation(BaseModel):
    rec_id: str | None = None
    chunk_id: str
    quote: str
    
class AgentResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    plan: dict | None = None
    assertions: list[dict] = Field(default_factory=list)