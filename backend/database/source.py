from abc import ABC, abstractmethod

from models.query_models import QueryResponse
from models.upload_models import DatabaseSchema


class DatabaseSource(ABC):
    def __init__(self, source_id: str) -> None:
        self.source_id = source_id

    @abstractmethod
    def test_connection(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def extract_schema(self) -> DatabaseSchema:
        raise NotImplementedError

    @abstractmethod
    def execute_read_query(self, sql: str, max_rows: int) -> QueryResponse:
        raise NotImplementedError
