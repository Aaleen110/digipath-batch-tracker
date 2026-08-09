import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.auth import verify_api_key
from app.database import get_db
from app.schemas import (
    BatchListResponse,
    BatchResponse,
    BatchStatus,
    CreateBatchRequest,
    UpdateStatusRequest,
)
from app.services.batch_service import (
    BatchNotFoundError,
    InvalidTransitionError,
    StatusConflictError,
    create_batch as create_batch_service,
    get_batch_or_404,
    list_batches as list_batches_service,
    update_batch_status as update_batch_status_service,
)
from app.services.notify import (
    UnsafeWebhookURLError,
    WebhookNotificationError,
    notify_webhook,
)

logger = logging.getLogger(__name__)

# Auth on the whole router using Depends — /health in main.py stays public
router = APIRouter(
    prefix="/batches",
    tags=["batches"],
    dependencies=[Depends(verify_api_key)],
)


def _batch_not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Batch not found",
    )


@router.post(
    "",
    response_model=BatchResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_batch(
    payload: CreateBatchRequest,
    response: Response,
    idempotency_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    if not idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key header is required",
        )

    result = create_batch_service(db, payload, idempotency_key)
    # 201 = new batch, 200 = idempotent replay 
    response.status_code = (
        status.HTTP_201_CREATED if result.created else status.HTTP_200_OK
    )
    return result.batch


@router.get(
    "/{batch_id}",
    response_model=BatchResponse,
)
def get_batch(
    batch_id: int,
    db: Session = Depends(get_db),
):
    try:
        return get_batch_or_404(db, batch_id)
    except BatchNotFoundError as exc:
        raise _batch_not_found() from exc


@router.patch(
    "/{batch_id}/status",
    response_model=BatchResponse,
)
def update_batch_status(
    batch_id: int,
    payload: UpdateStatusRequest,
    db: Session = Depends(get_db),
):
    try:
        return update_batch_status_service(db, batch_id, payload.status)
    except BatchNotFoundError as exc:
        raise _batch_not_found() from exc
    except InvalidTransitionError as exc:
        # e.g. queued → completed skips processing
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except StatusConflictError as exc:
        # Lost a race — another request already moved this batch
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Batch status was changed by another request",
        ) from exc


@router.get(
    "",
    response_model=BatchListResponse,
)
def list_batches(
    status_filter: BatchStatus | None = Query(
        default=None,
        alias="status",
    ),
    batch_type: str | None = Query(
        default=None,
        alias="type",
        min_length=1,
        max_length=100,
    ),
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
):
    result = list_batches_service(
        db,
        status_filter=status_filter,
        batch_type=batch_type,
        page=page,
        page_size=page_size,
    )

    return BatchListResponse(
        items=result.items,
        page=result.page,
        page_size=result.page_size,
        total=result.total,
    )


@router.post(
    "/{batch_id}/notify",
    status_code=status.HTTP_202_ACCEPTED,
)
def notify_batch(
    batch_id: int,
    db: Session = Depends(get_db),
):
    try:
        batch = get_batch_or_404(db, batch_id)
    except BatchNotFoundError as exc:
        raise _batch_not_found() from exc

    if not batch.partner_webhook:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch does not have a partner webhook URL",
        )

    payload = {
        "batch_id": batch.id,
        "sample_id": batch.sample_id,
        "batch_type": batch.batch_type,
        "status": batch.status,
        "result": batch.result,
    }

    # NOTE: no dedup yet — calling notify twice sends two webhooks (see REVIEW.md)
    try:
        notify_webhook(
            webhook_url=batch.partner_webhook,
            payload=payload,
        )

    except UnsafeWebhookURLError as exc:
        # Don't leak SSRF details to the client — generic message only
        logger.warning(
            "Unsafe webhook URL rejected",
            extra={
                "event": "batch.notify.unsafe_url",
                "batch_id": batch.id,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or unsafe webhook URL",
        ) from exc

    except WebhookNotificationError as exc:
        logger.error(
            "Webhook notification failed",
            extra={
                "event": "batch.notify.failure",
                "batch_id": batch.id,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return {
        "message": "Batch notification sent successfully",
        "batch_id": batch.id,
    }
