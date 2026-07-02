import re

from models.rag_models import SchemaChunk
from models.upload_models import DatabaseSchema, TableInfo


class SchemaChunker:
    def chunk_schema(self, schema: DatabaseSchema) -> list[SchemaChunk]:
        return [self._chunk_table(table) for table in schema.tables]

    def _chunk_table(self, table: TableInfo) -> SchemaChunk:
        text = self._table_to_text(table)
        return SchemaChunk(
            chunk_id=f"table:{table.name}",
            table_name=table.name,
            text=text,
            keywords=self._extract_keywords(text),
        )

    def _table_to_text(self, table: TableInfo) -> str:
        column_text = ", ".join(
            f"{column.name} {column.data_type}"
            for column in table.columns
        )
        foreign_key_text = ", ".join(
            f"{foreign_key.column} references "
            f"{foreign_key.referenced_table}.{foreign_key.referenced_column}"
            for foreign_key in table.foreign_keys
        )

        parts = [
            f"Table: {table.name}",
            f"Rows: {table.row_count}",
            f"Columns: {column_text}",
        ]
        if foreign_key_text:
            parts.append(f"Foreign keys: {foreign_key_text}")
        if table.sample_rows:
            parts.append(f"Sample rows: {table.sample_rows}")

        return "\n".join(parts)

    def _extract_keywords(self, text: str) -> set[str]:
        return {
            token
            for token in re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", text.lower())
            if len(token) > 1
        }
