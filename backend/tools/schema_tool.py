from database.source_factory import DatabaseSourceFactory, DatabaseSourceFactoryError
from database.sqlite_source import SQLiteSourceError
from models.upload_models import DatabaseSchema
from services.database_manager import DatabaseManager


class SchemaToolError(Exception):
    pass


class SchemaTool:
    def __init__(self, database_manager: DatabaseManager | None = None) -> None:
        self.database_manager = database_manager or DatabaseManager()
        self.source_factory = DatabaseSourceFactory(self.database_manager)

    def retrieve_schema(self, database_id: str) -> DatabaseSchema:
        try:
            source = self.source_factory.for_uploaded_database(database_id)
            return source.extract_schema()
        except (DatabaseSourceFactoryError, SQLiteSourceError) as exc:
            raise SchemaToolError(str(exc)) from exc

    def retrieve_schema_text(self, database_id: str) -> str:
        return self.retrieve_schema(database_id).schema_text
