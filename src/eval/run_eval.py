import json
from pathlib import Path
from src.workflows.nodes import get_retriever


from src.eval.metrics import (
    context_recall_at_k,
    context_precision_at_k,
    citation_precision,
    citation_recall,
)
from src.retrieval.hybrid_retriever import HybridRetriever
from src.workflows.graph import build_graph
from src.schemas import Citation

from src.eval.faithfulness import compute_faithfulness
from src.workflows.llm import get_llm

GOLD = Path("data/eval/gold_set.jsonl")
INDEX = Path("data/index/chunks.jsonl")
K = 3


def load_gold() -> list[dict]:
    return [json.loads(l) for l in GOLD.read_text(encoding="utf-8").splitlines() if l.strip()]


def load_chunk_map() -> dict:
    m = {}
    for line in INDEX.read_text(encoding="utf-8").splitlines():
        if line.strip():
            c = json.loads(line)
            m[c["chunk_id"]] = c
    return m


def main():
    gold = load_gold()
    chunk_map = load_chunk_map()
    retriever = get_retriever()
    graph = build_graph()
    judge_llm = get_llm(temperature=0.0)

    cr_list, cp_list, cp_r_list, cr_r_list, faith_list = [], [], [], [], []

    for i, item in enumerate(gold, 1):
        q = item["query"]
        gold_ids = item["gold_chunk_ids"]

        print(f"[{i}/{len(gold)}] {q}", flush=True)
        out = graph.invoke({"query": q})
        print(
            f"    -> 检索 {len(out.get('retrieved', []))} 条，"
            f"引用 {len(out.get('citations', []))} 条",
            flush=True,
        )

        # L1 检索审计：直接用 graph 内部检索结果（含查询改写 + search_multi）
        retrieved = out.get("retrieved", [])
        retrieved_ids = [c.chunk_id for c in retrieved]
        cr_list.append(context_recall_at_k(retrieved_ids, gold_ids, K))
        cp_list.append(context_precision_at_k(retrieved_ids, gold_ids, K))

        # L2 引用核验
        citations = [c.model_dump() for c in out.get("citations", [])]
        cp_r_list.append(citation_precision(citations, chunk_map))
        cr_r_list.append(citation_recall(citations, gold_ids))

        # L3 事实一致性
        faith = compute_faithfulness(out.get("answer", ""), citations, chunk_map, judge_llm)
        faith_list.append(faith["score"])

    def avg(xs):
        return sum(xs) / len(xs) if xs else 0.0

    print(f"样本数: {len(gold)}，K={K}")
    print(f"L1 context_recall@{K}:    {avg(cr_list):.3f}  (目标 ≥0.9)")
    print(f"L1 context_precision@{K}: {avg(cp_list):.3f}")
    print(f"L2 citation_precision:    {avg(cp_r_list):.3f}  (目标 ≥0.95)")
    print(f"L2 citation_recall:       {avg(cr_r_list):.3f}")
    print(f"L3 faithfulness:          {avg(faith_list):.3f}  (目标 ≥0.85)")


if __name__ == "__main__":
    main()