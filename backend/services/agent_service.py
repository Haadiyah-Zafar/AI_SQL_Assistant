from agents.agent_workflow import AgentWorkflow
from agents.sql_copilot_agent import SQLCopilotAgent
from models.agent_models import AgentQuestionRequest, AgentQuestionResponse
from models.agent_state import AgentState
from tools.schema_retriever_tool import SchemaRetrieverTool
from tools.schema_tool import SchemaTool
from tools.sql_generator_tool import SQLGeneratorTool


class AgentService:
    def __init__(
        self,
        schema_tool: SchemaTool | None = None,
        schema_retriever_tool: SchemaRetrieverTool | None = None,
        sql_generator_tool: SQLGeneratorTool | None = None,
        sql_copilot_agent: SQLCopilotAgent | None = None,
        agent_workflow: AgentWorkflow | None = None,
    ) -> None:
        self.schema_tool = schema_tool or SchemaTool()
        self.schema_retriever_tool = schema_retriever_tool or SchemaRetrieverTool()
        self.sql_generator_tool = sql_generator_tool or SQLGeneratorTool()
        self.sql_copilot_agent = sql_copilot_agent or SQLCopilotAgent(
            schema_tool=self.schema_tool
        )
        self.agent_workflow = agent_workflow or AgentWorkflow(
            schema_tool=self.schema_tool,
            schema_retriever_tool=self.schema_retriever_tool,
            sql_generator_tool=self.sql_generator_tool,
            sql_copilot_agent=self.sql_copilot_agent,
        )

    def answer_question(self, request: AgentQuestionRequest) -> AgentQuestionResponse:
        state = AgentState(
            user_question=request.question,
            database_id=request.database_id,
            conversation_history=request.conversation_history,
        )

        return self._to_response(self.agent_workflow.run(state))

    def _to_response(self, state: AgentState) -> AgentQuestionResponse:
        return AgentQuestionResponse(
            database_id=state.database_id or "",
            question=state.user_question,
            intent=state.intent,
            schema_context=state.schema_context,
            generated_sql=state.generated_sql,
            validation_result=state.validation_result,
            query_result=state.query_result,
            explanation=state.explanation,
            error=state.error,
        )
