from datetime import datetime, timezone

from sqlalchemy import DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Batch(Base):
    __tablename__ = "batches"

    # Indexes for GET /batches?status=&type= — see README scaling section
    __table_args__ = (
        Index("ix_batches_status", "status"),
        Index("ix_batches_batch_type", "batch_type"),
        Index(
            "ix_batches_status_batch_type",
            "status",
            "batch_type",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    sample_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    batch_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    submitted_by: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="queued",
    )

    result: Mapped[str | None] = mapped_column(
        nullable=True,
    )

    partner_webhook: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )

    # Client-supplied on POST /batches — unique so retries don't create duplicates
    idempotency_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )