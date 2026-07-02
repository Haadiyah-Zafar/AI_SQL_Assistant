from models.upload_models import ColumnInfo, DatabaseSchema, TableInfo
from rag.schema_retriever import SchemaRetriever


def _schema() -> DatabaseSchema:
    return DatabaseSchema(
        tables=[
            TableInfo(
                name="customers",
                columns=[
                    ColumnInfo(name="id", data_type="INTEGER", nullable=False),
                    ColumnInfo(name="name", data_type="TEXT", nullable=True),
                    ColumnInfo(name="email", data_type="TEXT", nullable=True),
                ],
                row_count=2,
            ),
            TableInfo(
                name="orders",
                columns=[
                    ColumnInfo(name="id", data_type="INTEGER", nullable=False),
                    ColumnInfo(name="customer_id", data_type="INTEGER", nullable=True),
                    ColumnInfo(name="total", data_type="REAL", nullable=True),
                ],
                row_count=5,
            ),
        ],
        schema_text="Table: customers\n\nTable: orders",
    )


def test_schema_retriever_returns_relevant_table_for_customer_question():
    result = SchemaRetriever().retrieve("show customer emails", _schema(), top_k=1)

    assert len(result.chunks) == 1
    assert result.chunks[0].chunk.table_name == "customers"
    assert "email" in result.context_text


def test_schema_retriever_returns_relevant_table_for_revenue_question():
    result = SchemaRetriever().retrieve("total order revenue", _schema(), top_k=1)

    assert len(result.chunks) == 1
    assert result.chunks[0].chunk.table_name == "orders"
    assert "total" in result.context_text
