from pydantic import BaseModel, Field

from models.upload_models import DatabaseSchema


class PostgresConnectionRequest(BaseModel):
    host: str
    port: int = Field(default=5432, ge=1, le=65535)
    database: str
    username: str
    password: str
    sslmode: str = "prefer"


class ConnectionTestResponse(BaseModel):
    success: bool
    message: str
    database_type: str = "postgresql"


class ConnectionSchemaResponse(BaseModel):
    success: bool
    database_type: str = "postgresql"
    database_schema: DatabaseSchema
