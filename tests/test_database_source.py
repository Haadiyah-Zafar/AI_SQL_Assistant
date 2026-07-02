from database.source_factory import DatabaseSourceFactory
from database.sqlite_source import SQLiteDatabaseSource
from services.database_manager import DatabaseManager
from services.file_parser import FileParser


def test_source_factory_returns_sqlite_source_for_uploaded_database(tmp_path):
    csv_path = tmp_path / "customers.csv"
    csv_path.write_text(
        "id,name\n"
        "1,Alice\n",
        encoding="utf-8",
    )
    database_path = FileParser().to_sqlite(csv_path)

    database_manager = DatabaseManager()
    database_manager.upload_dir = tmp_path
    factory = DatabaseSourceFactory(database_manager)

    source = factory.for_uploaded_database(database_path.stem)

    assert isinstance(source, SQLiteDatabaseSource)
    assert source.source_id == database_path.stem


def test_sqlite_source_extracts_schema_through_common_interface(tmp_path):
    csv_path = tmp_path / "customers.csv"
    csv_path.write_text(
        "id,name\n"
        "1,Alice\n",
        encoding="utf-8",
    )
    database_path = FileParser().to_sqlite(csv_path)

    source = SQLiteDatabaseSource(
        source_id=database_path.stem,
        database_path=database_path,
    )

    schema = source.extract_schema()

    assert schema.tables[0].name == "customers"
    assert [column.name for column in schema.tables[0].columns] == ["id", "name"]
