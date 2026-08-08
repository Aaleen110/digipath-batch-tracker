from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class BatchStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class CreateBatchRequest(BaseModel):
    sample_id: str = Field(min_length=1, max_length=100)
    batch_type: str = Field(min_length=1, max_length=100)
    submitted_by: str = Field(min_length=1, max_length=100)
    partner_webhook: str | None = Field(
        default=None,
        max_length=2048,
    )


class UpdateStatusRequest(BaseModel):
    status: BatchStatus


class BatchResponse(BaseModel):
    id: int
    sample_id: str
    batch_type: str
    submitted_by: str
    status: BatchStatus
    result: str | None
    partner_webhook: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


class BatchListResponse(BaseModel):
    items: list[BatchResponse]
    page: int
    page_size: int
    total: int