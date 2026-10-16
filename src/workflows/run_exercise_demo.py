from src.schemas import PatientProfile
from src.workflows.exercise_graph import build_exercise_graph


def main():
    graph = build_exercise_graph()

    cases = [
        PatientProfile(age=55, sex="male", bmi=28),
        PatientProfile(
            age=68, sex="female", bmi=26,
            complications=["增殖期视网膜病变"],
        ),
    ]

    for p in cases:
        print("=" * 50)
        print(f"患者 age={p.age} BMI={p.bmi} 并发症={p.complications}")
        out = graph.invoke({"patient": p})
        print("说明：", out.get("answer", "")[:150])
        print("重试次数：", out.get("retry_count", 0))
        print("方案：")
        for s in out["exercise_plan"].get("sessions", []):
            print(f"  {s['day']} | {s['type']} | {s['activity']} | {s['minutes']}min | {s['intensity']}")
        print("违规：")
        for v in out.get("violations", []):
            print(f"  [{v.severity}] {v.rule_id}: {v.message}")


if __name__ == "__main__":
    main()