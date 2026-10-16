"""极简食物营养库。所有数值为每 100g 可食部。
carb/protein/fat 单位 g，fiber g，sodium mg。
kcal 由宏量计算：carb*4 + protein*4 + fat*9。
"""

FOOD_DB: dict[str, dict[str, float]] = {
    # 谷薯
    "燕麦":       {"carb": 66.3, "protein": 15.0, "fat": 6.7, "fiber": 10.0, "sodium": 3.7},
    "白米饭":     {"carb": 25.9, "protein": 2.6,  "fat": 0.3, "fiber": 0.3,  "sodium": 1.0},
    "全麦面包":   {"carb": 47.1, "protein": 9.0,  "fat": 3.4, "fiber": 6.0,  "sodium": 460.0},
    "红薯":       {"carb": 24.7, "protein": 1.1,  "fat": 0.2, "fiber": 1.6,  "sodium": 28.0},
    "玉米":       {"carb": 22.8, "protein": 4.0,  "fat": 1.2, "fiber": 2.9,  "sodium": 1.1},

    # 蔬菜
    "西兰花":     {"carb": 4.3,  "protein": 4.1,  "fat": 0.6, "fiber": 1.6,  "sodium": 18.8},
    "菠菜":       {"carb": 2.8,  "protein": 2.6,  "fat": 0.3, "fiber": 1.7,  "sodium": 85.2},
    "番茄":       {"carb": 4.0,  "protein": 0.9,  "fat": 0.2, "fiber": 0.5,  "sodium": 5.0},
    "黄瓜":       {"carb": 2.9,  "protein": 0.8,  "fat": 0.2, "fiber": 0.5,  "sodium": 4.9},
    "青菜":       {"carb": 2.4,  "protein": 1.5,  "fat": 0.3, "fiber": 1.0,  "sodium": 73.0},

    # 蛋白
    "鸡胸肉":     {"carb": 0.0,  "protein": 31.0, "fat": 3.6, "fiber": 0.0,  "sodium": 63.0},
    "鸡蛋":       {"carb": 1.1,  "protein": 12.6, "fat": 10.6,"fiber": 0.0,  "sodium": 131.0},
    "三文鱼":     {"carb": 0.0,  "protein": 20.0, "fat": 13.0,"fiber": 0.0,  "sodium": 60.0},
    "瘦牛肉":     {"carb": 0.0,  "protein": 20.0, "fat": 8.0, "fiber": 0.0,  "sodium": 58.0},
    "豆腐":       {"carb": 4.2,  "protein": 8.1,  "fat": 3.7, "fiber": 0.4,  "sodium": 7.2},
    "草鱼":       {"carb": 0.0,  "protein": 16.6, "fat": 5.2, "fiber": 0.0,  "sodium": 46.0},

    # 乳制品
    "牛奶":       {"carb": 4.8,  "protein": 3.2,  "fat": 3.6, "fiber": 0.0,  "sodium": 43.0},
    "无糖酸奶":   {"carb": 4.0,  "protein": 3.5,  "fat": 3.2, "fiber": 0.0,  "sodium": 50.0},

    # 油脂坚果
    "橄榄油":     {"carb": 0.0,  "protein": 0.0,  "fat": 100.0,"fiber": 0.0, "sodium": 2.0},
    "花生":       {"carb": 16.0, "protein": 24.8, "fat": 44.3,"fiber": 8.5,  "sodium": 18.0},
    "核桃":       {"carb": 13.7, "protein": 15.2, "fat": 65.2,"fiber": 6.7,  "sodium": 2.0},

    # 水果
    "苹果":       {"carb": 13.8, "protein": 0.3,  "fat": 0.2, "fiber": 2.4,  "sodium": 1.0},
    "蓝莓":       {"carb": 14.5, "protein": 0.7,  "fat": 0.3, "fiber": 2.4,  "sodium": 1.0},

    # 调味
    "食盐":       {"carb": 0.0,  "protein": 0.0,  "fat": 0.0, "fiber": 0.0,  "sodium": 39300.0},
}


def item_nutrition(food: str, grams: float) -> dict[str, float]:
    if food not in FOOD_DB:
        raise KeyError(f"食物不在库中：{food}")
    base = FOOD_DB[food]
    f = grams / 100.0
    carb = base["carb"] * f
    protein = base["protein"] * f
    fat = base["fat"] * f
    return {
        "carb_g": round(carb, 2),
        "protein_g": round(protein, 2),
        "fat_g": round(fat, 2),
        "fiber_g": round(base["fiber"] * f, 2),
        "sodium_mg": round(base["sodium"] * f, 2),
        "kcal": round(carb * 4 + protein * 4 + fat * 9, 2),
    }


def sum_nutrition(items: list[dict[str, float]]) -> dict[str, float]:
    keys = ["carb_g", "protein_g", "fat_g", "fiber_g", "sodium_mg", "kcal"]
    total = {k: 0.0 for k in keys}
    for it in items:
        for k in keys:
            total[k] += it.get(k, 0.0)
    return {k: round(v, 2) for k, v in total.items()}