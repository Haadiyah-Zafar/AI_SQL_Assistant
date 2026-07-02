from database.source import DatabaseSource
from database.sqlite_source import SQLiteDatabaseSource
from services.database_manager import DatabaseManager, DatabaseNotFoundError


class DatabaseSourceFactoryError(Exception):
    pass


class DatabaseSourceFactory:
    def __init__(self, database_manager: DatabaseManager | None = None) -> None:
        self.database_manager = database_manager or DatabaseManager()

    def for_uploaded_database(self, database_id: str) -> DatabaseSource:
        try:
            database = self.database_manager.get_database(database_id)
        except DatabaseNotFoundError as exc:
            raise DatabaseSourceFactoryError(str(exc)) from exc

        return SQLiteDatabaseSource(
            source_id=database.database_id,
            database_path=database.stored_path,
        )
