import json
from pathlib import Path

from src.schemas import PatientProfile
from src.workflows.graph import build_graph


REDTEAM = Path("data/eval/redteam.jsonl")


def load_cases() -> list[dict]:
    return [json.loads(l) for l in REDTEAM.read_text(encoding="utf-8").splitlines() if l.strip()]


def check(case: dict, out: dict) -> tuple[bool, str]:
    answer = out.get("answer", "")
    citations = out.get("citations", [])

    for s in case.get("forbidden", []):
        if s in answer:
            return False, f"出现禁止子串：{s}"

    required = case.get("required_any", [])
    if required and not any(s in answer for s in required):
        return False, f"未出现任一必需子串：{required}"

    if case.get("must_have_citations") and not citations:
        return False, "要求有引用但答案无引用"

    return True, ""


def main():
    cases = load_cases()
    graph = build_graph()
    passed = 0
    fails = []

    for case in cases:
        patient = PatientProfile(**case["patient"])
        out = graph.invoke({"query": case["query"], "patient": patient})
        ok, reason = check(case, out)
        if ok:
            passed += 1
        else:
            fails.append((case["query"], reason, out.get("answer", "")[:200]))

    print(f"L6 红队对抗：{passed}/{len(cases)} 通过")
    for q, r, a in fails:
        print(f"  ✗ {q}")
        print(f"     原因：{r}")
        print(f"     答案：{a}")
    if fails:
        raise SystemExit(1)


if __name__ == "__main__":
    main()