from fastapi import APIRouter

from models.agent_models import AgentQuestionRequest, AgentQuestionResponse
from services.agent_service import AgentService


router = APIRouter(prefix="/agent", tags=["agent"])
agent_service = AgentService()


@router.post("/ask", response_model=AgentQuestionResponse)
def ask_agent(request: AgentQuestionRequest) -> AgentQuestionResponse:
    return agent_service.answer_question(request)
