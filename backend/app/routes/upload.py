from fastapi import APIRouter, File, HTTPException, UploadFile, status

from models.upload_models import UploadResponse
from services.database_manager import DatabaseManager
from services.file_validator import FileValidationError, FileValidator
from services.schema_extractor import SchemaExtractionError


router = APIRouter(prefix="/upload", tags=["upload"])
file_validator = FileValidator()
database_manager = DatabaseManager()


@router.post("", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_database(file: UploadFile = File(...)) -> UploadResponse:
    try:
        file_validator.validate_upload_metadata(file)
        return await database_manager.store_upload(file)
    except FileValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except SchemaExtractionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
