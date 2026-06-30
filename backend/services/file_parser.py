import csv
import sqlite3
from pathlib import Path


class FileParser:
    def to_sqlite(self, path: Path) -> Path:
        extension = path.suffix.lower()

        if extension in {".db", ".sqlite"}:
            return path
        if extension == ".csv":
            return self._csv_to_sqlite(path)
        if extension == ".sql":
            return self._sql_to_sqlite(path)

        raise ValueError(f"Unsupported file extension: {extension}")

    def _csv_to_sqlite(self, path: Path) -> Path:
        database_path = path.with_suffix(".sqlite")
        table_name = self._safe_table_name(path.stem)

        with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            fieldnames = reader.fieldnames or []
            if not fieldnames:
                raise ValueError("CSV file has no header row.")

            columns = [self._safe_column_name(column) for column in fieldnames]

            with sqlite3.connect(database_path) as connection:
                quoted_columns = ", ".join(f'"{column}" TEXT' for column in columns)
                connection.execute(f'CREATE TABLE "{table_name}" ({quoted_columns})')

                placeholders = ", ".join("?" for _ in columns)
                quoted_column_names = ", ".join(
                    self._quote_identifier(column) for column in columns
                )
                insert_sql = (
                    f"INSERT INTO {self._quote_identifier(table_name)} "
                    f"({quoted_column_names}) VALUES ({placeholders})"
                )
                for row in reader:
                    connection.execute(
                        insert_sql,
                        [row.get(original_column) for original_column in fieldnames],
                    )

        return database_path

    def _sql_to_sqlite(self, path: Path) -> Path:
        database_path = path.with_suffix(".sqlite")
        script = path.read_text(encoding="utf-8")

        with sqlite3.connect(database_path) as connection:
            connection.executescript(script)

        return database_path

    def _safe_table_name(self, name: str) -> str:
        return self._safe_identifier(name) or "uploaded_table"

    def _safe_column_name(self, name: str) -> str:
        return self._safe_identifier(name) or "column"

    def _safe_identifier(self, value: str) -> str:
        normalized = "".join(character if character.isalnum() else "_" for character in value)
        normalized = normalized.strip("_").lower()
        if normalized and normalized[0].isdigit():
            normalized = f"col_{normalized}"
        return normalized

    def _quote_identifier(self, value: str) -> str:
        return f'"{value.replace(chr(34), chr(34) + chr(34))}"'
