import re
from pathlib import Path
from src.schemas import GuidelineChunk

def parse_markdown(path, guide_name, year) -> list[GuidelineChunk]:
    text = Path(path).read_text(encoding="utf-8")
    lines = text.splitlines()
    
    chunks = []
    
    current_section = ""
    current_rec_id = None
    buffer = []
    
    evidence = None
    idx = 0
    
    def flush():
        nonlocal buffer, evidence, idx
        if buffer:
            chunk_text = "\n".join(buffer).strip()
            if chunk_text:
                idx += 1
                chunks.append(GuidelineChunk(
                    chunk_id=f"mock_{idx:03d}",
                    guide_name=guide_name,
                    year=year,
                    section=current_section,
                    rec_id=current_rec_id,
                    evidence_level=evidence,
                    page=None,
                    text=chunk_text,
                ))
        buffer = []
        evidence = None
        
    
    for line in lines:
        line = line.rstrip()
        if line.startswith("# "):
            flush()
            continue
        if line.startswith("## "):
            flush()
            current_section = line[3:].strip()
            current_rec_id = None
        elif line.startswith("### "):
            flush()
            current_section = f"{current_section} / {line[4:].strip()}"
            current_rec_id = None
        elif line.startswith("推荐意见："):
            flush()
            # 从 section 里抓 rec_id，例如 "5.1.2 血糖控制目标"
            m = re.match(r"(\d+(?:\.\d+)+)", current_section.split("/")[-1].strip())
            current_rec_id = m.group(1) if m else None
            buffer.append(line)
        elif line.startswith("证据等级："):
            evidence = line.replace("证据等级：", "").strip()
        elif line.strip() == "":
            flush()
        else:
            buffer.append(line)

    flush()
    return chunks