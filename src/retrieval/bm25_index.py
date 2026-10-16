import jieba
from rank_bm25 import BM25Okapi

def tokenize(text: str) -> list[str]:
    return list(jieba.cut(text))

class BM25Index:
    def __init__(self, texts: list[str]):
        self.texts = texts
        self.tokenized = [tokenize(t) for t in texts]
        self.bm25 = BM25Okapi(self.tokenized)
        
    def search(self, query: str, top_k: int = 10) -> list[tuple[int, float]]:
        tokens = tokenize(query)
        scores = self.bm25.get_scores(tokens)
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]
    
    