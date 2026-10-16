from src.schemas import PatientProfile
from src.workflows.graph import build_graph


def main():
    graph = build_graph()

    cases = [
        (
            "eGFR 28 的患者能不能用二甲双胍？",
            PatientProfile(age=68, bmi=27, egfr=28),
        ),
        (
            "老年患者 HbA1c 目标应该放宽到多少？",
            PatientProfile(age=72, bmi=25, health_status="poor"),
        ),
        (
            "每周运动至少多少分钟？",
            PatientProfile(age=55, bmi=28),
        ),
    ]

    for q, p in cases:
        print(f"\n===== {q} =====")
        out = graph.invoke({"query": q, "patient": p})
        print("答案：", out.get("answer", "")[:300])
        print("引用条数：", len(out.get("citations", [])))
        print("引用核验：", out.get("verify_ok"))
        print("重试次数：", out.get("retry_count", 0))
        for v in out.get("violations", []):
            print(f"  [{v.severity}] {v.rule_id}: {v.message}")


if __name__ == "__main__":
    main()