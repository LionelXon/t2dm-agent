from src.nutrition.calculator import (
    mifflin_st_jeor_bmr, tdee, energy_target, protein_target_g, diet_targets,
)
from src.nutrition.exercise_target import exercise_targets
from src.schemas import PatientProfile


def test_bmr_male_known_value():
    # 男性，70kg，175cm，40岁
    # BMR = 10*70 + 6.25*175 - 5*40 + 5 = 700 + 1093.75 - 200 + 5 = 1598.75
    p = PatientProfile(age=40, sex="male", bmi=22.9, weight_kg=70, height_cm=175)
    assert abs(mifflin_st_jeor_bmr(p) - 1598.75) < 0.01


def test_bmr_female_known_value():
    # 女性，60kg，165cm，45岁
    # BMR = 10*60 + 6.25*165 - 5*45 - 161 = 600 + 1031.25 - 225 - 161 = 1245.25
    p = PatientProfile(age=45, sex="female", bmi=22.0, weight_kg=60, height_cm=165)
    assert abs(mifflin_st_jeor_bmr(p) - 1245.25) < 0.01


def test_tdee_moderate_factor():
    p = PatientProfile(
        age=40, sex="male", bmi=22.9, weight_kg=70, height_cm=175,
        activity_level="moderate",
    )
    assert abs(tdee(p) - 1598.75 * 1.55) < 0.01


def test_energy_target_obese_is_deficit():
    p = PatientProfile(age=40, sex="male", bmi=28, weight_kg=85, height_cm=175)
    out = energy_target(p)
    assert out["weight_loss_oriented"] is True
    assert out["energy_target_kcal"] == out["tdee_kcal"] - 500


def test_energy_target_never_below_1200():
    p = PatientProfile(
        age=80, sex="female", bmi=28, weight_kg=50, height_cm=145,
        activity_level="sedentary",
    )
    out = energy_target(p)
    assert out["energy_target_kcal"] >= 1200


def test_protein_general_population():
    p = PatientProfile(age=50, sex="male", bmi=24, weight_kg=70, height_cm=175)
    out = protein_target_g(p)
    lo, hi = out["protein_g_range"]
    assert lo == 70.0 and hi == 84.0
    assert "一般人群" in out["note"]


def test_protein_ckd_restriction():
    p = PatientProfile(
        age=60, sex="male", bmi=24, weight_kg=70, height_cm=175,
        ckd_stage="3b", egfr=35,
    )
    out = protein_target_g(p)
    lo, hi = out["protein_g_range"]
    assert lo == 42.0 and hi == 56.0
    assert "CKD" in out["note"]


def test_diet_targets_assembles_all_parts():
    p = PatientProfile(age=50, sex="male", bmi=24, weight_kg=70, height_cm=175)
    out = diet_targets(p)
    assert "energy" in out and "macros" in out and "protein" in out


def test_exercise_default_target():
    p = PatientProfile(age=50, sex="male", bmi=24)
    out = exercise_targets(p)
    assert out["weekly_moderate_minutes"] == 150
    assert out["resistance_sessions_per_week"] == (2, 3)
    assert out["intensity_limit"] == "moderate"
    assert out["contraindications"] == []


def test_exercise_proliferative_retinopathy_limits_intensity():
    p = PatientProfile(age=50, sex="male", bmi=24, complications=["增殖期视网膜病变"])
    out = exercise_targets(p)
    assert out["intensity_limit"] == "low"
    assert any("视网膜" in c["complication"] for c in out["contraindications"])


def test_exercise_neuropathy_advice():
    p = PatientProfile(age=50, sex="male", bmi=24, complications=["周围神经病变"])
    out = exercise_targets(p)
    assert any("非负重" in c["advice"] for c in out["contraindications"])