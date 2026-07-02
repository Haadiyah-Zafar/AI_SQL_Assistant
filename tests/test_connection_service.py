from models.connection_models import PostgresConnectionRequest
from services.connection_service import ConnectionService


def test_postgres_connection_test_returns_failure_response_when_unavailable():
    request = PostgresConnectionRequest(
        host="localhost",
        database="missing",
        username="missing",
        password="missing",
    )

    response = ConnectionService().test_postgres_connection(request)

    assert response.success is False
    assert response.database_type == "postgresql"
    assert "postgresql" in response.message.lower() or "psycopg2" in response.message.lower()
