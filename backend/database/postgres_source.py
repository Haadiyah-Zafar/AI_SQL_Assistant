from __future__ import annotations

from time import perf_counter

from database.source import DatabaseSource
from models.connection_models import PostgresConnectionRequest
from models.query_models import QueryResponse
from models.upload_models import ColumnInfo, DatabaseSchema, ForeignKeyInfo, TableInfo


class PostgresSourceError(Exception):
    pass


class PostgresDatabaseSource(DatabaseSource):
    def __init__(self, source_id: str, config: PostgresConnectionRequest) -> None:
        super().__init__(source_id)
        self.config = config

    def test_connection(self) -> None:
        try:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
        except Exception as exc:
            raise PostgresSourceError(f"Could not connect to PostgreSQL: {exc}") from exc

    def extract_schema(self) -> DatabaseSchema:
        try:
            with self._connect() as connection:
                tables = self._extract_tables(connection)
        except Exception as exc:
            raise PostgresSourceError(f"Could not extract PostgreSQL schema: {exc}") from exc

        if not tables:
            raise PostgresSourceError("This database has no visible tables.")

        return DatabaseSchema(tables=tables, schema_text=self._build_schema_text(tables))

    def execute_read_query(self, sql: str, max_rows: int) -> QueryResponse:
        start = perf_counter()

        try:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(sql)
                    rows = cursor.fetchmany(max_rows + 1)
                    columns = [description[0] for description in cursor.description or []]
        except Exception as exc:
            raise PostgresSourceError(str(exc)) from exc

        truncated = len(rows) > max_rows
        visible_rows = rows[:max_rows]
        response_rows = [
            dict(zip(columns, row, strict=False))
            for row in visible_rows
        ]
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

    def _connect(self):
        try:
            import psycopg2
        except ImportError as exc:
            raise PostgresSourceError(
                "psycopg2 is not installed. Install backend requirements before using PostgreSQL."
            ) from exc

        return psycopg2.connect(
            host=self.config.host,
            port=self.config.port,
            dbname=self.config.database,
            user=self.config.username,
            password=self.config.password,
            sslmode=self.config.sslmode,
            connect_timeout=10,
        )

    def _extract_tables(self, connection) -> list[TableInfo]:
        table_rows = self._fetch_table_rows(connection)
        return [
            self._extract_table(connection, schema_name, table_name)
            for schema_name, table_name in table_rows
        ]

    def _fetch_table_rows(self, connection) -> list[tuple[str, str]]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_type = 'BASE TABLE'
                  AND table_schema NOT IN ('pg_catalog', 'information_schema')
                ORDER BY table_schema, table_name
                """
            )
            return cursor.fetchall()

    def _extract_table(self, connection, schema_name: str, table_name: str) -> TableInfo:
        columns = self._extract_columns(connection, schema_name, table_name)
        primary_keys = self._extract_primary_keys(connection, schema_name, table_name)
        foreign_keys = self._extract_foreign_keys(connection, schema_name, table_name)
        row_count = self._estimate_row_count(connection, schema_name, table_name)
        sample_rows = self._extract_sample_rows(connection, schema_name, table_name)

        columns_with_keys = [
            ColumnInfo(
                name=column.name,
                data_type=column.data_type,
                nullable=column.nullable,
                default=column.default,
                is_primary_key=column.name in primary_keys,
            )
            for column in columns
        ]

        display_name = f"{schema_name}.{table_name}"
        return TableInfo(
            name=display_name,
            columns=columns_with_keys,
            foreign_keys=foreign_keys,
            row_count=row_count,
            sample_rows=sample_rows,
        )

    def _extract_columns(
        self,
        connection,
        schema_name: str,
        table_name: str,
    ) -> list[ColumnInfo]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = %s
                  AND table_name = %s
                ORDER BY ordinal_position
                """,
                (schema_name, table_name),
            )
            return [
                ColumnInfo(
                    name=row[0],
                    data_type=row[1],
                    nullable=row[2] == "YES",
                    default=row[3],
                    is_primary_key=False,
                )
                for row in cursor.fetchall()
            ]

    def _extract_primary_keys(
        self,
        connection,
        schema_name: str,
        table_name: str,
    ) -> set[str]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                 AND tc.table_schema = kcu.table_schema
                WHERE tc.constraint_type = 'PRIMARY KEY'
                  AND tc.table_schema = %s
                  AND tc.table_name = %s
                """,
                (schema_name, table_name),
            )
            return {row[0] for row in cursor.fetchall()}

    def _extract_foreign_keys(
        self,
        connection,
        schema_name: str,
        table_name: str,
    ) -> list[ForeignKeyInfo]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    kcu.column_name,
                    ccu.table_schema,
                    ccu.table_name,
                    ccu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                 AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage ccu
                  ON ccu.constraint_name = tc.constraint_name
                 AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND tc.table_schema = %s
                  AND tc.table_name = %s
                """,
                (schema_name, table_name),
            )
            return [
                ForeignKeyInfo(
                    column=row[0],
                    referenced_table=f"{row[1]}.{row[2]}",
                    referenced_column=row[3],
                )
                for row in cursor.fetchall()
            ]

    def _estimate_row_count(self, connection, schema_name: str, table_name: str) -> int:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COALESCE(s.n_live_tup, 0)
                FROM pg_stat_all_tables s
                WHERE s.schemaname = %s
                  AND s.relname = %s
                """,
                (schema_name, table_name),
            )
            row = cursor.fetchone()
            return int(row[0]) if row else 0

    def _extract_sample_rows(
        self,
        connection,
        schema_name: str,
        table_name: str,
    ) -> list[dict[str, object | None]]:
        try:
            from psycopg2 import sql
        except ImportError as exc:
            raise PostgresSourceError(
                "psycopg2 is not installed. Install backend requirements before using PostgreSQL."
            ) from exc

        with connection.cursor() as cursor:
            query = sql.SQL("SELECT * FROM {}.{} LIMIT 3").format(
                sql.Identifier(schema_name),
                sql.Identifier(table_name),
            )
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description or []]
            return [dict(zip(columns, row, strict=False)) for row in rows]

    def _build_schema_text(self, tables: list[TableInfo]) -> str:
        sections: list[str] = []
        for table in tables:
            column_lines = [
                self._format_column(column)
                for column in table.columns
            ]
            foreign_key_lines = [
                f"  - {foreign_key.column} -> "
                f"{foreign_key.referenced_table}.{foreign_key.referenced_column}"
                for foreign_key in table.foreign_keys
            ]

            section = [
                f"Table: {table.name}",
                f"Estimated rows: {table.row_count}",
                "Columns:",
                *column_lines,
            ]
            if foreign_key_lines:
                section.extend(["Foreign keys:", *foreign_key_lines])
            if table.sample_rows:
                section.append(f"Sample rows: {table.sample_rows}")
            sections.append("\n".join(section))

        return "\n\n".join(sections)

    def _format_column(self, column: ColumnInfo) -> str:
        flags = []
        if column.is_primary_key:
            flags.append("PRIMARY KEY")
        if not column.nullable:
            flags.append("NOT NULL")

        suffix = f" ({', '.join(flags)})" if flags else ""
        return f"  - {column.name} {column.data_type}{suffix}"
