from src.schemas import PatientProfile


EXERCISE_CONTRAINDICATIONS = {
    "增殖期视网膜病变": "避免剧烈有氧与抗阻运动；改为低强度活动",
    "proliferative_retinopathy": "避免剧烈有氧与抗阻运动；改为低强度活动",
    "周围神经病变": "改为非负重运动，如游泳、骑车",
    "peripheral_neuropathy": "改为非负重运动，如游泳、骑车",
    "自主神经病变": "注意防体位性低血压，运动前后监测血压",
    "autonomic_neuropathy": "注意防体位性低血压，运动前后监测血压",
}


def exercise_targets(patient: PatientProfile) -> dict:
    """运动处方硬约束：每周有氧分钟、频次间隔、抗阻次数、禁忌。"""
    contraindications = [
        {"complication": c, "advice": EXERCISE_CONTRAINDICATIONS[c]}
        for c in patient.complications
        if c in EXERCISE_CONTRAINDICATIONS
    ]

    targets = {
        "weekly_moderate_minutes": 150,
        "max_consecutive_rest_days": 2,
        "resistance_sessions_per_week": (2, 3),
        "contraindications": contraindications,
    }
    if any(
        c in ("增殖期视网膜病变", "proliferative_retinopathy")
        for c in patient.complications
    ):
        targets["intensity_limit"] = "low"
    else:
        targets["intensity_limit"] = "moderate"
    return targets