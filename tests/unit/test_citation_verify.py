import json

from src.schemas import Citation, GuidelineChunk
from src.workflows.nodes import verify_node


def make_chunk():
    return GuidelineChunk(
        chunk_id="mock_002",
        guide_name="中国T2DM防治指南",
        year=2020,
        section="5.1 综合控制目标 / 5.1.2 血糖控制目标",
        rec_id="5.1.2",
        evidence_level="A",
        text="推荐意见：一般成人 T2DM 患者 HbA1c 目标 <7.0%。",
    )


def test_verify_ok():
    state = {
        "retrieved": [make_chunk()],
        "citations": [Citation(chunk_id="mock_002", quote="一般成人 T2DM 患者 HbA1c 目标 <7.0%")],
    }
    out = verify_node(state)
    assert out["verify_ok"] is True


def test_verify_chunk_id_missing():
    state = {
        "retrieved": [make_chunk()],
        "citations": [Citation(chunk_id="not_exist", quote="随便")],
    }
    out = verify_node(state)
    assert out["verify_ok"] is False


def test_verify_quote_not_substring():
    state = {
        "retrieved": [make_chunk()],
        "citations": [Citation(chunk_id="mock_002", quote="这句原文里没有")],
    }
    out = verify_node(state)
    assert out["verify_ok"] is False