from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",   # 忽略 .env 中未声明的字段
    )

    app_name: str = "t2dm-agent"
    data_dir: str = "data"
    chroma_dir: str = "data/chroma"
    embedding_model: str = "BAAI/bge-small-zh-v1.5"
    # embedding_model: str = "BAAI/bge-m3"
    reranker_model: str = "BAAI/bge-reranker-v2-m3"
    top_k: int = 10

    # 如果后面要用智谱，就补上这两个字段（推荐）
    zhipuai_api_key: str = "aee1d90682eb4b31b89ff8cfa67a35e5.PR8mV5uWprp9ddeo"
    zhipuai_base_url: str = "https://open.bigmodel.cn/api/paas/v4/"

settings = Settings()