import re

from models.intent_models import IntentClassificationResult


class IntentClassifierTool:
    schema_terms = {"schema", "table", "tables", "column", "columns", "structure"}
    follow_up_terms = {"now", "also", "then", "that", "those", "same", "sort", "filter"}
    off_topic_terms = {"weather", "joke", "recipe", "movie", "song", "capital"}
    vague_terms = {"thing", "stuff", "data", "info", "something"}
    sql_action_terms = {
        "show",
        "list",
        "count",
        "total",
        "average",
        "sum",
        "top",
        "highest",
        "lowest",
        "revenue",
        "sales",
        "orders",
        "customers",
    }

    def classify(
        self,
        question: str,
        conversation_history: list[str] | None = None,
    ) -> IntentClassificationResult:
        normalized = question.strip().lower()
        terms = set(re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", normalized))
        history = conversation_history or []

        if not normalized:
            return IntentClassificationResult(
                intent="clarification_needed",
                confidence=1.0,
                reason="The question is empty.",
            )

        if terms & self.off_topic_terms:
            return IntentClassificationResult(
                intent="off_topic",
                confidence=0.9,
                reason="The question is unrelated to database analysis.",
            )

        if terms & self.schema_terms:
            return IntentClassificationResult(
                intent="schema_question",
                confidence=0.9,
                reason="The question asks about database structure.",
            )

        if history and terms & self.follow_up_terms:
            return IntentClassificationResult(
                intent="follow_up",
                confidence=0.75,
                reason="The question appears to depend on previous context.",
            )

        if len(terms) <= 3 and terms & self.vague_terms:
            return IntentClassificationResult(
                intent="clarification_needed",
                confidence=0.7,
                reason="The question is too vague to generate reliable SQL.",
            )

        if terms & self.sql_action_terms:
            return IntentClassificationResult(
                intent="sql_query",
                confidence=0.8,
                reason="The question asks for data from the database.",
            )

        return IntentClassificationResult(
            intent="sql_query",
            confidence=0.55,
            reason="Defaulting to SQL query because the request is data-oriented.",
        )
