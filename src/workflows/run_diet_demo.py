from src.schemas import PatientProfile
from src.workflows.diet_graph import build_diet_graph


def main():
    graph = build_diet_graph()

    patient = PatientProfile(
        age=55, sex="male", bmi=28,
        weight_kg=85, height_cm=175,
        activity_level="moderate",
    )

    out = graph.invoke({"patient": patient})

    print("=" * 50)
    print("患者：", patient)
    print("=" * 50)
    print("说明：", out.get("answer", "")[:200])
    print("重试次数：", out.get("retry_count", 0))
    print()
    print("餐单：")
    for meal in out["meal_plan"].get("meals", []):
        print(f"  {meal['name']}:")
        for it in meal["items"]:
            print(f"    - {it['food']} {it['grams']}g")
    print()
    total = out["nutrition"].get("total", {})
    print("营养汇总：")
    for k in ("kcal", "carb_g", "protein_g", "fat_g", "carb_ratio", "fat_ratio", "salt_g", "fiber_per_1000kcal"):
        print(f"  {k}: {total.get(k)}")
    print()
    print("违规：")
    for v in out.get("violations", []):
        print(f"  [{v.severity}] {v.rule_id}: {v.message}")


if __name__ == "__main__":
    main()