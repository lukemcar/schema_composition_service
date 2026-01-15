"""
SQLAlchemy model for the FormSubmissionArchive domain.

Archive table for form submissions that have exited the active lifecycle.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Integer, String, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models.base import Base


class FormSubmissionArchive(Base):  # type: ignore[type-arg]
    """Archive table for form submissions that are no longer active."""

    __tablename__ = "form_submission_archive"
    __table_args__ = (
        Index("ix_form_submission_archive_tenant", "tenant_id"),
        Index("ix_form_submission_archive_tenant_form", "tenant_id", "form_id"),
        {"schema": "schema_composition"},
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    form_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)

    is_submitted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    submission_version: Mapped[int] = mapped_column(Integer, nullable=False)

    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False)
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    created_by: Mapped[Optional[str]] = mapped_column(String(100))
    updated_by: Mapped[Optional[str]] = mapped_column(String(100))

    archived_moved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return (
            f"<FormSubmissionArchive id={self.id} tenant_id={self.tenant_id} form_id={self.form_id}>"
        )
