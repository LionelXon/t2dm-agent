import json
from pathlib import Path
from src.ingest.markdown_parser import parse_markdown

RAW = Path("data/raw/mock_guideline.md")
OUT = Path("data/processed/chunks.jsonl")

def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    chunks = parse_markdown(
        str(RAW),
        guide_name="中国T2DM防治指南",
        year=2020,
    )
    with OUT.open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(c.model_dump_json() + "\n")
    print(f"写入 {len(chunks)} 条 chunk -> {OUT}")

if __name__ == "__main__":
    main()