from fastapi import APIRouter, HTTPException, status

from models.schema_index_models import (
    SchemaIndexResponse,
    SchemaSearchRequest,
    SchemaSearchResponse,
)
from services.schema_index_service import SchemaIndexService, SchemaIndexServiceError


router = APIRouter(prefix="/rag", tags=["rag"])
schema_index_service = SchemaIndexService()


@router.post("/databases/{database_id}/index", response_model=SchemaIndexResponse)
def index_database_schema(database_id: str) -> SchemaIndexResponse:
    try:
        return schema_index_service.index_database(database_id)
    except SchemaIndexServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post("/databases/{database_id}/search", response_model=SchemaSearchResponse)
def search_database_schema(
    database_id: str,
    request: SchemaSearchRequest,
) -> SchemaSearchResponse:
    try:
        return schema_index_service.search_database(database_id, request)
    except SchemaIndexServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
