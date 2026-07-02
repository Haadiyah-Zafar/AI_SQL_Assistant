from fastapi import APIRouter, HTTPException, status

from models.approval_models import (
    ApprovalCreateRequest,
    ApprovalCreateResponse,
    ApprovalDecisionRequest,
    ApprovalDecisionResponse,
    ApprovalRecord,
)
from services.approval_service import (
    ApprovalAlreadyDecidedError,
    ApprovalNotFoundError,
    ApprovalService,
)


router = APIRouter(prefix="/approvals", tags=["approvals"])
approval_service = ApprovalService()


@router.post("", response_model=ApprovalCreateResponse)
def create_approval(request: ApprovalCreateRequest) -> ApprovalCreateResponse:
    return approval_service.create_approval(request)


@router.get("/{approval_id}", response_model=ApprovalRecord)
def get_approval(approval_id: str) -> ApprovalRecord:
    try:
        return approval_service.get_approval(approval_id)
    except ApprovalNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post("/{approval_id}/decision", response_model=ApprovalDecisionResponse)
def decide_approval(
    approval_id: str,
    request: ApprovalDecisionRequest,
) -> ApprovalDecisionResponse:
    try:
        return approval_service.decide(approval_id, request)
    except ApprovalNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ApprovalAlreadyDecidedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
