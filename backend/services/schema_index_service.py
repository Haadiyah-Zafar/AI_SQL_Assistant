from config.settings import get_settings
from models.schema_index_models import (
    SchemaIndexResponse,
    SchemaSearchRequest,
    SchemaSearchResponse,
)
from rag.chroma_store import ChromaSchemaVectorStore
from rag.schema_chunker import SchemaChunker
from rag.vector_store import SchemaVectorStore, VectorStoreError
from models.rag_models import SchemaRetrievalResult
from tools.schema_tool import SchemaTool, SchemaToolError


class SchemaIndexServiceError(Exception):
    pass


class SchemaIndexService:
    def __init__(
        self,
        schema_tool: SchemaTool | None = None,
        chunker: SchemaChunker | None = None,
        vector_store: SchemaVectorStore | None = None,
    ) -> None:
        self.settings = get_settings()
        self.schema_tool = schema_tool or SchemaTool()
        self.chunker = chunker or SchemaChunker()
        self.vector_store = vector_store or ChromaSchemaVectorStore()

    def index_database(self, database_id: str) -> SchemaIndexResponse:
        try:
            schema = self.schema_tool.retrieve_schema(database_id)
            chunks = self.chunker.chunk_schema(schema)
            self.vector_store.delete_database_chunks(database_id)
            indexed_chunks = self.vector_store.upsert_schema_chunks(database_id, chunks)
        except (SchemaToolError, VectorStoreError) as exc:
            raise SchemaIndexServiceError(str(exc)) from exc

        return SchemaIndexResponse(
            database_id=database_id,
            indexed_chunks=indexed_chunks,
        )

    def search_database(
        self,
        database_id: str,
        request: SchemaSearchRequest,
    ) -> SchemaSearchResponse:
        top_k = request.top_k or self.settings.rag_top_k
        try:
            chunks = self.vector_store.query_schema_chunks(
                database_id=database_id,
                question=request.question,
                top_k=top_k,
            )
        except VectorStoreError as exc:
            raise SchemaIndexServiceError(str(exc)) from exc

        return SchemaSearchResponse(
            database_id=database_id,
            retrieval=SchemaRetrievalResult(chunks=chunks),
        )
