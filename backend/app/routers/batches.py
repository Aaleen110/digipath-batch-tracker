from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import func, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import verify_api_key
from app.database import get_db
from app.models import Batch
from app.schemas import (
    BatchListResponse,
    BatchResponse,
    BatchStatus,
    CreateBatchRequest,
    UpdateStatusRequest,
)
from app.services.batch_service import is_valid_transition
from app.services.notify import (
    UnsafeWebhookURLError,
    WebhookNotificationError,
    notify_webhook,
)


router = APIRouter(
    prefix="/batches",
    tags=["batches"],
    dependencies=[Depends(verify_api_key)],
)


@router.post(
    "",
    response_model=BatchResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_batch(
    payload: CreateBatchRequest,
    idempotency_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    if not idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key header is required",
        )

    existing_batch = (
        db.query(Batch)
        .filter(Batch.idempotency_key == idempotency_key)
        .first()
    )

    if existing_batch:
        return existing_batch

    try:
        batch = Batch(
            sample_id=payload.sample_id,
            batch_type=payload.batch_type,
            submitted_by=payload.submitted_by,
            partner_webhook=payload.partner_webhook,
            status="queued",
            idempotency_key=idempotency_key,
        )

        db.add(batch)
        db.commit()
        db.refresh(batch)

        return batch

    except IntegrityError:
        db.rollback()

        existing_batch = (
            db.query(Batch)
            .filter(Batch.idempotency_key == idempotency_key)
            .first()
        )

        if existing_batch:
            return existing_batch

        raise


@router.get(
    "/{batch_id}",
    response_model=BatchResponse,
)
def get_batch(
    batch_id: int,
    db: Session = Depends(get_db),
):
    batch = (
        db.query(Batch)
        .filter(Batch.id == batch_id)
        .first()
    )

    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found",
        )

    return batch


@router.patch(
    "/{batch_id}/status",
    response_model=BatchResponse,
)
def update_batch_status(
    batch_id: int,
    payload: UpdateStatusRequest,
    db: Session = Depends(get_db),
):
    batch = (
        db.query(Batch)
        .filter(Batch.id == batch_id)
        .first()
    )

    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found",
        )

    current_status = BatchStatus(batch.status)
    new_status = payload.status

    if not is_valid_transition(current_status, new_status):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Invalid status transition: "
                f"{current_status.value} -> {new_status.value}"
            ),
        )

    # The status check is part of the UPDATE itself. This makes the
    # transition atomic and prevents two concurrent requests from
    # both successfully changing the same state.
    result = db.execute(
        update(Batch)
        .where(
            Batch.id == batch_id,
            Batch.status == current_status.value,
        )
        .values(status=new_status.value)
    )

    if result.rowcount != 1:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Batch status was changed by another request",
        )

    db.commit()
    db.refresh(batch)

    return batch


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
    query = db.query(Batch)

    if status_filter is not None:
        query = query.filter(
            Batch.status == status_filter.value
        )

    if batch_type is not None:
        query = query.filter(
            func.lower(Batch.batch_type) == batch_type.lower()
        )

    total = query.with_entities(
        func.count(Batch.id)
    ).scalar()

    offset = (page - 1) * page_size

    batches = (
        query
        .order_by(Batch.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return BatchListResponse(
        items=batches,
        page=page,
        page_size=page_size,
        total=total,
    )


@router.post(
    "/{batch_id}/notify",
    status_code=status.HTTP_202_ACCEPTED,
)
def notify_batch(
    batch_id: int,
    db: Session = Depends(get_db),
):
    batch = (
        db.query(Batch)
        .filter(Batch.id == batch_id)
        .first()
    )

    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found",
        )

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

    try:
        notify_webhook(
            webhook_url=batch.partner_webhook,
            payload=payload,
        )

    except UnsafeWebhookURLError as exc:
        # Never expose internal networking details to the API consumer.
        # The service logs/security layer can capture the detailed reason.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or unsafe webhook URL",
        ) from exc

    except WebhookNotificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return {
        "message": "Batch notification sent successfully",
        "batch_id": batch.id,
    }