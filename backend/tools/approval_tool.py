from models.approval_models import ApprovalCreateRequest, ApprovalRecord
from services.approval_service import ApprovalService


class ApprovalTool:
    def __init__(self, approval_service: ApprovalService | None = None) -> None:
        self.approval_service = approval_service or ApprovalService()

    def request_approval(
        self,
        database_id: str,
        sql: str,
        reason: str = "This query may modify data.",
    ) -> ApprovalRecord:
        response = self.approval_service.create_approval(
            ApprovalCreateRequest(database_id=database_id, sql=sql, reason=reason)
        )
        return response.approval
