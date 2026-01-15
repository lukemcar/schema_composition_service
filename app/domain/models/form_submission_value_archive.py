"""
SQLAlchemy model for the FormSubmissionValueArchive domain.

Archive table for captured field values belonging to archived form submissions.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import String, DateTime, Index, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models.base import Base


class FormSubmissionValueArchive(Base):  # type: ignore[type-arg]
    """Archive table for captured field values belonging to archived form submissions."""

    __tablename__ = "form_submission_value_archive"
    __table_args__ = (
        Index("ix_form_submission_value_archive_tenant", "tenant_id"),
        Index("ix_form_submission_value_archive_submission", "tenant_id", "form_submission_id"),
        {"schema": "schema_composition"},
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    form_submission_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    field_def_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)

    field_path: Mapped[str] = mapped_column(String(800), nullable=False)

    form_panel_field_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    form_panel_component_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))
    component_panel_field_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True))

    value: Mapped[Optional[dict]] = mapped_column(JSONB)
    value_search_text: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    created_by: Mapped[Optional[str]] = mapped_column(String(100))
    updated_by: Mapped[Optional[str]] = mapped_column(String(100))

    archived_moved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return (
            f"<FormSubmissionValueArchive id={self.id} tenant_id={self.tenant_id} form_submission_id={self.form_submission_id}>"
        )
