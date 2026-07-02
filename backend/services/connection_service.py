from database.postgres_source import PostgresDatabaseSource, PostgresSourceError
from models.connection_models import (
    ConnectionSchemaResponse,
    ConnectionTestResponse,
    PostgresConnectionRequest,
)


class ConnectionService:
    def test_postgres_connection(
        self,
        request: PostgresConnectionRequest,
    ) -> ConnectionTestResponse:
        source = PostgresDatabaseSource(source_id=request.database, config=request)
        try:
            source.test_connection()
        except PostgresSourceError as exc:
            return ConnectionTestResponse(success=False, message=str(exc))

        return ConnectionTestResponse(
            success=True,
            message="PostgreSQL connection succeeded.",
        )

    def extract_postgres_schema(
        self,
        request: PostgresConnectionRequest,
    ) -> ConnectionSchemaResponse:
        source = PostgresDatabaseSource(source_id=request.database, config=request)
        schema = source.extract_schema()
        return ConnectionSchemaResponse(success=True, database_schema=schema)
