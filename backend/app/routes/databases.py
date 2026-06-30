from fastapi import APIRouter, HTTPException, status

from models.upload_models import DatabaseInfo
from services.database_manager import DatabaseManager, DatabaseNotFoundError


router = APIRouter(prefix="/databases", tags=["databases"])
database_manager = DatabaseManager()


@router.get("", response_model=list[DatabaseInfo])
def list_databases() -> list[DatabaseInfo]:
    return database_manager.list_databases()


@router.get("/{database_id}", response_model=DatabaseInfo)
def get_database(database_id: str) -> DatabaseInfo:
    try:
        return database_manager.get_database(database_id)
    except DatabaseNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
