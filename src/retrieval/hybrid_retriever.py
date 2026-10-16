import json
from pathlib import Path

import numpy as np

from src.retrieval.embedder import Embedder
from src.retrieval.bm25_index import BM25Index
from src.retrieval.reranker import Reranker   # ← 新增
from src.schemas import GuidelineChunk


def rrf_fuse(rankings: list[list[int]], k: int = 60) -> list[int]:
    scores: dict[int, float] = {}
    for ranking in rankings:
        for rank, idx in enumerate(ranking):
            scores[idx] = scores.get(idx, 0.0) + 1.0 / (k + rank + 1)
    return [i for i, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True)]


class HybridRetriever:
    def __init__(self, index_dir: str = "data/index", use_reranker: bool = False):
        index_dir = Path(index_dir)
        chunks_path = index_dir / "chunks.jsonl"
        emb_path = index_dir / "embeddings.npy"

        text = chunks_path.read_text(encoding="utf-8")
        self.chunks: list[GuidelineChunk] = [
            GuidelineChunk.model_validate_json(line)
            for line in text.splitlines()
            if line.strip()
        ]
        self.embeddings = np.load(emb_path)
        self.bm25 = BM25Index([c.text for c in self.chunks])
        self.embedder = Embedder()
        self.use_reranker = use_reranker
        self.reranker = Reranker() if use_reranker else None

    def search_multi(self, queries: list[str], top_k: int = 5, recall_k: int = 20):
        """对多条改写 query 分别检索，再按 RRF 融合。"""
        import numpy as np

        rankings = []
        all_scores: dict[int, float] = {}
        for q in queries:
            q_emb = self.embedder.encode([q], is_query=True)[0]
            vec_scores = self.embeddings @ q_emb
            vec_ranking = list(np.argsort(-vec_scores))[:recall_k]
            bm25_ranking = [i for i, _ in self.bm25.search(q, top_k=recall_k)]
            fused = rrf_fuse([vec_ranking, bm25_ranking])[:recall_k]
            rankings.append(fused)
            for idx in fused:
                all_scores[idx] = max(all_scores.get(idx, 0.0), float(vec_scores[idx]))

        merged = rrf_fuse(rankings)[:top_k]
        return [(self.chunks[i], all_scores.get(i, 0.0)) for i in merged]
    
    def search(self, query: str, top_k: int = 5, recall_k: int = 20) -> list[tuple[GuidelineChunk, float]]:
        q_emb = self.embedder.encode([query], is_query=True)[0]
        vec_scores = self.embeddings @ q_emb
        vec_ranking = list(np.argsort(-vec_scores))[:recall_k]

        bm25_ranking = [i for i, _ in self.bm25.search(query, top_k=recall_k)]

        fused = rrf_fuse([vec_ranking, bm25_ranking])[:recall_k]

        if self.reranker is not None:
            candidates = [self.chunks[i] for i in fused]
            reranked = self.reranker.rerank(query, candidates, top_k=top_k)
            return reranked
        else:
            return [(self.chunks[i], float(vec_scores[i])) for i in fused[:top_k]]