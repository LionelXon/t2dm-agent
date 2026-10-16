import os
from langchain_openai import ChatOpenAI
from src.config import settings

def get_llm(model: str = "glm-5.3-flash", temperature: float = 0.1) -> ChatOpenAI:
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=settings.zhipuai_api_key,
        base_url=settings.zhipuai_base_url,
        timeout=90,
        max_retries=1,
    )