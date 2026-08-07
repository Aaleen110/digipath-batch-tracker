from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import verify_api_key
from app.database import get_db
from app.models import Batch
from app.schemas import BatchResponse, CreateBatchRequest

from sqlalchemy import update

from app.schemas import (
    BatchStatus,
    UpdateStatusRequest,
)
from app.services.batch_service import is_valid_transition

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