import re

from models.agent_state import ValidationResult
from models.upload_models import DatabaseSchema


class SQLValidatorTool:
    write_keywords = {
        "alter",
        "create",
        "delete",
        "drop",
        "insert",
        "replace",
        "truncate",
        "update",
    }

    def validate(self, sql: str, schema: DatabaseSchema | None = None) -> ValidationResult:
        issues: list[str] = []
        normalized = sql.strip()
        lowered = normalized.lower()

        if not normalized:
            return ValidationResult(
                valid=False,
                issues=["SQL query cannot be empty."],
                is_read_query=False,
                requires_approval=False,
            )

        is_read_query = lowered.startswith("select ") or lowered.startswith("with ")
        if not is_read_query:
            issues.append("Only read-only SELECT queries are allowed at this stage.")

        first_keyword = self._first_keyword(lowered)
        if first_keyword in self.write_keywords:
            issues.append(f"Query uses write keyword: {first_keyword.upper()}.")

        if schema is not None:
            issues.extend(self._validate_referenced_tables(lowered, schema))

        return ValidationResult(
            valid=not issues,
            issues=issues,
            is_read_query=is_read_query,
            requires_approval=not is_read_query,
        )

    def _first_keyword(self, lowered_sql: str) -> str | None:
        match = re.match(r"^\s*([a-z]+)", lowered_sql)
        return match.group(1) if match else None

    def _validate_referenced_tables(
        self,
        lowered_sql: str,
        schema: DatabaseSchema,
    ) -> list[str]:
        known_tables = {table.name.lower() for table in schema.tables}
        referenced_tables = set(
            match.group(2).lower()
            for match in re.finditer(r"\b(from|join)\s+([a-zA-Z_][\w.]*)", lowered_sql)
        )

        unknown_tables = sorted(referenced_tables - known_tables)
        return [
            f"Query references unknown table: {table_name}."
            for table_name in unknown_tables
        ]
