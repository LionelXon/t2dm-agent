from src.ingest.extractor import (
    extract_rec_id_cn_numbered,
    extract_evidence_cn_level,
    extract_rec_id_ada_lettered,
    extract_evidence_ada_grade,
)


def test_cn_rec_id():
    assert extract_rec_id_cn_numbered("5.1.2 血糖控制目标") == "5.1.2"
    assert extract_rec_id_cn_numbered("见 6.2.1 节") == "6.2.1"
    assert extract_rec_id_cn_numbered("没有编号") is None


def test_cn_evidence_level():
    assert extract_evidence_cn_level("证据等级：A") == "A"
    assert extract_evidence_cn_level("（B级）") == "B"
    assert extract_evidence_cn_level("无") is None


def test_ada_rec_id():
    assert extract_rec_id_ada_lettered("Recommendation 5.2 ...") == "5.2"
    assert extract_rec_id_ada_lettered("Section 6.1 ...") == "6.1"


def test_ada_evidence():
    assert extract_evidence_ada_grade("Level A") == "A"
    assert extract_evidence_ada_grade("Grade B") == "B"