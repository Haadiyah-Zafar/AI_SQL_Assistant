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
