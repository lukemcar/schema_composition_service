"""
Event payload schemas for the FormSubmissionValue domain.

Messages describing changes to captured values within a submission.
"""

from __future__ import annotations

from typing import Dict, Any
from uuid import UUID

from pydantic import BaseModel


class FormSubmissionValueCreatedMessage(BaseModel):
    tenant_id: UUID
    form_submission_value_id: UUID
    form_submission_id: UUID
    field_instance_path: str
    payload: Dict[str, Any]


class FormSubmissionValueUpdatedMessage(BaseModel):
    tenant_id: UUID
    form_submission_value_id: UUID
    form_submission_id: UUID
    field_instance_path: str
    changes: Dict[str, Any]
    payload: Dict[str, Any]


class FormSubmissionValueDeletedMessage(BaseModel):
    tenant_id: UUID
    form_submission_value_id: UUID
    form_submission_id: UUID
    field_instance_path: str