from pydantic import BaseModel

from models.query_models import QueryResponse


class InsightRequest(BaseModel):
    user_question: str
    generated_sql: str
    query_result: QueryResponse


class InsightResult(BaseModel):
    explanation: str
    used_llm: bool = False
