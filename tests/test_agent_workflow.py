from agents.agent_workflow import AgentWorkflow
from agents.sql_copilot_agent import SQLCopilotAgent
from models.agent_state import AgentState
from services.database_manager import DatabaseManager
from services.file_parser import FileParser
from services.query_service import QueryService
from tools.intent_classifier_tool import IntentClassifierTool
from tools.schema_tool import SchemaTool
from tools.sql_executor_tool import SQLExecutorTool
from tools.sql_generator_tool import SQLGeneratorTool


def test_intent_classifier_identifies_schema_question():
    result = IntentClassifierTool().classify("What tables are in this database?")

    assert result.intent == "schema_question"
    assert result.confidence > 0


def test_intent_classifier_identifies_off_topic_question():
    result = IntentClassifierTool().classify("What is the weather today?")

    assert result.intent == "off_topic"


def test_agent_workflow_returns_schema_for_schema_question(tmp_path):
    csv_path = tmp_path / "customers.csv"
    csv_path.write_text(
        "id,name\n"
        "1,Alice\n",
        encoding="utf-8",
    )
    database_path = FileParser().to_sqlite(csv_path)

    database_manager = DatabaseManager()
    database_manager.upload_dir = tmp_path

    workflow = AgentWorkflow(schema_tool=SchemaTool(database_manager))
    state = workflow.run(
        AgentState(
            user_question="What columns are in this database?",
            database_id=database_path.stem,
        )
    )

    assert state.intent == "schema_question"
    assert state.error is None
    assert state.explanation is not None
    assert "Table: customers" in state.explanation


def test_agent_workflow_returns_clear_error_when_groq_is_not_configured(tmp_path):
    csv_path = tmp_path / "customers.csv"
    csv_path.write_text(
        "id,name\n"
        "1,Alice\n",
        encoding="utf-8",
    )
    database_path = FileParser().to_sqlite(csv_path)

    database_manager = DatabaseManager()
    database_manager.upload_dir = tmp_path

    query_service = QueryService()
    query_service.database_manager.upload_dir = tmp_path
    query_service.source_factory.database_manager.upload_dir = tmp_path

    schema_tool = SchemaTool(database_manager)
    workflow = AgentWorkflow(
        schema_tool=schema_tool,
        sql_generator_tool=SQLGeneratorTool(),
        sql_copilot_agent=SQLCopilotAgent(
            schema_tool=schema_tool,
            executor_tool=SQLExecutorTool(query_service),
        ),
    )

    state = workflow.run(
        AgentState(
            user_question="Show all customers",
            database_id=database_path.stem,
        )
    )

    assert state.intent == "sql_query"
    assert state.error == "SQL generation requires GROQ_API_KEY to be configured."
