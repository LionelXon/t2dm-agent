# src/contracts/guideline.py
from pydantic import BaseModel, Field
from src.schemas import PatientProfile


class KnowledgeItem(BaseModel):
    """对外暴露的指南知识条目。"""
    id: str
    type: str                    # 知识类型
    content: str                 # 推荐内容
    applicable_condition: str    # 适用条件
    evidence_level: str | None   # 证据等级
    source: str                  # 来源定位
    entities: list[str]          # 关联实体


class RetrievalRequest(BaseModel):
    query: str
    top_k: int = 3
    filters: dict = Field(default_factory=dict)  # 如 {"type": "药物推荐"}


class RetrievalResponse(BaseModel):
    items: list[KnowledgeItem]
    query: str
    elapsed_ms: float


class RuleViolation(BaseModel):
    rule_id: str
    severity: str                # hard / soft
    message: str
    evidence: str | None
    source_knowledge_id: str | None  # 关联到知识库 ID，可溯源


class RuleCheckRequest(BaseModel):
    patient: PatientProfile
    plan: dict = Field(default_factory=dict)


class RuleCheckResponse(BaseModel):
    violations: list[RuleViolation]
    passed: bool                 # 无 hard 违规即为 True


class CitationCheckRequest(BaseModel):
    answer: str
    citations: list[dict]


class CitationCheckResponse(BaseModel):
    ok: bool
    precision: float
    failed: list[dict]           # 未通过核验的引用


class ComplianceRequest(BaseModel):
    plan: dict
    domain: str                  # "diet" / "exercise" / "medication"


class ComplianceResponse(BaseModel):
    passed: bool
    violations: list[RuleViolation]
    checked_rules: list[str]