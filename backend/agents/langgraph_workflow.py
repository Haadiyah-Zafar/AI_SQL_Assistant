from agents.agent_workflow import AgentWorkflow
from models.agent_state import AgentState


class LangGraphWorkflowUnavailableError(Exception):
    pass


class LangGraphAgentWorkflow:
    def __init__(self, deterministic_workflow: AgentWorkflow | None = None) -> None:
        self.deterministic_workflow = deterministic_workflow or AgentWorkflow()
        self._compiled_graph = None

    def is_available(self) -> bool:
        try:
            self._import_langgraph()
        except LangGraphWorkflowUnavailableError:
            return False
        return True

    def run(self, state: AgentState) -> AgentState:
        graph = self._graph()
        return graph.invoke(state)

    def _graph(self):
        if self._compiled_graph is not None:
            return self._compiled_graph

        StateGraph, END = self._import_langgraph()
        graph = StateGraph(AgentState)

        graph.add_node("classify_intent", self._classify_intent)
        graph.add_node("run_workflow", self._run_workflow)
        graph.set_entry_point("classify_intent")
        graph.add_edge("classify_intent", "run_workflow")
        graph.add_edge("run_workflow", END)

        self._compiled_graph = graph.compile()
        return self._compiled_graph

    def _classify_intent(self, state: AgentState) -> AgentState:
        return self.deterministic_workflow._classify_intent(state)

    def _run_workflow(self, state: AgentState) -> AgentState:
        return self.deterministic_workflow.run(state)

    def _import_langgraph(self):
        try:
            from langgraph.graph import END, StateGraph
        except ImportError as exc:
            raise LangGraphWorkflowUnavailableError(
                "langgraph is not installed. Install backend requirements to enable LangGraph."
            ) from exc
        return StateGraph, END
