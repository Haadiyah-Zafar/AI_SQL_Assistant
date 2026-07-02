from datetime import datetime, timezone
from uuid import uuid4

from models.approval_models import (
    ApprovalCreateRequest,
    ApprovalCreateResponse,
    ApprovalDecisionRequest,
    ApprovalDecisionResponse,
    ApprovalRecord,
)


class ApprovalNotFoundError(Exception):
    pass


class ApprovalAlreadyDecidedError(Exception):
    pass


class ApprovalService:
    def __init__(self) -> None:
        self._approvals: dict[str, ApprovalRecord] = {}

    def create_approval(self, request: ApprovalCreateRequest) -> ApprovalCreateResponse:
        approval = ApprovalRecord(
            approval_id=uuid4().hex,
            database_id=request.database_id,
            sql=request.sql,
            reason=request.reason,
            created_at=datetime.now(timezone.utc),
        )
        self._approvals[approval.approval_id] = approval
        return ApprovalCreateResponse(approval=approval)

    def get_approval(self, approval_id: str) -> ApprovalRecord:
        try:
            return self._approvals[approval_id]
        except KeyError as exc:
            raise ApprovalNotFoundError(f"Approval '{approval_id}' was not found.") from exc

    def decide(
        self,
        approval_id: str,
        request: ApprovalDecisionRequest,
    ) -> ApprovalDecisionResponse:
        approval = self.get_approval(approval_id)
        if approval.status != "pending":
            raise ApprovalAlreadyDecidedError(
                f"Approval '{approval_id}' has already been {approval.status}."
            )

        updated = ApprovalRecord(
            approval_id=approval.approval_id,
            database_id=approval.database_id,
            sql=approval.sql,
            reason=approval.reason,
            status="approved" if request.approved else "rejected",
            reviewer_note=request.reviewer_note,
            created_at=approval.created_at,
            decided_at=datetime.now(timezone.utc),
        )
        self._approvals[approval_id] = updated
        return ApprovalDecisionResponse(approval=updated)
