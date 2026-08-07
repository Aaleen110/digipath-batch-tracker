from datetime import datetime, timezone

from sqlalchemy import DateTime, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Batch(Base):
    __tablename__ = "batches"

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
        Text,
        nullable=True,
    )

    partner_webhook: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )

    idempotency_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_batches_status", "status"),
        Index("ix_batches_batch_type", "batch_type"),
        Index("ix_batches_created_at", "created_at"),
    )