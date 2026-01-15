"""
SQLAlchemy model for the ``form_submission`` table.

This model mirrors the DDL for ``schema_composition.form_submission``.  A
submission is an updatable envelope for capturing values against a form.
Submissions support draft and submitted states, track the number of times
they have been submitted, and enforce consistency between lifecycle flags
and timestamps.

Captured values themselves live in ``form_submission_value``.  This table
only stores metadata about the submission envelope.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class FormSubmission(Base):  # type: ignore[type-arg]
    """Updatable submission envelope for a specific form.

    Submissions can be saved as drafts (``is_submitted = False``) and later
    submitted one or more times.  ``submission_version`` tracks how many
    times the submission has been submitted.  Timestamps must align with
    lifecycle flags as enforced by check constraints.
    """

    __tablename__ = "form_submission"
    __table_args__ = (
        # Canonical tenant‑safe unique constraint.
        UniqueConstraint("tenant_id", "id", name="ux_form_submission_tenant_id"),
        # Non‑negative submission counter.
        CheckConstraint(
            "submission_version >= 0",
            name="ck_form_submission_version_non_negative",
        ),
        # Align draft/submitted state with timestamps and version counter.
        CheckConstraint(
            "(is_submitted = FALSE AND submitted_at IS NULL AND submission_version = 0)"
            " OR (is_submitted = TRUE  AND submitted_at IS NOT NULL AND submission_version >= 1)",
            name="ck_form_submission_submitted_state_consistency",
        ),
        # Archived timestamp must align with archived flag.
        CheckConstraint(
            "(is_archived = TRUE  AND archived_at IS NOT NULL) OR (is_archived = FALSE AND archived_at IS NULL)",
            name="ck_form_submission_archived_at_consistency",
        ),
        # Tenant‑safe FK to forms.
        ForeignKeyConstraint(
            ["tenant_id", "form_id"],
            ["form.tenant_id", "form.id"],
            name="fk_form_submission_form_tenant",
            ondelete="CASCADE",
        ),
        # Indexes
        Index("ix_form_submission_tenant_form", "tenant_id", "form_id"),
        Index(
            "ix_form_submission_tenant_form_updated_at",
            "tenant_id",
            "form_id",
            "updated_at",
        ),
        # Schema specification
        {"schema": "schema_composition"},
    )

    # ---------------------------------------------------------------------
    # Primary identity
    # ---------------------------------------------------------------------
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    # ---------------------------------------------------------------------
    # Tenant boundary and form reference
    # ---------------------------------------------------------------------
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    form_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    # ---------------------------------------------------------------------
    # Submission lifecycle
    # ---------------------------------------------------------------------
    is_submitted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    submission_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # ---------------------------------------------------------------------
    # Audit columns
    # ---------------------------------------------------------------------
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(100))
    updated_by: Mapped[Optional[str]] = mapped_column(String(100))

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<FormSubmission id={self.id} tenant_id={self.tenant_id} form_id={self.form_id} "
            f"is_submitted={self.is_submitted} version={self.submission_version}>"
        )


__all__ = ["FormSubmission"]