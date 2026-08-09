import logging
from dataclasses import dataclass

from sqlalchemy import func, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Query, Session

from app.models import Batch, utc_now
from app.schemas import BatchStatus, CreateBatchRequest

logger = logging.getLogger(__name__)


VALID_TRANSITIONS: dict[BatchStatus, set[BatchStatus]] = {
    BatchStatus.QUEUED: {
        BatchStatus.PROCESSING,
    },
    BatchStatus.PROCESSING: {
        BatchStatus.COMPLETED,
        BatchStatus.FAILED,
    },
    BatchStatus.COMPLETED: set(),
    BatchStatus.FAILED: set(),
}


class BatchNotFoundError(Exception):
    """Raised when a batch id does not exist."""


class InvalidTransitionError(Exception):
    def __init__(self, current: BatchStatus, new: BatchStatus) -> None:
        self.current = current
        self.new = new
        super().__init__(
            f"Invalid status transition: {current.value} -> {new.value}"
        )


class StatusConflictError(Exception):
    """Raised when an atomic status update loses a concurrent race."""


@dataclass(frozen=True)
class CreateBatchResult:
    batch: Batch
    created: bool


@dataclass(frozen=True)
class BatchListResult:
    items: list[Batch]
    total: int
    page: int
    page_size: int


def is_valid_transition(
    current_status: BatchStatus,
    new_status: BatchStatus,
) -> bool:
    return new_status in VALID_TRANSITIONS.get(current_status, set())


def get_batch_or_404(db: Session, batch_id: int) -> Batch:
    batch = (
        db.query(Batch)
        .filter(Batch.id == batch_id)
        .first()
    )

    if not batch:
        raise BatchNotFoundError()

    return batch


def create_batch(
    db: Session,
    payload: CreateBatchRequest,
    idempotency_key: str,
) -> CreateBatchResult:
    existing_batch = (
        db.query(Batch)
        .filter(Batch.idempotency_key == idempotency_key)
        .first()
    )

    if existing_batch:
        logger.info(
            "Idempotent batch create replay",
            extra={
                "event": "batch.create.idempotent_replay",
                "batch_id": existing_batch.id,
                "idempotency_key": idempotency_key,
            },
        )
        return CreateBatchResult(batch=existing_batch, created=False)

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

        logger.info(
            "Batch created",
            extra={
                "event": "batch.create.success",
                "batch_id": batch.id,
                "idempotency_key": idempotency_key,
            },
        )
        return CreateBatchResult(batch=batch, created=True)

    except IntegrityError:
        db.rollback()

        existing_batch = (
            db.query(Batch)
            .filter(Batch.idempotency_key == idempotency_key)
            .first()
        )

        if existing_batch:
            logger.info(
                "Idempotent batch create replay after race",
                extra={
                    "event": "batch.create.idempotent_replay",
                    "batch_id": existing_batch.id,
                    "idempotency_key": idempotency_key,
                },
            )
            return CreateBatchResult(batch=existing_batch, created=False)

        raise


def update_batch_status(
    db: Session,
    batch_id: int,
    new_status: BatchStatus,
) -> Batch:
    batch = get_batch_or_404(db, batch_id)
    current_status = BatchStatus(batch.status)

    if not is_valid_transition(current_status, new_status):
        raise InvalidTransitionError(current_status, new_status)

    result = db.execute(
        update(Batch)
        .where(
            Batch.id == batch_id,
            Batch.status == current_status.value,
        )
        .values(status=new_status.value, updated_at=utc_now())
    )

    if result.rowcount != 1:
        db.rollback()
        logger.warning(
            "Batch status update conflict",
            extra={
                "event": "batch.status.conflict",
                "batch_id": batch_id,
                "expected_status": current_status.value,
                "requested_status": new_status.value,
            },
        )
        raise StatusConflictError()

    db.commit()
    db.refresh(batch)

    logger.info(
        "Batch status updated",
        extra={
            "event": "batch.status.updated",
            "batch_id": batch_id,
            "from_status": current_status.value,
            "to_status": new_status.value,
        },
    )
    return batch


def _apply_list_filters(
    query: Query,
    status_filter: BatchStatus | None,
    batch_type: str | None,
) -> Query:
    if status_filter is not None:
        query = query.filter(Batch.status == status_filter.value)

    if batch_type is not None:
        query = query.filter(
            func.lower(Batch.batch_type) == batch_type.lower()
        )

    return query


def list_batches(
    db: Session,
    *,
    status_filter: BatchStatus | None,
    batch_type: str | None,
    page: int,
    page_size: int,
) -> BatchListResult:
    offset = (page - 1) * page_size
    total_count = func.count(Batch.id).over().label("total_count")

    query = _apply_list_filters(
        db.query(Batch, total_count),
        status_filter,
        batch_type,
    )

    rows = (
        query
        .order_by(Batch.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    if rows:
        items = [row[0] for row in rows]
        total = rows[0][1]
    else:
        items = []
        count_query = _apply_list_filters(
            db.query(func.count(Batch.id)),
            status_filter,
            batch_type,
        )
        total = count_query.scalar() or 0

    return BatchListResult(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )
