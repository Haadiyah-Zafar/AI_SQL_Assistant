from models.rag_models import SchemaRetrievalResult
from models.upload_models import DatabaseSchema
from rag.chroma_store import ChromaSchemaVectorStore
from rag.schema_retriever import SchemaRetriever
from rag.vector_store import VectorStoreError


class SchemaRetrieverTool:
    def __init__(
        self,
        retriever: SchemaRetriever | None = None,
        vector_store: ChromaSchemaVectorStore | None = None,
        database_id: str | None = None,
    ) -> None:
        self.retriever = retriever or SchemaRetriever()
        self.vector_store = vector_store or ChromaSchemaVectorStore()
        self.database_id = database_id

    def retrieve_relevant_schema(
        self,
        question: str,
        schema: DatabaseSchema,
        database_id: str | None = None,
    ) -> SchemaRetrievalResult:
        source_id = database_id or self.database_id
        if source_id:
            try:
                chunks = self.vector_store.query_schema_chunks(
                    database_id=source_id,
                    question=question,
                    top_k=self.retriever.settings.rag_top_k,
                )
                if chunks:
                    return SchemaRetrievalResult(chunks=chunks)
            except VectorStoreError:
                pass

        return self.retriever.retrieve(question=question, schema=schema)
