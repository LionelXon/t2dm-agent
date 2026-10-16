from src.rules.schema import Violation
from src.rules.schema import Violation
from src.schemas import PatientProfile


def rule_metformin_egfr(patient: PatientProfile, plan: dict | None) -> list[Violation]:
    """R1: eGFR < 30 禁用二甲双胍；30-45 需减量并监测。"""
    violations: list[Violation] = []
    if patient.egfr is None:
        return violations

    # 只检查方案里是否含二甲双胍
    plan_text = str(plan) if plan else ""
    uses_metformin = "二甲双胍" in plan_text or "metformin" in plan_text.lower()

    if patient.egfr < 30 and uses_metformin:
        violations.append(Violation(
            rule_id="CDS-MET-001",
            severity="hard",
            message=f"eGFR={patient.egfr} <30，禁用二甲双胍",
            evidence="中国T2DM防治指南（2020）- 6.2.1 二甲双胍",
        ))
    elif 30 <= patient.egfr < 45 and uses_metformin:
        violations.append(Violation(
            rule_id="CDS-MET-002",
            severity="soft",
            message=f"eGFR={patient.egfr} 在 30-45，二甲双胍需减量并密切监测",
            evidence="中国T2DM防治指南（2020）- 6.2.1 二甲双胍",
        ))
    return violations


def rule_hba1c_target(patient: PatientProfile, plan: dict | None) -> list[Violation]:
    """R2: 老年/差健康状态 HbA1c 目标应放宽至 7.0%-8.0%。"""
    violations: list[Violation] = []
    if patient.hba1c is None:
        return violations

    is_elderly = patient.age >= 65
    is_poor = patient.health_status == "poor" or patient.hypoglycemia_history

    if (is_elderly or is_poor) and patient.hba1c < 7.0:
        # 这里语义上不是“违规”，而是提醒不要过度收紧。
        # MVP 里作为 soft 提醒，L4 真正硬约束由生成端断言处理。
        violations.append(Violation(
            rule_id="CDS-GLU-003",
            severity="soft",
            message=(
                f"患者年龄={patient.age}, health_status={patient.health_status}, "
                f"低血糖史={patient.hypoglycemia_history}，HbA1c 目标应个体化放宽至 7.0%-8.0%，"
                f"当前 {patient.hba1c}% 可能过严"
            ),
            evidence="中国T2DM防治指南（2020）- 5.1.2 血糖控制目标",
        ))
    return violations


def rule_exercise_minutes(patient: PatientProfile, plan: dict | None) -> list[Violation]:
    """R3: 无禁忌者每周中等强度有氧 ≥150 分钟。"""
    violations: list[Violation] = []
    if not plan:
        return violations

    weekly = plan.get("weekly_moderate_minutes")
    if weekly is None:
        return violations

    # 有运动禁忌的，先不判总量
    contraindications = {"增殖期视网膜病变", "proliferative_retinopathy"}
    if any(c in contraindications for c in patient.complications):
        return violations

    if weekly < 150:
        violations.append(Violation(
            rule_id="CDS-EXE-001",
            severity="hard",
            message=f"每周中等强度有氧 {weekly} 分钟 < 150 分钟",
            evidence="中国T2DM防治指南（2020）- 7.3 运动治疗",
        ))
    return violations


def rule_macros(patient: PatientProfile, plan: dict | None) -> list[Violation]:
    """R4: 宏量营养素区间与盐摄入。"""
    violations: list[Violation] = []
    if not plan:
        return violations

    carb = plan.get("carb_ratio")
    fat = plan.get("fat_ratio")
    salt = plan.get("salt_g_per_day")

    if carb is not None and not (0.45 <= carb <= 0.60):
        violations.append(Violation(
            rule_id="CDS-NUT-001",
            severity="hard",
            message=f"碳水供能比 {carb:.0%} 不在 45%-60%",
            evidence="中国T2DM防治指南（2020）- 8.1 医学营养治疗",
        ))
    if fat is not None and not (0.20 <= fat <= 0.30):
        violations.append(Violation(
            rule_id="CDS-NUT-002",
            severity="hard",
            message=f"脂肪供能比 {fat:.0%} 不在 20%-30%",
            evidence="中国T2DM防治指南（2020）- 8.1 医学营养治疗",
        ))
    if salt is not None and salt >= 5.0:
        violations.append(Violation(
            rule_id="CDS-NUT-003",
            severity="hard",
            message=f"食盐 {salt} g/d ≥ 5 g/d",
            evidence="中国T2DM防治指南（2020）- 8.1 医学营养治疗",
        ))
    return violations
    
    
