import json
from pathlib import Path

from src.retrieval.hybrid_retriever import HybridRetriever


GOLD = Path("data/eval/gold_set.jsonl")
K = 5


def main():
    gold = [json.loads(l) for l in GOLD.read_text(encoding="utf-8").splitlines() if l.strip()]
    r = HybridRetriever(use_reranker=False)

    for item in gold:
        q = item["query"]
        gold_ids = set(item["gold_chunk_ids"])
        results = r.search(q, top_k=K)
        retrieved_ids = [c.chunk_id for c, _ in results]

        hit_rank = None
        for rank, cid in enumerate(retrieved_ids, 1):
            if cid in gold_ids:
                hit_rank = rank
                break

        status = f"命中@{hit_rank}" if hit_rank else "未命中"
        print(f"[{status}] {q}")
        if hit_rank is None:
            for rank, (c, score) in enumerate(results, 1):
                print(f"    {rank}. [{score:.3f}] {c.chunk_id} | {c.text[:60].replace(chr(10), ' ')}")
        print()


if __name__ == "__main__":
    main()