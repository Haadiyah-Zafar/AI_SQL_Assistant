from agents.langgraph_workflow import LangGraphAgentWorkflow
from agents.sql_copilot_agent import SQLCopilotAgent
from models.agent_state import AgentState
from services.approval_service import ApprovalService
from services.database_manager import DatabaseManager
from services.file_parser import FileParser
from tools.approval_tool import ApprovalTool
from tools.schema_tool import SchemaTool


def test_agent_creates_approval_for_write_query(tmp_path):
    csv_path = tmp_path / "customers.csv"
    csv_path.write_text(
        "id,name\n"
        "1,Alice\n",
        encoding="utf-8",
    )
    database_path = FileParser().to_sqlite(csv_path)

    database_manager = DatabaseManager()
    database_manager.upload_dir = tmp_path
    approval_service = ApprovalService()

    agent = SQLCopilotAgent(
        schema_tool=SchemaTool(database_manager),
        approval_tool=ApprovalTool(approval_service),
    )
    state = agent.run_generated_sql(
        AgentState(
            user_question="Delete Alice",
            database_id=database_path.stem,
            generated_sql="DELETE FROM customers WHERE id = 1",
        )
    )

    assert state.error is None
    assert state.approval_id is not None
    assert state.approval_status == "pending"
    assert state.query_result is None
    assert approval_service.get_approval(state.approval_id).status == "pending"


def test_langgraph_workflow_adapter_is_safe_to_construct():
    workflow = LangGraphAgentWorkflow()

    assert isinstance(workflow.is_available(), bool)
