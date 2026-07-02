from models.query_models import QueryRequest, QueryResponse
from services.query_service import QueryExecutionError, QueryService


class SQLExecutorToolError(Exception):
    pass


class SQLExecutorTool:
    def __init__(self, query_service: QueryService | None = None) -> None:
        self.query_service = query_service or QueryService()

    def execute_read_query(
        self,
        database_id: str,
        sql: str,
        max_rows: int | None = None,
    ) -> QueryResponse:
        try:
            return self.query_service.execute(
                QueryRequest(database_id=database_id, sql=sql, max_rows=max_rows)
            )
        except QueryExecutionError as exc:
            raise SQLExecutorToolError(str(exc)) from exc
