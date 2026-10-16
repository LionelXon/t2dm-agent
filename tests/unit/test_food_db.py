from src.nutrition.food_db import item_nutrition, sum_nutrition


def test_oat_nutrition_per_100g():
    n = item_nutrition("燕麦", 100)
    assert abs(n["carb_g"] - 66.3) < 0.01
    assert abs(n["protein_g"] - 15.0) < 0.01
    # kcal = 66.3*4 + 15*4 + 6.7*9 = 265.2 + 60 + 60.3 = 385.5
    assert abs(n["kcal"] - 385.5) < 0.1


def test_sum_nutrition():
    a = item_nutrition("白米饭", 150)
    b = item_nutrition("鸡胸肉", 100)
    t = sum_nutrition([a, b])
    assert abs(t["carb_g"] - (25.9 * 1.5 + 0)) < 0.01
    assert abs(t["protein_g"] - (2.6 * 1.5 + 31.0)) < 0.01