import sqlite3
from pathlib import Path
from time import perf_counter

from database.source import DatabaseSource
from models.query_models import QueryResponse
from models.upload_models import DatabaseSchema
from services.schema_extractor import SchemaExtractor, SchemaExtractionError


class SQLiteSourceError(Exception):
    pass


class SQLiteDatabaseSource(DatabaseSource):
    def __init__(self, source_id: str, database_path: Path) -> None:
        super().__init__(source_id)
        self.database_path = database_path
        self.schema_extractor = SchemaExtractor()

    def test_connection(self) -> None:
        try:
            with sqlite3.connect(self.database_path) as connection:
                connection.execute("PRAGMA schema_version").fetchone()
        except sqlite3.DatabaseError as exc:
            raise SQLiteSourceError("Could not connect to SQLite database.") from exc

    def extract_schema(self) -> DatabaseSchema:
        try:
            return self.schema_extractor.extract(self.database_path)
        except SchemaExtractionError as exc:
            raise SQLiteSourceError(str(exc)) from exc

    def execute_read_query(self, sql: str, max_rows: int) -> QueryResponse:
        start = perf_counter()

        try:
            with sqlite3.connect(self.database_path) as connection:
                connection.row_factory = sqlite3.Row
                cursor = connection.execute(sql)
                rows = cursor.fetchmany(max_rows + 1)
                columns = [description[0] for description in cursor.description or []]
        except sqlite3.DatabaseError as exc:
            raise SQLiteSourceError(str(exc)) from exc

        truncated = len(rows) > max_rows
        visible_rows = rows[:max_rows]
        response_rows = [dict(row) for row in visible_rows]
        elapsed_ms = int((perf_counter() - start) * 1000)

        return QueryResponse(
            database_id=self.source_id,
            sql=sql,
            columns=columns,
            rows=response_rows,
            row_count=len(response_rows),
            truncated=truncated,
            execution_time_ms=elapsed_ms,
        )
