from services.file_parser import FileParser
from services.schema_extractor import SchemaExtractor


def test_csv_file_is_converted_to_sqlite_and_schema_is_extracted(tmp_path):
    csv_path = tmp_path / "customers.csv"
    csv_path.write_text(
        "id,name,email\n"
        "1,Alice,alice@example.com\n"
        "2,Bob,bob@example.com\n",
        encoding="utf-8",
    )

    database_path = FileParser().to_sqlite(csv_path)
    schema = SchemaExtractor().extract(database_path)

    assert database_path.exists()
    assert len(schema.tables) == 1
    assert schema.tables[0].name == "customers"
    assert schema.tables[0].row_count == 2
    assert [column.name for column in schema.tables[0].columns] == [
        "id",
        "name",
        "email",
    ]
    assert "Table: customers" in schema.schema_text
