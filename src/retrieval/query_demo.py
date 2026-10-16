from src.retrieval.hybrid_retriever import HybridRetriever

def main():
    r = HybridRetriever()
    for q in [
        "老年患者 HbA1c 目标应该放宽到多少",
        "eGFR 28 能不能用二甲双胍",
        "每周运动多少分钟",
    ]:
        print(f"\n=== {q} ===")
        for chunk, score in r.search(q, top_k=3):
            print(f"[{score:.3f}] rec_id={chunk.rec_id} | {chunk.text[:60]}")
            
if __name__ == "__main__":
    main()