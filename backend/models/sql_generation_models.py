from pydantic import BaseModel, Field


class SQLGenerationRequest(BaseModel):
    user_question: str
    schema_context: str
    rag_context: str | None = None
    conversation_history: list[str] = Field(default_factory=list)


class SQLGenerationResult(BaseModel):
    sql: str
    is_read_query: bool
    explanation: str | None = None
