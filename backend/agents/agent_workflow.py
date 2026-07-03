from agents.sql_copilot_agent import SQLCopilotAgent
from models.agent_state import AgentState
from models.sql_generation_models import SQLGenerationRequest
from tools.intent_classifier_tool import IntentClassifierTool
from tools.schema_retriever_tool import SchemaRetrieverTool
from tools.schema_tool import SchemaTool, SchemaToolError
from tools.sql_generator_tool import SQLGeneratorTool, SQLGeneratorToolError


class AgentWorkflow:
    def __init__(
        self,
        intent_classifier: IntentClassifierTool | None = None,
        schema_tool: SchemaTool | None = None,
        schema_retriever_tool: SchemaRetrieverTool | None = None,
        sql_generator_tool: SQLGeneratorTool | None = None,
        sql_copilot_agent: SQLCopilotAgent | None = None,
    ) -> None:
        self.intent_classifier = intent_classifier or IntentClassifierTool()
        self.schema_tool = schema_tool or SchemaTool()
        self.schema_retriever_tool = schema_retriever_tool or SchemaRetrieverTool()
        self.sql_generator_tool = sql_generator_tool or SQLGeneratorTool()
        self.sql_copilot_agent = sql_copilot_agent or SQLCopilotAgent(
            schema_tool=self.schema_tool
        )

    def run(self, state: AgentState) -> AgentState:
        state = self._classify_intent(state)

        if state.intent == "off_topic":
            state.explanation = "I can help with questions about your connected database."
            return state

        if state.intent == "clarification_needed":
            state.error = "Please ask a more specific database question."
            return state

        if not state.database_id:
            state.error = "Please upload or connect a database first."
            return state

        schema = self._retrieve_schema(state)
        if schema is None:
            return state

        if state.intent == "schema_question":
            state.explanation = state.schema_context
            return state

        state = self._retrieve_relevant_schema(state, schema)
        state = self._generate_sql(state)
        if state.error:
            return state

        return self.sql_copilot_agent.run_generated_sql(state)

    def _classify_intent(self, state: AgentState) -> AgentState:
        classification = self.intent_classifier.classify(
            question=state.user_question,
            conversation_history=state.conversation_history,
        )
        state.intent = classification.intent
        return state

    def _retrieve_schema(self, state: AgentState):
        try:
            schema = self.schema_tool.retrieve_schema(state.database_id or "")
        except SchemaToolError as exc:
            state.error = str(exc)
            return None

        state.schema_context = schema.schema_text
        return schema

    def _retrieve_relevant_schema(self, state: AgentState, schema) -> AgentState:
        retrieval = self.schema_retriever_tool.retrieve_relevant_schema(
            question=state.user_question,
            schema=schema,
            database_id=state.database_id,
        )
        state.rag_context = retrieval.context_text
        return state

    def _generate_sql(self, state: AgentState) -> AgentState:
        schema_context = state.rag_context or state.schema_context or ""
        try:
            generation = self.sql_generator_tool.generate(
                SQLGenerationRequest(
                    user_question=state.user_question,
                    schema_context=schema_context,
                    rag_context=state.rag_context,
                    conversation_history=state.conversation_history,
                )
            )
        except SQLGeneratorToolError as exc:
            state.error = str(exc)
            return state

        state.generated_sql = generation.sql
        state.explanation = generation.explanation
        return state
