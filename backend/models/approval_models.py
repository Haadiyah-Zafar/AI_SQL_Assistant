from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ApprovalStatus = Literal["pending", "approved", "rejected"]


class ApprovalCreateRequest(BaseModel):
    database_id: str
    sql: str
    reason: str = "This query may modify data."


class ApprovalDecisionRequest(BaseModel):
    approved: bool
    reviewer_note: str | None = None


class ApprovalRecord(BaseModel):
    approval_id: str
    database_id: str
    sql: str
    reason: str
    status: ApprovalStatus = "pending"
    reviewer_note: str | None = None
    created_at: datetime
    decided_at: datetime | None = None


class ApprovalCreateResponse(BaseModel):
    approval: ApprovalRecord


class ApprovalDecisionResponse(BaseModel):
    approval: ApprovalRecord
