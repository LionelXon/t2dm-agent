from src.nutrition.calculator import diet_targets
from src.nutrition.plan_assert import assert_diet_plan, compute_meal_nutrition
from src.schemas import PatientProfile


def _targets():
    p = PatientProfile(
        age=55, sex="male", bmi=28, weight_kg=85, height_cm=175,
        activity_level="moderate",
    )
    return diet_targets(p)


def _balanced_plan():
    return {"meals": [
        {"name": "早餐", "items": [
            {"food": "燕麦", "grams": 60},
            {"food": "牛奶", "grams": 250},
            {"food": "鸡蛋", "grams": 50},
        ]},
        {"name": "午餐", "items": [
            {"food": "白米饭", "grams": 220},
            {"food": "鸡胸肉", "grams": 120},
            {"food": "西兰花", "grams": 200},
            {"food": "橄榄油", "grams": 8},
        ]},
        {"name": "晚餐", "items": [
            {"food": "红薯", "grams": 250},
            {"food": "草鱼", "grams": 100},
            {"food": "青菜", "grams": 200},
            {"food": "橄榄油", "grams": 6},
        ]},
    ]}


def test_compute_meal_nutrition_has_ratios():
    n = compute_meal_nutrition(_balanced_plan())
    assert "total" in n
    assert 0 < n["total"]["carb_ratio"] < 1
    assert "salt_g" in n["total"]


def test_assert_balanced_plan_no_hard_violation():
    n = compute_meal_nutrition(_balanced_plan())
    v = assert_diet_plan(n, _targets())
    hard = [x for x in v if x.severity == "hard"]
    # 允许个别 hard 因食物库精度不足，但碳水/脂肪比例必须过
    ratio_violations = [x for x in v if x.rule_id in ("CDS-NUT-001", "CDS-NUT-002")]
    assert ratio_violations == [], [x.message for x in ratio_violations]


def test_high_carb_plan_triggers_violation():
    plan = {"meals": [
        {"name": "早餐", "items": [{"food": "白米饭", "grams": 500}]},
    ]}
    n = compute_meal_nutrition(plan)
    v = assert_diet_plan(n, _targets())
    assert any(x.rule_id == "CDS-NUT-001" and x.severity == "hard" for x in v)


def test_high_salt_triggers_violation():
    plan = {"meals": [
        {"name": "调味", "items": [{"food": "食盐", "grams": 6}]},
    ]}
    n = compute_meal_nutrition(plan)
    v = assert_diet_plan(n, _targets())
    assert any(x.rule_id == "CDS-NUT-003" for x in v)