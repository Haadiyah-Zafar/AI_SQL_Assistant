from abc import ABC, abstractmethod

from models.rag_models import RetrievedSchemaChunk, SchemaChunk


class VectorStoreError(Exception):
    pass


class SchemaVectorStore(ABC):
    @abstractmethod
    def upsert_schema_chunks(self, database_id: str, chunks: list[SchemaChunk]) -> int:
        raise NotImplementedError

    @abstractmethod
    def query_schema_chunks(
        self,
        database_id: str,
        question: str,
        top_k: int,
    ) -> list[RetrievedSchemaChunk]:
        raise NotImplementedError

    @abstractmethod
    def delete_database_chunks(self, database_id: str) -> None:
        raise NotImplementedError
