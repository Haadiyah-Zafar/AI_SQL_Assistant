import math
import re
from collections import Counter

from config.settings import get_settings
from models.rag_models import RetrievedSchemaChunk, SchemaRetrievalResult
from models.upload_models import DatabaseSchema
from rag.schema_chunker import SchemaChunker


class SchemaRetriever:
    def __init__(self, chunker: SchemaChunker | None = None) -> None:
        self.settings = get_settings()
        self.chunker = chunker or SchemaChunker()

    def retrieve(
        self,
        question: str,
        schema: DatabaseSchema,
        top_k: int | None = None,
    ) -> SchemaRetrievalResult:
        chunks = self.chunker.chunk_schema(schema)
        if not chunks:
            return SchemaRetrievalResult(chunks=[])

        query_terms = self._tokenize(question)
        if not query_terms:
            return SchemaRetrievalResult(
                chunks=[
                    RetrievedSchemaChunk(chunk=chunk, score=0)
                    for chunk in chunks[: self._limit(top_k)]
                ]
            )

        document_frequency = self._document_frequency(chunks)
        scored_chunks = [
            RetrievedSchemaChunk(
                chunk=chunk,
                score=self._score(query_terms, chunk.keywords, document_frequency, len(chunks)),
            )
            for chunk in chunks
        ]
        ranked = sorted(
            scored_chunks,
            key=lambda result: (result.score, result.chunk.table_name),
            reverse=True,
        )

        positive_matches = [result for result in ranked if result.score > 0]
        selected = positive_matches or ranked
        return SchemaRetrievalResult(chunks=selected[: self._limit(top_k)])

    def _limit(self, top_k: int | None) -> int:
        return top_k or self.settings.rag_top_k

    def _tokenize(self, text: str) -> Counter[str]:
        terms = re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", text.lower())
        return Counter(term for term in terms if len(term) > 1)

    def _document_frequency(self, chunks) -> Counter[str]:
        frequency: Counter[str] = Counter()
        for chunk in chunks:
            frequency.update(chunk.keywords)
        return frequency

    def _score(
        self,
        query_terms: Counter[str],
        chunk_terms: set[str],
        document_frequency: Counter[str],
        document_count: int,
    ) -> float:
        score = 0.0
        for term, term_frequency in query_terms.items():
            if term not in chunk_terms:
                continue
            inverse_document_frequency = math.log(
                (document_count + 1) / (document_frequency[term] + 1)
            ) + 1
            score += term_frequency * inverse_document_frequency
        return score
