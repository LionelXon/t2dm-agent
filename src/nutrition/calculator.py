from src.schemas import PatientProfile


# 活动系数
ACTIVITY_FACTORS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
}


def mifflin_st_jeor_bmr(patient: PatientProfile) -> float:
    """基础代谢率（kcal/d）。"""
    weight = patient.resolved_weight_kg()
    if weight is None or patient.height_cm is None:
        raise ValueError("计算 BMR 需要体重（或 BMI+身高）和身高")
    if patient.sex == "male":
        return 10 * weight + 6.25 * patient.height_cm - 5 * patient.age + 5
    else:
        return 10 * weight + 6.25 * patient.height_cm - 5 * patient.age - 161


def tdee(patient: PatientProfile) -> float:
    """每日总能量消耗。"""
    factor = ACTIVITY_FACTORS.get(patient.activity_level, 1.55)
    return mifflin_st_jeor_bmr(patient) * factor


def energy_target(patient: PatientProfile) -> dict:
    """
    能量目标：超重/肥胖减重导向。
    BMI ≥ 24 时给 TDEE - 500 kcal，最低不低于 1200 kcal。
    """
    base = tdee(patient)
    if patient.bmi >= 24:
        kcal = max(base - 500.0, 1200.0)
    else:
        kcal = base
    return {
        "bmr_kcal": round(base / ACTIVITY_FACTORS.get(patient.activity_level, 1.55), 1),
        "tdee_kcal": round(base, 1),
        "energy_target_kcal": round(kcal, 1),
        "weight_loss_oriented": patient.bmi >= 24,
    }


def macro_targets(patient: PatientProfile) -> dict:
    """宏量营养素区间，全部来自指南条目。"""
    # 碳水 45%-60%，脂肪 20%-30%，纤维 10-14 g/1000 kcal，盐 <5 g/d
    return {
        "carb_ratio_range": (0.45, 0.60),
        "fat_ratio_range": (0.20, 0.30),
        "protein_ratio_range": (0.15, 0.20),  # 一般人群，CKD 另作分支
        "fiber_g_per_1000kcal": (10.0, 14.0),
        "salt_g_per_day_max": 5.0,
    }


def protein_target_g(patient: PatientProfile) -> dict:
    """
    蛋白质：一般 1.0-1.2 g/kg/d；
    CKD 3 期及以上限制到 0.8 g/kg/d。
    """
    weight = patient.resolved_weight_kg()
    if weight is None:
        raise ValueError("计算蛋白质目标需要体重")
    if patient.ckd_stage in ("3a", "3b", "4", "5"):
        low, high = 0.6, 0.8
        note = f"CKD {patient.ckd_stage}：限制蛋白 0.6-0.8 g/kg/d"
    else:
        low, high = 1.0, 1.2
        note = "一般人群：1.0-1.2 g/kg/d"
    return {
        "weight_kg": round(weight, 1),
        "protein_g_range": (round(low * weight, 1), round(high * weight, 1)),
        "note": note,
    }


def diet_targets(patient: PatientProfile) -> dict:
    """汇总：能量 + 宏量 + 蛋白 + 纤维 + 盐。"""
    return {
        "energy": energy_target(patient),
        "macros": macro_targets(patient),
        "protein": protein_target_g(patient),
    }