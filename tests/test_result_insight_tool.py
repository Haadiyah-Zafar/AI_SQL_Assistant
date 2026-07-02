from models.insight_models import InsightRequest
from models.query_models import QueryResponse
from tools.result_insight_tool import ResultInsightTool


def test_result_insight_tool_returns_fallback_without_groq_key():
    result = ResultInsightTool().explain(
        InsightRequest(
            user_question="Show customers",
            generated_sql="SELECT name FROM customers",
            query_result=QueryResponse(
                database_id="customers",
                sql="SELECT name FROM customers",
                columns=["name"],
                rows=[{"name": "Alice"}],
                row_count=1,
                truncated=False,
                execution_time_ms=3,
            ),
        )
    )

    assert result.used_llm is False
    assert "1 row" in result.explanation
    assert "name" in result.explanation
