from src.ingest.markdown_parser import parse_markdown


def test_parse_mock_guideline():
    chunks = parse_markdown(
        "data/raw/mock_guideline.md",
        guide_name="中国T2DM防治指南",
        year=2020,
    )
    assert len(chunks) >= 8
    # 必须抓到这条关键推荐
    hba1c_chunks = [c for c in chunks if "HbA1c 目标 <7.0%" in c.text]
    assert len(hba1c_chunks) == 1
    c = hba1c_chunks[0]
    assert c.rec_id == "5.1.2"
    assert c.evidence_level == "A"
    assert "综合控制目标" in c.section

    # 二甲双胍 eGFR 禁忌也要抓到
    met_chunks = [c for c in chunks if "eGFR <30" in c.text and "二甲双胍" in c.text]
    assert len(met_chunks) == 1
    assert met_chunks[0].evidence_level == "A"