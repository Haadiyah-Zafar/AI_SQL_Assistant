from fastapi import APIRouter, HTTPException, status

from models.connection_models import (
    ConnectionSchemaResponse,
    ConnectionTestResponse,
    PostgresConnectionRequest,
)
from services.connection_service import ConnectionService
from database.postgres_source import PostgresSourceError


router = APIRouter(prefix="/connections", tags=["connections"])
connection_service = ConnectionService()


@router.post("/postgres/test", response_model=ConnectionTestResponse)
def test_postgres_connection(
    request: PostgresConnectionRequest,
) -> ConnectionTestResponse:
    return connection_service.test_postgres_connection(request)


@router.post("/postgres/schema", response_model=ConnectionSchemaResponse)
def extract_postgres_schema(
    request: PostgresConnectionRequest,
) -> ConnectionSchemaResponse:
    try:
        return connection_service.extract_postgres_schema(request)
    except PostgresSourceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
