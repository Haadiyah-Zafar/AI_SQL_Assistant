from agents.sql_copilot_agent import SQLCopilotAgent
from models.agent_models import AgentQuestionRequest, AgentQuestionResponse
from models.agent_state import AgentState
from models.sql_generation_models import SQLGenerationRequest
from tools.schema_tool import SchemaTool, SchemaToolError
from tools.sql_generator_tool import SQLGeneratorTool, SQLGeneratorToolError


class AgentService:
    def __init__(
        self,
        schema_tool: SchemaTool | None = None,
        sql_generator_tool: SQLGeneratorTool | None = None,
        sql_copilot_agent: SQLCopilotAgent | None = None,
    ) -> None:
        self.schema_tool = schema_tool or SchemaTool()
        self.sql_generator_tool = sql_generator_tool or SQLGeneratorTool()
        self.sql_copilot_agent = sql_copilot_agent or SQLCopilotAgent(
            schema_tool=self.schema_tool
        )

    def answer_question(self, request: AgentQuestionRequest) -> AgentQuestionResponse:
        state = AgentState(
            user_question=request.question,
            database_id=request.database_id,
            conversation_history=request.conversation_history,
        )

        try:
            schema = self.schema_tool.retrieve_schema(request.database_id)
        except SchemaToolError as exc:
            state.error = str(exc)
            return self._to_response(state)

        state.schema_context = schema.schema_text

        if self._is_schema_question(request.question):
            state.intent = "schema_question"
            state.explanation = schema.schema_text
            return self._to_response(state)

        state.intent = "sql_query"
        try:
            generation = self.sql_generator_tool.generate(
                SQLGenerationRequest(
                    user_question=request.question,
                    schema_context=schema.schema_text,
                    conversation_history=request.conversation_history,
                )
            )
        except SQLGeneratorToolError as exc:
            state.error = str(exc)
            return self._to_response(state)

        state.generated_sql = generation.sql
        state.explanation = generation.explanation
        state = self.sql_copilot_agent.run_generated_sql(state)
        return self._to_response(state)

    def _is_schema_question(self, question: str) -> bool:
        normalized = question.lower()
        schema_terms = {"schema", "table", "tables", "column", "columns"}
        return any(term in normalized for term in schema_terms)

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
