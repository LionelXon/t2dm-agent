import json
from pathlib import Path

import numpy as np
from src.retrieval.embedder import Embedder
from src.schemas import GuidelineChunk

CHUNKS_IN = Path("data/processed/chunks.jsonl")
INDEX_DIR = Path("data/index")

def main():
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    chunks = [
        GuidelineChunk.model_validate_json(line)
        for line in CHUNKS_IN.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    print(f"加载 {len(chunks)} 条 chunk")
    
    embedder = Embedder()
    embeddings = embedder.encode([c.text for c in chunks])
    np.save(INDEX_DIR / "embeddings.npy", embeddings)
    
    with (INDEX_DIR / "chunks.jsonl").open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(c.model_dump_json() + "\n")
            
    print(f"向量维度 {embeddings.shape} -> {INDEX_DIR}")
    
if __name__ == "__main__":
    main()
