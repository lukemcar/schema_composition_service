"""
Pydantic schemas for the FormSubmission domain.

Form submissions capture an instance of data entry against a Form. These
schemas support creation, updating (status changes), and returning
submissions.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.schemas.common import PaginationEnvelope


class FormSubmissionBase(BaseModel):
    """Shared fields for FormSubmission create/update."""

    form_id: UUID
    submission_status: Optional[str] = Field("draft", max_length=50)
    submitted_at: Optional[datetime] = None
    submitted_by: Optional[str] = None
    created_by: Optional[str] = None


class FormSubmissionCreate(FormSubmissionBase):
    """Schema for creating a FormSubmission."""

    pass


class FormSubmissionUpdate(BaseModel):
    """Schema for updating a FormSubmission."""

    submission_status: Optional[str] = Field(None, max_length=50)
    submitted_at: Optional[datetime] = None
    submitted_by: Optional[str] = None
    updated_by: Optional[str] = None


class FormSubmissionOut(FormSubmissionBase):
    """Schema for returning a FormSubmission."""

    form_submission_id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    model_config = {"from_attributes": True}


class FormSubmissionListResponse(PaginationEnvelope[FormSubmissionOut]):
    """Paginated response for FormSubmissions."""

    items: List[FormSubmissionOut]