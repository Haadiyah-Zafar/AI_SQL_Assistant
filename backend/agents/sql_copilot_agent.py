from models.agent_state import AgentState
from tools.schema_tool import SchemaTool, SchemaToolError
from tools.sql_executor_tool import SQLExecutorTool, SQLExecutorToolError
from tools.sql_validator_tool import SQLValidatorTool


class SQLCopilotAgent:
    def __init__(
        self,
        schema_tool: SchemaTool | None = None,
        validator_tool: SQLValidatorTool | None = None,
        executor_tool: SQLExecutorTool | None = None,
    ) -> None:
        self.schema_tool = schema_tool or SchemaTool()
        self.validator_tool = validator_tool or SQLValidatorTool()
        self.executor_tool = executor_tool or SQLExecutorTool()

    def run_generated_sql(self, state: AgentState) -> AgentState:
        if not state.database_id:
            state.error = "Please upload or connect a database first."
            return state

        if not state.generated_sql:
            state.error = "SQL generation is not implemented yet."
            return state

        try:
            schema = self.schema_tool.retrieve_schema(state.database_id)
        except SchemaToolError as exc:
            state.error = str(exc)
            return state

        state.schema_context = schema.schema_text
        state.validation_result = self.validator_tool.validate(
            state.generated_sql,
            schema,
        )

        if not state.validation_result.valid:
            state.error = " ".join(state.validation_result.issues)
            return state

        try:
            state.query_result = self.executor_tool.execute_read_query(
                database_id=state.database_id,
                sql=state.generated_sql,
            )
        except SQLExecutorToolError as exc:
            state.error = str(exc)
            return state

        state.error = None
        return state
