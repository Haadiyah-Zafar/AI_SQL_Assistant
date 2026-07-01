from services.file_parser import FileParser
from services.query_service import QueryService
from models.query_models import QueryRequest


def test_query_service_returns_rows_for_select(tmp_path):
    csv_path = tmp_path / "customers.csv"
    csv_path.write_text(
        "id,name\n"
        "1,Alice\n"
        "2,Bob\n",
        encoding="utf-8",
    )

    database_path = FileParser().to_sqlite(csv_path)
    service = QueryService()

    # QueryService discovers uploaded databases by scanning the upload directory.
    # Mirror the upload directory layout used in the app.
    upload_dir = database_path.parent
    service.database_manager.upload_dir = upload_dir

    response = service.execute(
        QueryRequest(
            database_id=database_path.stem,
            sql='SELECT name FROM customers ORDER BY id',
        )
    )

    assert response.row_count == 2
    assert response.columns == ["name"]
    assert response.rows == [{"name": "Alice"}, {"name": "Bob"}]
    assert response.truncated is False


def test_query_service_rejects_write_queries(tmp_path):
    csv_path = tmp_path / "customers.csv"
    csv_path.write_text(
        "id,name\n"
        "1,Alice\n",
        encoding="utf-8",
    )

    database_path = FileParser().to_sqlite(csv_path)
    service = QueryService()
    service.database_manager.upload_dir = database_path.parent

    try:
        service.execute(
            QueryRequest(
                database_id=database_path.stem,
                sql="UPDATE customers SET name = 'Mallory'",
            )
        )
    except Exception as exc:
        assert "read-only" in str(exc).lower()
    else:
        raise AssertionError("Expected write query to be rejected")
