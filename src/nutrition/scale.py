from src.nutrition.food_db import item_nutrition


STAPLE_FOODS = {"燕麦", "白米饭", "全麦面包", "红薯", "玉米"}


def scale_meal_plan(
    meal_plan: dict,
    target_kcal: float,
    min_scale: float = 0.5,
    max_scale: float = 2.5,
) -> tuple[dict, bool, float]:
    """只缩放主食克重，让总能量贴近目标。蛋白/油脂/蔬菜不动。
    返回 (新 meal_plan, 是否缩放, 缩放因子)。
    """
    items = [it for m in meal_plan.get("meals", []) for it in m.get("items", [])]
    if not items:
        return meal_plan, False, 1.0

    try:
        total_kcal = sum(item_nutrition(it["food"], float(it["grams"]))["kcal"] for it in items)
        staple_kcal = sum(
            item_nutrition(it["food"], float(it["grams"]))["kcal"]
            for it in items if it["food"] in STAPLE_FOODS
        )
    except KeyError:
        return meal_plan, False, 1.0

    if staple_kcal <= 0:
        return meal_plan, False, 1.0

    non_staple_kcal = total_kcal - staple_kcal
    target_staple_kcal = target_kcal - non_staple_kcal
    if target_staple_kcal <= 0:
        return meal_plan, False, 1.0

    scale = target_staple_kcal / staple_kcal
    if not (min_scale <= scale <= max_scale):
        return meal_plan, False, scale

    new_meals = []
    for meal in meal_plan.get("meals", []):
        new_items = []
        for it in meal.get("items", []):
            if it["food"] in STAPLE_FOODS:
                new_g = max(round(float(it["grams"]) * scale / 5) * 5, 5)
                new_items.append({"food": it["food"], "grams": new_g})
            else:
                new_items.append(it)
        new_meals.append({"name": meal.get("name", ""), "items": new_items})
    return {"meals": new_meals}, True, scale