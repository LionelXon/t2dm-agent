from src.rules.engine import evaluate_rules, has_hard_violation
from src.schemas import PatientProfile


def test_metformin_egfr_28_should_be_hard_violation():
    p = PatientProfile(age=60, bmi=27, egfr=28)
    plan = {"medications": ["二甲双胍"]}
    v = evaluate_rules(p, plan)
    assert any(x.rule_id == "CDS-MET-001" and x.severity == "hard" for x in v)
    assert has_hard_violation(v)


def test_metformin_egfr_60_should_pass():
    p = PatientProfile(age=60, bmi=27, egfr=60)
    plan = {"medications": ["二甲双胍"]}
    v = evaluate_rules(p, plan)
    assert not has_hard_violation(v)


def test_metformin_egfr_35_should_be_soft_warning():
    p = PatientProfile(age=60, bmi=27, egfr=35)
    plan = {"medications": ["二甲双胍"]}
    v = evaluate_rules(p, plan)
    assert any(x.rule_id == "CDS-MET-002" and x.severity == "soft" for x in v)
    assert not has_hard_violation(v)


def test_elderly_hba1c_too_tight_should_warn():
    p = PatientProfile(age=72, bmi=25, hba1c=6.5, health_status="poor")
    v = evaluate_rules(p, plan=None)
    assert any(x.rule_id == "CDS-GLU-003" for x in v)
    assert not has_hard_violation(v)


def test_exercise_below_150_should_be_hard_violation():
    p = PatientProfile(age=55, bmi=28)
    plan = {"weekly_moderate_minutes": 90}
    v = evaluate_rules(p, plan)
    assert any(x.rule_id == "CDS-EXE-001" and x.severity == "hard" for x in v)


def test_exercise_150_should_pass():
    p = PatientProfile(age=55, bmi=28)
    plan = {"weekly_moderate_minutes": 150}
    v = evaluate_rules(p, plan)
    assert not has_hard_violation(v)


def test_macros_carb_out_of_range_should_be_hard_violation():
    p = PatientProfile(age=55, bmi=28)
    plan = {"carb_ratio": 0.70, "fat_ratio": 0.25, "salt_g_per_day": 4.0}
    v = evaluate_rules(p, plan)
    assert any(x.rule_id == "CDS-NUT-001" and x.severity == "hard" for x in v)


def test_macros_all_ok_should_pass():
    p = PatientProfile(age=55, bmi=28)
    plan = {"carb_ratio": 0.55, "fat_ratio": 0.25, "salt_g_per_day": 4.0}
    v = evaluate_rules(p, plan)
    assert not has_hard_violation(v)


def test_salt_5g_should_be_hard_violation():
    p = PatientProfile(age=55, bmi=28)
    plan = {"carb_ratio": 0.55, "fat_ratio": 0.25, "salt_g_per_day": 5.0}
    v = evaluate_rules(p, plan)
    assert any(x.rule_id == "CDS-NUT-003" and x.severity == "hard" for x in v)