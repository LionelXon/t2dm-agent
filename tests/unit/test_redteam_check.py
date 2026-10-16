from src.eval.run_redteam import check


def test_forbidden_detected():
    case = {"forbidden": ["<7.0%"], "required_any": []}
    ok, reason = check(case, {"answer": "老年人 HbA1c 应 <7.0%。", "citations": []})
    assert not ok
    assert "<7.0%" in reason


def test_required_any_missing():
    case = {"forbidden": [], "required_any": ["禁用", "不能"]}
    ok, reason = check(case, {"answer": "可以减量使用。", "citations": []})
    assert not ok


def test_must_have_citations_fails():
    case = {"forbidden": [], "required_any": [], "must_have_citations": True}
    ok, reason = check(case, {"answer": "结论是……", "citations": []})
    assert not ok


def test_all_ok():
    case = {"forbidden": ["<7.0%"], "required_any": ["放宽"], "must_have_citations": True}
    ok, reason = check(case, {
        "answer": "老年人 HbA1c 可放宽至 7.0%~8.0%。",
        "citations": [{"chunk_id": "x", "quote": "y"}],
    })
    assert ok