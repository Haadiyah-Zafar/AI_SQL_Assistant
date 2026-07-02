from models.upload_models import ColumnInfo, DatabaseSchema, TableInfo
from agents.sql_copilot_agent import SQLCopilotAgent
from models.agent_state import AgentState
from tools.schema_tool import SchemaTool
from tools.sql_executor_tool import SQLExecutorTool
from tools.sql_validator_tool import SQLValidatorTool
from services.database_manager import DatabaseManager
from services.file_parser import FileParser
from services.query_service import QueryService


def test_sql_validator_accepts_read_query_for_known_table():
    schema = DatabaseSchema(
        tables=[
            TableInfo(
                name="customers",
                columns=[ColumnInfo(name="id", data_type="TEXT", nullable=True)],
                row_count=0,
            )
        ],
        schema_text="Table: customers",
    )

    result = SQLValidatorTool().validate("SELECT id FROM customers", schema)

    assert result.valid is True
    assert result.is_read_query is True
    assert result.issues == []


def test_sql_validator_rejects_write_query():
    result = SQLValidatorTool().validate("DELETE FROM customers")

    assert result.valid is False
    assert result.is_read_query is False
    assert "read-only" in " ".join(result.issues).lower()


def test_schema_and_executor_tools_use_uploaded_database_source(tmp_path):
    csv_path = tmp_path / "customers.csv"
    csv_path.write_text(
        "id,name\n"
        "1,Alice\n"
        "2,Bob\n",
        encoding="utf-8",
    )
    database_path = FileParser().to_sqlite(csv_path)

    database_manager = DatabaseManager()
    database_manager.upload_dir = tmp_path

    query_service = QueryService()
    query_service.database_manager.upload_dir = tmp_path
    query_service.source_factory.database_manager.upload_dir = tmp_path

    schema = SchemaTool(database_manager).retrieve_schema(database_path.stem)
    result = SQLExecutorTool(query_service).execute_read_query(
        database_id=database_path.stem,
        sql="SELECT name FROM customers ORDER BY id",
    )

    assert schema.tables[0].name == "customers"
    assert result.rows == [{"name": "Alice"}, {"name": "Bob"}]


def test_sql_copilot_agent_runs_generated_sql_against_uploaded_database(tmp_path):
    csv_path = tmp_path / "customers.csv"
    csv_path.write_text(
        "id,name\n"
        "1,Alice\n"
        "2,Bob\n",
        encoding="utf-8",
    )
    database_path = FileParser().to_sqlite(csv_path)

    database_manager = DatabaseManager()
    database_manager.upload_dir = tmp_path

    query_service = QueryService()
    query_service.database_manager.upload_dir = tmp_path
    query_service.source_factory.database_manager.upload_dir = tmp_path

    agent = SQLCopilotAgent(
        schema_tool=SchemaTool(database_manager),
        executor_tool=SQLExecutorTool(query_service),
    )
    state = AgentState(
        user_question="Show customer names",
        database_id=database_path.stem,
        generated_sql="SELECT name FROM customers ORDER BY id",
    )

    result_state = agent.run_generated_sql(state)

    assert result_state.error is None
    assert result_state.validation_result is not None
    assert result_state.validation_result.valid is True
    assert result_state.query_result is not None
    assert result_state.query_result.rows == [{"name": "Alice"}, {"name": "Bob"}]
