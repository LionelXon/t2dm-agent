import time
from src.contracts.guideline import (
    KnowledgeItem, RetrievalRequest, RetrievalResponse,
    RuleCheckRequest, RuleCheckResponse, RuleViolation,
    CitationCheckRequest, CitationCheckResponse,
    ComplianceRequest, ComplianceResponse,
)
from src.rules.engine import evaluate_rules, has_hard_violation
from src.workflows.nodes import get_retriever


class GuidelineService:
    """指南能力服务。所有对外能力的唯一入口。"""

    def __init__(self):
        self._retriever = None

    @property
    def retriever(self):
        if self._retriever is None:
            self._retriever = get_retriever()
        return self._retriever

    # ---------- 能力1：知识检索 ----------
    def retrieve(self, req: RetrievalRequest) -> RetrievalResponse:
        t0 = time.time()
        results = self.retriever.search(req.query, top_k=req.top_k * 2)
        items = []
        for chunk, _ in results:
            # 过滤
            if req.filters.get("type") and chunk.section != req.filters["type"]:
                continue
            items.append(self._chunk_to_item(chunk))
            if len(items) >= req.top_k:
                break
        return RetrievalResponse(
            items=items,
            query=req.query,
            elapsed_ms=(time.time() - t0) * 1000,
        )

    # ---------- 能力2：规则执行 ----------
    def check_rules(self, req: RuleCheckRequest) -> RuleCheckResponse:
        violations = evaluate_rules(req.patient, req.plan)
        return RuleCheckResponse(
            violations=[self._to_violation(v) for v in violations],
            passed=not has_hard_violation(violations),
        )

    # ---------- 能力3：引用核验 ----------
    def check_citations(self, req: CitationCheckRequest) -> CitationCheckResponse:
        from src.eval.metrics import citation_precision
        chunk_map = self._load_chunk_map()
        prec = citation_precision(req.citations, chunk_map)
        failed = [
            c for c in req.citations
            if not self._citation_ok(c, chunk_map)
        ]
        return CitationCheckResponse(
            ok=prec >= 0.95,
            precision=prec,
            failed=failed,
        )

    # ---------- 能力4：合规报告 ----------
    def check_compliance(self, req: ComplianceRequest) -> ComplianceResponse:
        # 按 domain 选择规则子集
        all_violations = evaluate_rules(
            patient=self._extract_patient(req.plan),
            plan=req.plan,
        )
        domain_rules = self._rules_for_domain(req.domain)
        relevant = [v for v in all_violations if v.rule_id in domain_rules]
        return ComplianceResponse(
            passed=not any(v.severity == "hard" for v in relevant),
            violations=[self._to_violation(v) for v in relevant],
            checked_rules=domain_rules,
        )

    # ---------- 能力5：知识查询 ----------
    def get_knowledge(self, knowledge_id: str) -> KnowledgeItem | None:
        chunk_map = self._load_chunk_map()
        chunk = chunk_map.get(knowledge_id)
        return self._chunk_to_item(chunk) if chunk else None

    # ---------- 内部工具 ----------
    def _chunk_to_item(self, chunk) -> KnowledgeItem:
        return KnowledgeItem(
            id=chunk.chunk_id,
            type=chunk.section,
            content=chunk.text,
            applicable_condition="",
            evidence_level=chunk.evidence_level,
            source=f"Page {chunk.page}" if chunk.page else "",
            entities=[],
        )

    def _to_violation(self, v) -> RuleViolation:
        return RuleViolation(
            rule_id=v.rule_id,
            severity=v.severity,
            message=v.message,
            evidence=v.evidence,
            source_knowledge_id=self._rule_to_knowledge(v.rule_id),
        )

    def _load_chunk_map(self):
        import json
        from pathlib import Path
        m = {}
        for line in Path("data/index/chunks.jsonl").read_text(encoding="utf-8").splitlines():
            if line.strip():
                c = json.loads(line)
                m[c["chunk_id"]] = type("C", (), c)()
        return m

    def _citation_ok(self, cite, chunk_map):
        import re
        chunk = chunk_map.get(cite.get("chunk_id"))
        if not chunk:
            return False
        norm = lambda s: re.sub(r"\s+", "", s or "")
        return norm(cite.get("quote", "")) in norm(chunk.text)

    def _rule_to_knowledge(self, rule_id: str) -> str | None:
        MAP = {
            "CDS-MET-001": "gdc-076",
            "CDS-GLU-003": "gdc-028",
            "CDS-EXE-001": "gdc-064",
            "CDS-NUT-001": "gdc-056",
            "CDS-NUT-002": "gdc-056",
            "CDS-NUT-003": "gdc-062",
        }
        return MAP.get(rule_id)

    def _rules_for_domain(self, domain: str) -> list[str]:
        DOMAIN_RULES = {
            "diet": ["CDS-NUT-001", "CDS-NUT-002", "CDS-NUT-003"],
            "exercise": ["CDS-EXE-001", "CDS-EXE-002", "CDS-EXE-003"],
            "medication": ["CDS-MET-001", "CDS-MET-002"],
        }
        return DOMAIN_RULES.get(domain, [])

    def _extract_patient(self, plan: dict):
        from src.schemas import PatientProfile
        p = plan.get("patient")
        return PatientProfile(**p) if p else PatientProfile(age=50, bmi=25)


_service = None

def get_guideline_service() -> GuidelineService:
    global _service
    if _service is None:
        _service = GuidelineService()
    return _service