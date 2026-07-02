from pathlib import Path


class PromptLoaderError(Exception):
    pass


class PromptLoader:
    def __init__(self, prompt_dir: Path | None = None) -> None:
        self.prompt_dir = prompt_dir or Path(__file__).resolve().parents[1] / "prompts"

    def load(self, prompt_name: str) -> str:
        path = self.prompt_dir / prompt_name
        if not path.exists():
            raise PromptLoaderError(f"Prompt file '{prompt_name}' was not found.")
        return path.read_text(encoding="utf-8")
