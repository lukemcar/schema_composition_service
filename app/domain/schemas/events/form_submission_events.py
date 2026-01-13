"""
Event payload schemas for the FormSubmission domain.

Messages describing creation, update and deletion of form submissions.
"""

from __future__ import annotations

from typing import Dict, Any
from uuid import UUID

from pydantic import BaseModel


class FormSubmissionCreatedMessage(BaseModel):
    tenant_id: UUID
    form_submission_id: UUID
    form_id: UUID
    payload: Dict[str, Any]


class FormSubmissionUpdatedMessage(BaseModel):
    tenant_id: UUID
    form_submission_id: UUID
    form_id: UUID
    changes: Dict[str, Any]
    payload: Dict[str, Any]


class FormSubmissionDeletedMessage(BaseModel):
    tenant_id: UUID
    form_submission_id: UUID
    form_id: UUID