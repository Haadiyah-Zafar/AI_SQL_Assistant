from pydantic import BaseModel

from models.agent_state import AgentIntent


class IntentClassificationResult(BaseModel):
    intent: AgentIntent
    confidence: float
    reason: str
