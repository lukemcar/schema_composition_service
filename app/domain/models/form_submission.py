"""
SQLAlchemy model for the FormSubmission domain.

A FormSubmission represents a submission envelope for a form. Each record
captures the status (draft, submitted, etc.), timestamps, and audit
metadata. Actual field values are stored in the associated
FormSubmissionValue table.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class FormSubmission(Base):
    """Database model for form submissions."""

    __tablename__ = "form_submission"

    form_submission_id: uuid.UUID = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    tenant_id: uuid.UUID = Column(UUID(as_uuid=True), nullable=False)
    form_id: uuid.UUID = Column(UUID(as_uuid=True), nullable=False)
    submission_status: str = Column(String(50), nullable=False, default="draft")
    submitted_at: datetime = Column(DateTime, nullable=True)
    submitted_by: str = Column(String(100), nullable=True)
    created_at: datetime = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by: str = Column(String(100), nullable=True)
    updated_by: str = Column(String(100), nullable=True)
    is_deleted: bool = Column(Boolean, nullable=False, default=False)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<FormSubmission form_submission_id={self.form_submission_id} "
            f"form_id={self.form_id} status={self.submission_status}>"
        )