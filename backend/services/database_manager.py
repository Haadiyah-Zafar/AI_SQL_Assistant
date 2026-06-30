from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from config.settings import get_settings
from models.upload_models import DatabaseInfo, UploadResponse
from services.file_parser import FileParser
from services.schema_extractor import SchemaExtractor


class DatabaseNotFoundError(Exception):
    pass


class DatabaseManager:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.upload_dir = self.settings.upload_dir
        self.parser = FileParser()
        self.schema_extractor = SchemaExtractor()

    async def store_upload(self, upload: UploadFile) -> UploadResponse:
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        database_id = uuid4().hex
        extension = Path(upload.filename or "").suffix.lower()
        raw_path = self.upload_dir / f"{database_id}{extension}"

        contents = await upload.read()
        raw_path.write_bytes(contents)

        database_path = self.parser.to_sqlite(raw_path)
        schema = self.schema_extractor.extract(database_path)

        database = DatabaseInfo(
            database_id=database_id,
            original_filename=upload.filename or "uploaded_database",
            stored_path=database_path,
            uploaded_at=datetime.now(timezone.utc),
            table_count=len(schema.tables),
        )

        return UploadResponse(database=database, database_schema=schema)

    def list_databases(self) -> list[DatabaseInfo]:
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        database_files = sorted(self.upload_dir.glob("*.sqlite"))
        database_files.extend(sorted(self.upload_dir.glob("*.db")))

        databases: list[DatabaseInfo] = []
        for path in database_files:
            try:
                schema = self.schema_extractor.extract(path)
            except Exception:
                continue

            databases.append(
                DatabaseInfo(
                    database_id=path.stem,
                    original_filename=path.name,
                    stored_path=path,
                    uploaded_at=datetime.fromtimestamp(
                        path.stat().st_mtime,
                        tz=timezone.utc,
                    ),
                    table_count=len(schema.tables),
                )
            )

        return databases

    def get_database(self, database_id: str) -> DatabaseInfo:
        for database in self.list_databases():
            if database.database_id == database_id:
                return database

        raise DatabaseNotFoundError(f"Database '{database_id}' was not found.")
