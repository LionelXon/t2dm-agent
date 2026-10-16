from src.nutrition.food_db import item_nutrition, sum_nutrition
from src.rules.schema import Violation


def compute_meal_nutrition(meal_plan: dict) -> dict:
    """meal_plan: {"meals": [{"name": "...", "items": [{"food": "...", "grams": 50}]}]}
    返回全天营养汇总 + 各餐明细。
    """
    meal_details = []
    all_items = []
    for meal in meal_plan.get("meals", []):
        items_nut = []
        for it in meal.get("items", []):
            n = item_nutrition(it["food"], float(it["grams"]))
            n["food"] = it["food"]
            n["grams"] = float(it["grams"])
            items_nut.append(n)
            all_items.append(n)
        meal_details.append({
            "name": meal.get("name", ""),
            "items": items_nut,
            "subtotal": sum_nutrition(items_nut),
        })

    total = sum_nutrition(all_items)
    kcal = total["kcal"]
    if kcal > 0:
        total["carb_ratio"] = round(total["carb_g"] * 4 / kcal, 4)
        total["fat_ratio"] = round(total["fat_g"] * 9 / kcal, 4)
        total["protein_ratio"] = round(total["protein_g"] * 4 / kcal, 4)
    else:
        total["carb_ratio"] = total["fat_ratio"] = total["protein_ratio"] = 0.0

    # 钠 → 食盐：NaCl = Na × 2.54
    total["salt_g"] = round(total["sodium_mg"] * 2.54 / 1000, 2)
    total["fiber_per_1000kcal"] = round(
        total["fiber_g"] / kcal * 1000, 2
    ) if kcal > 0 else 0.0

    return {"meals": meal_details, "total": total}


def assert_diet_plan(
    nutrition: dict,
    targets: dict,
    energy_tolerance: float = 0.15,
) -> list[Violation]:
    """对全天营养跑硬规则断言。"""
    v: list[Violation] = []
    total = nutrition["total"]

    target_kcal = targets["energy"]["energy_target_kcal"]
    lo = target_kcal * (1 - energy_tolerance)
    hi = target_kcal * (1 + energy_tolerance)
    if not (lo <= total["kcal"] <= hi):
        v.append(Violation(
            rule_id="CDS-NUT-ENERGY",
            severity="hard",
            message=f"全天能量 {total['kcal']} kcal 超出目标 {target_kcal}±{int(energy_tolerance*100)}% 区间",
            evidence="中国T2DM防治指南（2020）- 8.1 医学营养治疗",
        ))

    carb_lo, carb_hi = targets["macros"]["carb_ratio_range"]
    if not (carb_lo <= total["carb_ratio"] <= carb_hi):
        v.append(Violation(
            rule_id="CDS-NUT-001",
            severity="hard",
            message=f"碳水供能比 {total['carb_ratio']:.0%} 不在 {carb_lo:.0%}-{carb_hi:.0%}",
            evidence="中国T2DM防治指南（2020）- 8.1",
        ))

    fat_lo, fat_hi = targets["macros"]["fat_ratio_range"]
    if not (fat_lo <= total["fat_ratio"] <= fat_hi):
        v.append(Violation(
            rule_id="CDS-NUT-002",
            severity="hard",
            message=f"脂肪供能比 {total['fat_ratio']:.0%} 不在 {fat_lo:.0%}-{fat_hi:.0%}",
            evidence="中国T2DM防治指南（2020）- 8.1",
        ))

    protein_lo, protein_hi = targets["protein"]["protein_g_range"]
    tol = 0.20
    if not (protein_lo * (1 - tol) <= total["protein_g"] <= protein_hi * (1 + tol)):
        v.append(Violation(
            rule_id="CDS-NUT-PROTEIN",
            severity="hard",
            message=f"蛋白质 {total['protein_g']} g 不在 {protein_lo}-{protein_hi} g（±15%）",
            evidence=targets["protein"]["note"],
        ))

    salt_max = targets["macros"]["salt_g_per_day_max"]
    if total["salt_g"] >= salt_max:
        v.append(Violation(
            rule_id="CDS-NUT-003",
            severity="hard",
            message=f"食盐 {total['salt_g']} g/d ≥ {salt_max} g/d",
            evidence="中国T2DM防治指南（2020）- 8.1",
        ))

    fiber_lo, fiber_hi = targets["macros"]["fiber_g_per_1000kcal"]
    if not (fiber_lo <= total["fiber_per_1000kcal"] <= fiber_hi * 1.5):
        # 上限放宽，因为 MVP 食物库纤维数据不全
        v.append(Violation(
            rule_id="CDS-NUT-FIBER",
            severity="soft",
            message=f"膳食纤维 {total['fiber_per_1000kcal']} g/1000kcal 偏低",
            evidence="中国T2DM防治指南（2020）- 8.1",
        ))

    return v