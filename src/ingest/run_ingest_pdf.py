import json
from pathlib import Path

import yaml

from src.ingest.pdf_parser import parse_pdf


CONFIG = Path("configs/guides.yaml")
OUT = Path("data/processed/chunks.jsonl")


def load_config() -> list[dict]:
    data = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    return data["guides"]


def main():
    guides = load_config()
    all_chunks = []

    for g in guides:
        pdf_path = Path(g["pdf"])
        if not pdf_path.exists():
            print(f"[跳过] 找不到 {pdf_path}")
            continue
        chunks = parse_pdf(
            path=str(pdf_path),
            guide_id=g["id"],
            guide_name=g["guide_name"],
            year=g["year"],
            rec_id_pattern=g["rec_id_pattern"],
            evidence_pattern=g["evidence_pattern"],
        )
        print(f"[{g['id']}] 解析 {len(chunks)} 条 chunk")
        all_chunks.extend(chunks)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for c in all_chunks:
            f.write(c.model_dump_json() + "\n")
    print(f"写入 {len(all_chunks)} 条 -> {OUT}")


if __name__ == "__main__":
    main()