import sqlite3
from pathlib import Path

from config.settings import get_settings
from models.upload_models import ColumnInfo, DatabaseSchema, ForeignKeyInfo, TableInfo


class SchemaExtractionError(Exception):
    pass


class SchemaExtractor:
    def __init__(self) -> None:
        self.settings = get_settings()

    def extract(self, database_path: Path) -> DatabaseSchema:
        try:
            with sqlite3.connect(database_path) as connection:
                connection.row_factory = sqlite3.Row
                tables = self._extract_tables(connection)
        except sqlite3.DatabaseError as exc:
            raise SchemaExtractionError("The file appears to be corrupted.") from exc

        if not tables:
            raise SchemaExtractionError("This database has no tables.")
        if len(tables) > self.settings.max_table_count:
            raise SchemaExtractionError("Database has too many tables for processing.")

        return DatabaseSchema(tables=tables, schema_text=self._build_schema_text(tables))

    def _extract_tables(self, connection: sqlite3.Connection) -> list[TableInfo]:
        rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()

        return [self._extract_table(connection, row["name"]) for row in rows]

    def _extract_table(self, connection: sqlite3.Connection, table_name: str) -> TableInfo:
        columns = [
            ColumnInfo(
                name=row["name"],
                data_type=row["type"] or "UNKNOWN",
                nullable=not bool(row["notnull"]),
                default=row["dflt_value"],
                is_primary_key=bool(row["pk"]),
            )
            for row in connection.execute(f'PRAGMA table_info("{table_name}")').fetchall()
        ]

        foreign_keys = [
            ForeignKeyInfo(
                column=row["from"],
                referenced_table=row["table"],
                referenced_column=row["to"],
            )
            for row in connection.execute(f'PRAGMA foreign_key_list("{table_name}")').fetchall()
        ]

        row_count = connection.execute(
            f'SELECT COUNT(*) AS row_count FROM "{table_name}"'
        ).fetchone()["row_count"]

        sample_rows = [
            dict(row)
            for row in connection.execute(
                f'SELECT * FROM "{table_name}" LIMIT ?',
                (self.settings.sample_row_limit,),
            ).fetchall()
        ]

        return TableInfo(
            name=table_name,
            columns=columns,
            foreign_keys=foreign_keys,
            row_count=row_count,
            sample_rows=sample_rows,
        )

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
                f"Rows: {table.row_count}",
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
