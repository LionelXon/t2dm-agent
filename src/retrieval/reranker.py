from sentence_transformers import CrossEncoder
from src.config import settings
from src.schemas import GuidelineChunk

class Reranker:
    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or settings.reranker_model
        self.model = CrossEncoder(self.model_name, local_files_only=True)
        
    def rerank(
        self,
        query: str,
        candidates: list[GuidelineChunk],
        top_k: int = 5,
    ) -> list[tuple[GuidelineChunk, float]]:
        if not candidates:
            return []
        pairs = [(query, c.text) for c in candidates]
        scores = self.model.predict(pairs)
        ranked = sorted(zip(candidates, scores), key=lambda x:x[1], reverse=True)
        return [(c, float(s)) for c, s in ranked[:top_k]]