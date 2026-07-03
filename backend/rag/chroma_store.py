from config.settings import get_settings
from models.rag_models import RetrievedSchemaChunk, SchemaChunk
from rag.local_embeddings import HashEmbeddingFunction
from rag.vector_store import SchemaVectorStore, VectorStoreError


class ChromaSchemaVectorStore(SchemaVectorStore):
    def __init__(self) -> None:
        self.settings = get_settings()
        self.embedding_function = HashEmbeddingFunction(
            dimensions=self.settings.local_embedding_dimensions
        )

    def upsert_schema_chunks(self, database_id: str, chunks: list[SchemaChunk]) -> int:
        if not chunks:
            return 0

        collection = self._collection()
        ids = [self._record_id(database_id, chunk.chunk_id) for chunk in chunks]
        documents = [chunk.text for chunk in chunks]
        embeddings = [self.embedding_function.embed(chunk.text) for chunk in chunks]
        metadatas = [
            {
                "database_id": database_id,
                "chunk_id": chunk.chunk_id,
                "table_name": chunk.table_name,
            }
            for chunk in chunks
        ]

        collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        return len(chunks)

    def query_schema_chunks(
        self,
        database_id: str,
        question: str,
        top_k: int,
    ) -> list[RetrievedSchemaChunk]:
        collection = self._collection()
        query_embedding = self.embedding_function.embed(question)
        result = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where={"database_id": database_id},
            include=["documents", "metadatas", "distances"],
        )

        documents = result.get("documents", [[]])[0] or []
        metadatas = result.get("metadatas", [[]])[0] or []
        distances = result.get("distances", [[]])[0] or []

        retrieved: list[RetrievedSchemaChunk] = []
        for document, metadata, distance in zip(documents, metadatas, distances):
            if metadata is None:
                continue

            chunk = SchemaChunk(
                chunk_id=str(metadata.get("chunk_id", "")),
                table_name=str(metadata.get("table_name", "")),
                text=document,
            )
            retrieved.append(
                RetrievedSchemaChunk(
                    chunk=chunk,
                    score=self._distance_to_score(distance),
                )
            )
        return retrieved

    def delete_database_chunks(self, database_id: str) -> None:
        self._collection().delete(where={"database_id": database_id})

    def _collection(self):
        try:
            import chromadb
        except ImportError as exc:
            raise VectorStoreError(
                "chromadb is not installed. Install backend requirements before using Chroma RAG."
            ) from exc

        self.settings.chroma_persist_dir.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(self.settings.chroma_persist_dir))
        return client.get_or_create_collection(
            name=self.settings.chroma_collection_name,
            metadata={"description": "Agentic SQL Copilot schema chunks"},
        )

    def _record_id(self, database_id: str, chunk_id: str) -> str:
        safe_chunk_id = chunk_id.replace(":", "_").replace(".", "_")
        return f"{database_id}:{safe_chunk_id}"

    def _distance_to_score(self, distance: float | None) -> float:
        if distance is None:
            return 0.0
        return 1.0 / (1.0 + float(distance))
