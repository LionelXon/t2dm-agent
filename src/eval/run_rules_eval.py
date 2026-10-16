"""L4 硬规则断言评测：对每条规则跑正向 + 反例。"""
from src.rules.engine import evaluate_rules, has_hard_violation
from src.schemas import PatientProfile


CASES = [
    # (描述, patient, plan, 期望: "pass" 或 "hard_violation")
    ("eGFR=28 用二甲双胍应硬违规",
     PatientProfile(age=60, bmi=27, egfr=28),
     {"medications": ["二甲双胍"]},
     "hard_violation"),
    ("eGFR=60 用二甲双胍应通过",
     PatientProfile(age=60, bmi=27, egfr=60),
     {"medications": ["二甲双胍"]},
     "pass"),
    ("eGFR=35 用二甲双胍应仅 soft 提醒",
     PatientProfile(age=60, bmi=27, egfr=35),
     {"medications": ["二甲双胍"]},
     "pass"),  # 仅 soft，不算 hard
    ("每周运动 90 分钟应硬违规",
     PatientProfile(age=55, bmi=28),
     {"weekly_moderate_minutes": 90},
     "hard_violation"),
    ("每周运动 150 分钟应通过",
     PatientProfile(age=55, bmi=28),
     {"weekly_moderate_minutes": 150},
     "pass"),
    ("碳水 70% 应硬违规",
     PatientProfile(age=55, bmi=28),
     {"carb_ratio": 0.70, "fat_ratio": 0.25, "salt_g_per_day": 4.0},
     "hard_violation"),
    ("碳水 55% 应通过",
     PatientProfile(age=55, bmi=28),
     {"carb_ratio": 0.55, "fat_ratio": 0.25, "salt_g_per_day": 4.0},
     "pass"),
    ("食盐 5g 应硬违规",
     PatientProfile(age=55, bmi=28),
     {"carb_ratio": 0.55, "fat_ratio": 0.25, "salt_g_per_day": 5.0},
     "hard_violation"),
]


def main():
    passed = 0
    failed = []
    for desc, patient, plan, expect in CASES:
        v = evaluate_rules(patient, plan)
        got_hard = has_hard_violation(v)
        ok = (got_hard and expect == "hard_violation") or \
             (not got_hard and expect == "pass")
        if ok:
            passed += 1
        else:
            failed.append((desc, expect, got_hard, [x.message for x in v]))

    print(f"L4 硬规则断言：{passed}/{len(CASES)} 通过")
    for d, e, g, msgs in failed:
        print(f"  ✗ {d}：期望 {e}，实际 hard={g}")
        for m in msgs:
            print(f"      - {m}")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()