from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    database_id: str
    sql: str
    max_rows: int | None = Field(default=None, ge=1)


class QueryResponse(BaseModel):
    database_id: str
    sql: str
    columns: list[str]
    rows: list[dict[str, object | None]]
    row_count: int
    truncated: bool
    execution_time_ms: int
