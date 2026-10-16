import json
from pathlib import Path

from src.schemas import GuidelineChunk


KNOWLEDGE_IN = Path("data/processed/extracted.jsonl")   # 你的 289 条
OUT = Path("data/processed/chunks.jsonl")


def load_knowledge(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8").strip()
    # 优先尝试整份 JSON
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
        return data.get("items", data.get("knowledge", []))
    except json.JSONDecodeError:
        pass
    # 退回 JSONL
    items = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            items.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return items


def knowledge_to_chunk(item: dict, idx: int) -> GuidelineChunk:
    """把结构化知识映射成 GuidelineChunk，保持下游零改动。"""
    # 拼检索文本：推荐内容 + 适用条件 + 关联实体
    text_parts = [item["推荐内容"].strip()]

    cond = item.get("适用条件", "").strip()
    if cond:
        text_parts.append(f"适用条件：{cond}")

    entities = item.get("关联实体", [])
    if entities:
        text_parts.append(f"关键词：{'、'.join(entities)}")

    text = "\n".join(text_parts)

    # 从 source_locator 粗略提取 guide_name 和 page
    locator = item.get("来源定位", "")
    guide_name = "中国T2DM防治指南"
    year = 2024
    page = None
    # 尝试从 locator 里抓 Page 数字
    import re
    m = re.search(r"[Pp]age\s*(\d+)", locator)
    if m:
        page = int(m.group(1))

    return GuidelineChunk(
        chunk_id=item["ID"],                       # 直接用 gdc-002 当 chunk_id
        guide_name=guide_name,
        year=year,
        section=item.get("知识类型", ""),           # 用知识类型当 section
        rec_id=item["ID"],                          # ID 同时充当 rec_id
        evidence_level=item.get("证据等级"),
        page=page,
        text=text,
    )


def main():
    items = load_knowledge(KNOWLEDGE_IN)
    print(f"加载 {len(items)} 条结构化知识")

    chunks = [knowledge_to_chunk(it, i) for i, it in enumerate(items, 1)]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(c.model_dump_json() + "\n")
    print(f"写入 {len(chunks)} 条 -> {OUT}")


if __name__ == "__main__":
    main()