from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field


class ColumnInfo(BaseModel):
    name: str
    data_type: str
    nullable: bool
    default: str | None = None
    is_primary_key: bool = False


class ForeignKeyInfo(BaseModel):
    column: str
    referenced_table: str
    referenced_column: str


class TableInfo(BaseModel):
    name: str
    columns: list[ColumnInfo]
    foreign_keys: list[ForeignKeyInfo] = Field(default_factory=list)
    row_count: int
    sample_rows: list[dict[str, object | None]] = Field(default_factory=list)


class DatabaseSchema(BaseModel):
    tables: list[TableInfo]
    schema_text: str


class DatabaseInfo(BaseModel):
    database_id: str
    original_filename: str
    stored_path: Path
    uploaded_at: datetime
    table_count: int
    status: str = "ready"


class UploadResponse(BaseModel):
    database: DatabaseInfo
    database_schema: DatabaseSchema
