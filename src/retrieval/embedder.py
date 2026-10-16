from sentence_transformers import SentenceTransformer
import numpy as np
from src.config import settings

class Embedder:
    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or settings.embedding_model
        self.model = SentenceTransformer(self.model_name, local_files_only=True)
        
    def encode(self, texts: list[str], is_query: bool = False) -> np.ndarray:
        if is_query:
            # bge 系列推荐 query 加前缀
            texts = [f"为这个句子生成表示以用于检索相关文章：{t}" for t in texts]
        
        return self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )