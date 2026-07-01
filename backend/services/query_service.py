from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from time import perf_counter

from config.settings import get_settings
from models.query_models import QueryRequest, QueryResponse
from services.database_manager import DatabaseManager, DatabaseNotFoundError


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

    def execute(self, request: QueryRequest) -> QueryResponse:
        database = self._get_database(request.database_id)
        safety = self._check_sql_safety(request.sql)
        if not safety.allowed:
            raise QueryExecutionError(safety.reason or "Query is not allowed.")

        row_limit = request.max_rows or self.settings.query_row_limit
        start = perf_counter()

        try:
            with sqlite3.connect(database.stored_path) as connection:
                connection.row_factory = sqlite3.Row
                cursor = connection.execute(request.sql)
                rows = cursor.fetchmany(row_limit + 1)
                columns = [description[0] for description in cursor.description or []]
        except sqlite3.DatabaseError as exc:
            raise QueryExecutionError(str(exc)) from exc

        truncated = len(rows) > row_limit
        visible_rows = rows[:row_limit]
        response_rows = [dict(row) for row in visible_rows]
        elapsed_ms = int((perf_counter() - start) * 1000)

        return QueryResponse(
            database_id=request.database_id,
            sql=request.sql,
            columns=columns,
            rows=response_rows,
            row_count=len(response_rows),
            truncated=truncated,
            execution_time_ms=elapsed_ms,
        )

    def _get_database(self, database_id: str):
        try:
            return self.database_manager.get_database(database_id)
        except DatabaseNotFoundError as exc:
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
