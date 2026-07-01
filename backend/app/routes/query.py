from fastapi import APIRouter, HTTPException, status

from models.query_models import QueryRequest, QueryResponse
from services.query_service import QueryExecutionError, QueryService


router = APIRouter(prefix="/query", tags=["query"])
query_service = QueryService()


@router.post("", response_model=QueryResponse)
def execute_query(request: QueryRequest) -> QueryResponse:
    try:
        return query_service.execute(request)
    except QueryExecutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
