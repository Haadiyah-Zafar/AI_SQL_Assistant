import json

from config.settings import get_settings
from models.sql_generation_models import SQLGenerationRequest, SQLGenerationResult
from services.prompt_loader import PromptLoader


class SQLGeneratorToolError(Exception):
    pass


class SQLGeneratorTool:
    def __init__(self, prompt_loader: PromptLoader | None = None) -> None:
        self.settings = get_settings()
        self.prompt_loader = prompt_loader or PromptLoader()

    def generate(self, request: SQLGenerationRequest) -> SQLGenerationResult:
        if not self.settings.openai_api_key:
            raise SQLGeneratorToolError(
                "SQL generation requires OPENAI_API_KEY to be configured."
            )

        prompt = self.prompt_loader.load("generate_sql.txt")
        messages = self._build_messages(prompt, request)

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise SQLGeneratorToolError(
                "The openai package is not installed. Install backend requirements first."
            ) from exc

        client = OpenAI(api_key=self.settings.openai_api_key)
        response = client.chat.completions.create(
            model=self.settings.openai_model,
            messages=messages,
            temperature=0,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or "{}"
        try:
            payload = json.loads(content)
            return SQLGenerationResult(
                sql=payload["sql"],
                is_read_query=bool(payload.get("is_read_query", True)),
                explanation=payload.get("explanation"),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise SQLGeneratorToolError(
                "SQL generator returned an invalid response."
            ) from exc

    def _build_messages(
        self,
        prompt: str,
        request: SQLGenerationRequest,
    ) -> list[dict[str, str]]:
        user_payload = {
            "question": request.user_question,
            "schema_context": request.schema_context,
            "rag_context": request.rag_context,
            "conversation_history": request.conversation_history,
        }
        return [
            {"role": "system", "content": prompt},
            {"role": "user", "content": json.dumps(user_payload)},
        ]
