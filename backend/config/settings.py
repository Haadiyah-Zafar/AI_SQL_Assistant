from functools import lru_cache
import os
from pathlib import Path


class Settings:
    def __init__(self) -> None:
        self.app_name = os.getenv("APP_NAME", "Agentic SQL Copilot")
        self.app_version = os.getenv("APP_VERSION", "0.1.0")
        self.max_upload_size_mb = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))
        self.max_table_count = int(os.getenv("MAX_TABLE_COUNT", "200"))
        self.sample_row_limit = int(os.getenv("SAMPLE_ROW_LIMIT", "3"))
        self.query_row_limit = int(os.getenv("QUERY_ROW_LIMIT", "1000"))
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.rag_top_k = int(os.getenv("RAG_TOP_K", "5"))
        self.rag_backend = os.getenv("RAG_BACKEND", "chroma")
        self.chroma_persist_dir = Path(os.getenv("CHROMA_PERSIST_DIR", "data/chroma"))
        self.chroma_collection_name = os.getenv(
            "CHROMA_COLLECTION_NAME",
            "schema_chunks",
        )
        self.local_embedding_dimensions = int(os.getenv("LOCAL_EMBEDDING_DIMENSIONS", "384"))
        self.upload_dir = Path(os.getenv("UPLOAD_DIR", "data/uploads"))
        self.cors_origins = self._parse_csv_env(
            "CORS_ORIGINS",
            ["http://localhost:3000", "http://127.0.0.1:3000"],
        )

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    def _parse_csv_env(self, key: str, default: list[str]) -> list[str]:
        value = os.getenv(key)
        if not value:
            return default
        return [item.strip() for item in value.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
