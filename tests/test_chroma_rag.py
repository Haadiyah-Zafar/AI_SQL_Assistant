from models.rag_models import RetrievedSchemaChunk, SchemaChunk
from models.schema_index_models import SchemaSearchRequest
from models.upload_models import ColumnInfo, DatabaseSchema, TableInfo
from rag.local_embeddings import HashEmbeddingFunction
from rag.vector_store import SchemaVectorStore
from services.schema_index_service import SchemaIndexService
from tools.schema_retriever_tool import SchemaRetrieverTool


class FakeSchemaTool:
    def __init__(self, schema: DatabaseSchema) -> None:
        self.schema = schema

    def retrieve_schema(self, database_id: str) -> DatabaseSchema:
        return self.schema


class FakeVectorStore(SchemaVectorStore):
    def __init__(self) -> None:
        self.chunks_by_database: dict[str, list[SchemaChunk]] = {}

    def upsert_schema_chunks(self, database_id: str, chunks: list[SchemaChunk]) -> int:
        self.chunks_by_database[database_id] = chunks
        return len(chunks)

    def query_schema_chunks(
        self,
        database_id: str,
        question: str,
        top_k: int,
    ) -> list[RetrievedSchemaChunk]:
        chunks = self.chunks_by_database.get(database_id, [])
        matching = [
            chunk for chunk in chunks
            if any(term in chunk.text.lower() for term in question.lower().split())
        ]
        selected = (matching or chunks)[:top_k]
        return [
            RetrievedSchemaChunk(chunk=chunk, score=1.0)
            for chunk in selected
        ]

    def delete_database_chunks(self, database_id: str) -> None:
        self.chunks_by_database.pop(database_id, None)


def _schema() -> DatabaseSchema:
    return DatabaseSchema(
        tables=[
            TableInfo(
                name="customers",
                columns=[
                    ColumnInfo(name="id", data_type="INTEGER", nullable=False),
                    ColumnInfo(name="email", data_type="TEXT", nullable=True),
                ],
                row_count=2,
            ),
            TableInfo(
                name="orders",
                columns=[
                    ColumnInfo(name="id", data_type="INTEGER", nullable=False),
                    ColumnInfo(name="total", data_type="REAL", nullable=True),
                ],
                row_count=3,
            ),
        ],
        schema_text="Table: customers\n\nTable: orders",
    )


def test_hash_embedding_function_is_deterministic_and_normalized():
    embedding_function = HashEmbeddingFunction(dimensions=16)

    first = embedding_function.embed("customers email")
    second = embedding_function.embed("customers email")

    assert first == second
    assert len(first) == 16
    assert sum(value * value for value in first) > 0


def test_schema_index_service_indexes_and_searches_schema_chunks():
    vector_store = FakeVectorStore()
    service = SchemaIndexService(
        schema_tool=FakeSchemaTool(_schema()),
        vector_store=vector_store,
    )

    indexed = service.index_database("sales")
    searched = service.search_database(
        "sales",
        SchemaSearchRequest(question="email", top_k=1),
    )

    assert indexed.indexed_chunks == 2
    assert searched.retrieval.chunks[0].chunk.table_name == "customers"


def test_schema_retriever_tool_prefers_vector_store_when_results_exist():
    vector_store = FakeVectorStore()
    service = SchemaIndexService(
        schema_tool=FakeSchemaTool(_schema()),
        vector_store=vector_store,
    )
    service.index_database("sales")

    result = SchemaRetrieverTool(vector_store=vector_store).retrieve_relevant_schema(
        question="total",
        schema=_schema(),
        database_id="sales",
    )

    assert result.chunks[0].chunk.table_name == "orders"
