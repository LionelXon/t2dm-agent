from src.workflows.nodes import extract_json


REWRITE_PROMPT = """你是检索助手。把用户问题改写成 3 条更适合检索临床指南的查询，每条不超过 20 字。
保留关键医学概念，换成指南里可能出现的术语。
严格输出 JSON：{"queries": ["...", "...", "..."]}
不要输出 JSON 之外的任何文字。
"""

def rewrite_query(query: str, llm) -> list[str]:
    resp = llm.invoke([
        {"role": "system", "content": REWRITE_PROMPT},
        {"role": "user", "content": query}
    ])
    
    text = resp.content if hasattr(resp, "content") else str(resp)
    
    try:
        data = extract_json(text)
        queries = data.get("queries", [])
        return [q for q in queries if q][:3] or [query]
    except Exception:
        return [query]
    
    