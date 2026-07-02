import json

from config.settings import get_settings
from models.insight_models import InsightRequest, InsightResult
from services.prompt_loader import PromptLoader


class ResultInsightToolError(Exception):
    pass


class ResultInsightTool:
    def __init__(self, prompt_loader: PromptLoader | None = None) -> None:
        self.settings = get_settings()
        self.prompt_loader = prompt_loader or PromptLoader()

    def explain(self, request: InsightRequest) -> InsightResult:
        if not self.settings.groq_api_key:
            return self._fallback_explanation(request)

        prompt = self.prompt_loader.load("explain_results.txt")
        messages = self._build_messages(prompt, request)

        try:
            from groq import Groq
        except ImportError as exc:
            raise ResultInsightToolError(
                "The groq package is not installed. Install backend requirements first."
            ) from exc

        client = Groq(api_key=self.settings.groq_api_key)
        response = client.chat.completions.create(
            model=self.settings.groq_model,
            messages=messages,
            temperature=0.2,
        )
        explanation = response.choices[0].message.content or ""
        if not explanation.strip():
            return self._fallback_explanation(request)

        return InsightResult(explanation=explanation.strip(), used_llm=True)

    def _fallback_explanation(self, request: InsightRequest) -> InsightResult:
        result = request.query_result
        row_word = "row" if result.row_count == 1 else "rows"
        truncated_note = " The result was truncated by the row limit." if result.truncated else ""
        columns = ", ".join(result.columns) if result.columns else "no columns"
        return InsightResult(
            explanation=(
                f"The query returned {result.row_count} {row_word} "
                f"with columns: {columns}.{truncated_note}"
            ),
            used_llm=False,
        )

    def _build_messages(
        self,
        prompt: str,
        request: InsightRequest,
    ) -> list[dict[str, str]]:
        payload = {
            "question": request.user_question,
            "sql": request.generated_sql,
            "columns": request.query_result.columns,
            "rows": request.query_result.rows[:20],
            "row_count": request.query_result.row_count,
            "truncated": request.query_result.truncated,
        }
        return [
            {"role": "system", "content": prompt},
            {"role": "user", "content": json.dumps(payload)},
        ]
