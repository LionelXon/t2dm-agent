import re
from src.ingest.pdf_parser import _split_paragraphs


def test_split_paragraphs_filters_short():
    text = "1\n\n这是一段足够长的指南正文内容，包含推荐意见。\n\n另一个短句。"
    paras = _split_paragraphs(text)
    assert any("这是一段足够长" in p for p in paras)
    assert not any(p == "1" for p in paras)


def test_split_paragraphs_filters_page_number():
    text = "—— 15 ——\n\n推荐意见：二甲双胍是一线首选药物，证据等级 A。"
    paras = _split_paragraphs(text)
    assert len(paras) == 1
    assert "二甲双胍" in paras[0]