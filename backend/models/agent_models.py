from pydantic import BaseModel, Field

from models.agent_state import AgentIntent, ValidationResult
from models.query_models import QueryResponse


class AgentQuestionRequest(BaseModel):
    database_id: str
    question: str
    conversation_history: list[str] = Field(default_factory=list)


class AgentQuestionResponse(BaseModel):
    database_id: str
    question: str
    intent: AgentIntent | None = None
    schema_context: str | None = None
    generated_sql: str | None = None
    validation_result: ValidationResult | None = None
    query_result: QueryResponse | None = None
    explanation: str | None = None
    error: str | None = None
