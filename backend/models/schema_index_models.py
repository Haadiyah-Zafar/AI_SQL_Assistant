from pydantic import BaseModel

from models.rag_models import SchemaRetrievalResult


class SchemaIndexResponse(BaseModel):
    database_id: str
    indexed_chunks: int
    vector_store: str = "chroma"


class SchemaSearchRequest(BaseModel):
    question: str
    top_k: int | None = None


class SchemaSearchResponse(BaseModel):
    database_id: str
    retrieval: SchemaRetrievalResult
    vector_store: str = "chroma"
