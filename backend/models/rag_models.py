from pydantic import BaseModel, Field


class SchemaChunk(BaseModel):
    chunk_id: str
    table_name: str
    text: str
    keywords: set[str] = Field(default_factory=set)


class RetrievedSchemaChunk(BaseModel):
    chunk: SchemaChunk
    score: float


class SchemaRetrievalResult(BaseModel):
    chunks: list[RetrievedSchemaChunk]

    @property
    def context_text(self) -> str:
        return "\n\n".join(result.chunk.text for result in self.chunks)
