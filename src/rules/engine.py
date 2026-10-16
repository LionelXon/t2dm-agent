from src.rules.rules import (
    rule_metformin_egfr,
    rule_hba1c_target,
    rule_exercise_minutes,
    rule_macros,
)
from src.rules.schema import Violation
from src.schemas import PatientProfile

ALL_RULES = [
    rule_metformin_egfr,
    rule_hba1c_target,
    rule_exercise_minutes,
    rule_macros,
]

def evaluate_rules(
    patient: PatientProfile,
    plan: dict | None = None,
) -> list[Violation]:
    violations: list[Violation] = []
    for rule in ALL_RULES:
        violations.extend(rule(patient, plan))
    return violations

def has_hard_violation(violations: list[Violation]) -> bool:
    return any(v.severity == "hard" for v in violations)