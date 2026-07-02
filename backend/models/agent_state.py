from typing import Literal

from pydantic import BaseModel, Field

from models.query_models import QueryResponse


AgentIntent = Literal[
    "sql_query",
    "schema_question",
    "follow_up",
    "off_topic",
    "clarification_needed",
]


class ValidationResult(BaseModel):
    valid: bool
    issues: list[str] = Field(default_factory=list)
    is_read_query: bool = False


class AgentState(BaseModel):
    user_question: str
    database_id: str | None = None
    intent: AgentIntent | None = None
    conversation_history: list[str] = Field(default_factory=list)
    schema_context: str | None = None
    rag_context: str | None = None
    generated_sql: str | None = None
    validation_result: ValidationResult | None = None
    query_result: QueryResponse | None = None
    explanation: str | None = None
    error: str | None = None
    retry_count: int = 0
