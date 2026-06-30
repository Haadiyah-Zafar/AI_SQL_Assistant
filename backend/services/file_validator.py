import sqlite3
from pathlib import Path

from fastapi import UploadFile

from config.settings import get_settings


class FileValidationError(Exception):
    pass


class FileValidator:
    supported_extensions = {".db", ".sqlite", ".csv", ".sql"}

    def __init__(self) -> None:
        self.settings = get_settings()

    def validate_upload_metadata(self, upload: UploadFile) -> None:
        filename = upload.filename or ""
        extension = Path(filename).suffix.lower()

        if extension not in self.supported_extensions:
            raise FileValidationError("Unsupported file format.")

        size = getattr(upload, "size", None)
        if size is not None and size > self.settings.max_upload_size_bytes:
            raise FileValidationError(
                f"File too large. Maximum size is {self.settings.max_upload_size_mb} MB."
            )

    def validate_sqlite_file(self, path: Path) -> None:
        try:
            with sqlite3.connect(path) as connection:
                connection.execute("PRAGMA schema_version").fetchone()
        except sqlite3.DatabaseError as exc:
            raise FileValidationError("The file appears to be corrupted.") from exc
