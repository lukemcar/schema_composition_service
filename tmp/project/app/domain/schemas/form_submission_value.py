"""
Pydantic schemas for the FormSubmissionValue domain.

FormSubmissionValue records hold individual field values captured within a
submission. Each is identified by a fully qualified field path.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.schemas.common import PaginationEnvelope


class FormSubmissionValueBase(BaseModel):
    """Shared fields for FormSubmissionValue create/update."""

    form_submission_id: UUID
    field_instance_path: str = Field(..., max_length=255)
    value: Optional[Dict[str, Any]] = None
    created_by: Optional[str] = None


class FormSubmissionValueCreate(FormSubmissionValueBase):
    """Schema for creating a FormSubmissionValue."""

    pass


class FormSubmissionValueUpdate(BaseModel):
    """Schema for updating a FormSubmissionValue."""

    field_instance_path: Optional[str] = Field(None, max_length=255)
    value: Optional[Dict[str, Any]] = None
    updated_by: Optional[str] = None


class FormSubmissionValueOut(FormSubmissionValueBase):
    """Schema for returning a FormSubmissionValue."""

    form_submission_value_id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FormSubmissionValueListResponse(PaginationEnvelope[FormSubmissionValueOut]):
    """Paginated response for FormSubmissionValues."""

    items: List[FormSubmissionValueOut]