from models.approval_models import ApprovalCreateRequest, ApprovalDecisionRequest
from services.approval_service import ApprovalAlreadyDecidedError, ApprovalService


def test_approval_service_creates_and_approves_pending_request():
    service = ApprovalService()

    created = service.create_approval(
        ApprovalCreateRequest(
            database_id="sales",
            sql="UPDATE customers SET status = 'inactive'",
        )
    )
    decided = service.decide(
        created.approval.approval_id,
        ApprovalDecisionRequest(approved=True, reviewer_note="Looks correct."),
    )

    assert created.approval.status == "pending"
    assert decided.approval.status == "approved"
    assert decided.approval.reviewer_note == "Looks correct."
    assert decided.approval.decided_at is not None


def test_approval_service_rejects_second_decision():
    service = ApprovalService()
    created = service.create_approval(
        ApprovalCreateRequest(database_id="sales", sql="DELETE FROM customers")
    )

    service.decide(created.approval.approval_id, ApprovalDecisionRequest(approved=False))

    try:
        service.decide(created.approval.approval_id, ApprovalDecisionRequest(approved=True))
    except ApprovalAlreadyDecidedError:
        pass
    else:
        raise AssertionError("Expected second approval decision to fail")
