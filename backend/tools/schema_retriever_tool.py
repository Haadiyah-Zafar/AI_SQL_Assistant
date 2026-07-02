from models.rag_models import SchemaRetrievalResult
from models.upload_models import DatabaseSchema
from rag.schema_retriever import SchemaRetriever


class SchemaRetrieverTool:
    def __init__(self, retriever: SchemaRetriever | None = None) -> None:
        self.retriever = retriever or SchemaRetriever()

    def retrieve_relevant_schema(
        self,
        question: str,
        schema: DatabaseSchema,
    ) -> SchemaRetrievalResult:
        return self.retriever.retrieve(question=question, schema=schema)
