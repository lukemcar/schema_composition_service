"""
SQLAlchemy model for the FormSubmissionValue domain.

This table stores captured values for each field instance within a form
submission. Each value is linked to a submission and identifies the field
instance via a fully qualified path (supports nested structures). For
flexibility, values are stored as JSON.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import String

from .base import Base


class FormSubmissionValue(Base):
    """Database model for individual values within a form submission."""

    __tablename__ = "form_submission_value"

    form_submission_value_id: uuid.UUID = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    tenant_id: uuid.UUID = Column(UUID(as_uuid=True), nullable=False)
    form_submission_id: uuid.UUID = Column(UUID(as_uuid=True), nullable=False)
    field_instance_path: str = Column(String(255), nullable=False)
    value: dict = Column(JSONB, nullable=True)
    created_at: datetime = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by: str = Column(String(100), nullable=True)
    updated_by: str = Column(String(100), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<FormSubmissionValue form_submission_value_id={self.form_submission_value_id} "
            f"submission_id={self.form_submission_id} path={self.field_instance_path}>"
        )