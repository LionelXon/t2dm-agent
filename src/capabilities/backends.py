# src/capabilities/backends.py
from abc import ABC, abstractmethod


class KnowledgeBackend(ABC):
    @abstractmethod
    def search(self, query: str, top_k: int) -> list[dict]: ...

    @abstractmethod
    def get_by_id(self, knowledge_id: str) -> dict | None: ...


class LocalFileBackend(KnowledgeBackend):
    """当前实现：本地 JSON + BGE 检索。"""
    ...


class MedicalKnowledgeBaseBackend(KnowledgeBackend):
    """对接团队底座，接口就绪后实现。"""
    def __init__(self, base_url: str, api_key: str):
        ...