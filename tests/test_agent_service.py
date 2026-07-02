from models.agent_models import AgentQuestionRequest
from services.agent_service import AgentService
from services.database_manager import DatabaseManager
from services.file_parser import FileParser
from services.query_service import QueryService
from tools.schema_tool import SchemaTool
from tools.sql_executor_tool import SQLExecutorTool
from tools.sql_generator_tool import SQLGeneratorTool
from agents.sql_copilot_agent import SQLCopilotAgent


def _build_agent_service_for_upload_dir(upload_dir):
    database_manager = DatabaseManager()
    database_manager.upload_dir = upload_dir

    query_service = QueryService()
    query_service.database_manager.upload_dir = upload_dir
    query_service.source_factory.database_manager.upload_dir = upload_dir

    schema_tool = SchemaTool(database_manager)
    executor_tool = SQLExecutorTool(query_service)

    return AgentService(
        schema_tool=schema_tool,
        sql_generator_tool=SQLGeneratorTool(),
        sql_copilot_agent=SQLCopilotAgent(
            schema_tool=schema_tool,
            executor_tool=executor_tool,
        ),
    )


def test_agent_service_answers_schema_question_without_llm(tmp_path):
    csv_path = tmp_path / "customers.csv"
    csv_path.write_text(
        "id,name\n"
        "1,Alice\n",
        encoding="utf-8",
    )
    database_path = FileParser().to_sqlite(csv_path)

    service = _build_agent_service_for_upload_dir(tmp_path)

    response = service.answer_question(
        AgentQuestionRequest(
            database_id=database_path.stem,
            question="What tables are in this database?",
        )
    )

    assert response.error is None
    assert response.intent == "schema_question"
    assert response.explanation is not None
    assert "Table: customers" in response.explanation


def test_agent_service_returns_clear_error_when_sql_generation_is_not_configured(tmp_path):
    csv_path = tmp_path / "customers.csv"
    csv_path.write_text(
        "id,name\n"
        "1,Alice\n",
        encoding="utf-8",
    )
    database_path = FileParser().to_sqlite(csv_path)

    service = _build_agent_service_for_upload_dir(tmp_path)

    response = service.answer_question(
        AgentQuestionRequest(
            database_id=database_path.stem,
            question="Show me all customers",
        )
    )

    assert response.intent == "sql_query"
    assert response.error == "SQL generation requires GROQ_API_KEY to be configured."
    assert response.generated_sql is None
