from __future__ import annotations

from dataclasses import dataclass

from config.settings import get_settings
from database.source_factory import DatabaseSourceFactory, DatabaseSourceFactoryError
from database.sqlite_source import SQLiteSourceError
from models.query_models import QueryRequest, QueryResponse
from services.database_manager import DatabaseManager


class QueryExecutionError(Exception):
    pass


@dataclass
class QuerySafetyCheck:
    allowed: bool
    reason: str | None = None


class QueryService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.database_manager = DatabaseManager()
        self.source_factory = DatabaseSourceFactory(self.database_manager)

    def execute(self, request: QueryRequest) -> QueryResponse:
        safety = self._check_sql_safety(request.sql)
        if not safety.allowed:
            raise QueryExecutionError(safety.reason or "Query is not allowed.")

        row_limit = request.max_rows or self.settings.query_row_limit

        try:
            source = self.source_factory.for_uploaded_database(request.database_id)
            return source.execute_read_query(request.sql, row_limit)
        except (DatabaseSourceFactoryError, SQLiteSourceError) as exc:
            raise QueryExecutionError(str(exc)) from exc

    def _check_sql_safety(self, sql: str) -> QuerySafetyCheck:
        normalized = sql.strip().lower()
        if not normalized:
            return QuerySafetyCheck(False, "SQL query cannot be empty.")
        if normalized.startswith("select ") or normalized.startswith("with "):
            return QuerySafetyCheck(True)
        return QuerySafetyCheck(
            False,
            "Only read-only SELECT queries are allowed at this stage.",
        )
