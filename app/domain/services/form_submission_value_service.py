"""
Service functions for the FormSubmissionValue domain.

FormSubmissionValue records hold individual captured values within a
submission. Each value is linked to a FormSubmission via
``form_submission_id`` and is identified by a fully qualified path
(``field_instance_path``) to support nested structures. Values are
stored as JSON for flexibility.

This module provides CRUD operations scoped to a tenant and emits
lifecycle events via Celery producers.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.domain.models import FormSubmissionValue
from app.domain.schemas.form_submission_value import (
    FormSubmissionValueCreate,
    FormSubmissionValueUpdate,
    FormSubmissionValueOut,
)
from app.messaging.producers.form_submission_value_producer import (
    FormSubmissionValueProducer,
)


logger = logging.getLogger(__name__)


def create_form_submission_value(
    db: Session,
    tenant_id: UUID,
    data: FormSubmissionValueCreate,
    created_by: str = "system",
) -> FormSubmissionValue:
    """Create a new FormSubmissionValue for a tenant."""
    logger.info(
        "Creating FormSubmissionValue tenant_id=%s submission_id=%s path=%s",
        tenant_id,
        data.form_submission_id,
        data.field_instance_path,
    )
    value = FormSubmissionValue(
        tenant_id=tenant_id,
        form_submission_id=data.form_submission_id,
        field_instance_path=data.field_instance_path,
        value=data.value,
        created_by=data.created_by or created_by,
    )
    db.add(value)
    try:
        db.commit()
        db.refresh(value)
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error while creating FormSubmissionValue")
        raise HTTPException(
            status_code=500, detail="An error occurred while creating the submission value."
        )
    payload = FormSubmissionValueOut.model_validate(value).model_dump(mode="json")
    FormSubmissionValueProducer.send_form_submission_value_created(
        tenant_id=tenant_id,
        form_submission_value_id=value.form_submission_value_id,
        form_submission_id=value.form_submission_id,
        field_instance_path=value.field_instance_path,
        payload=payload,
    )
    return value


def get_form_submission_value(
    db: Session, tenant_id: UUID, form_submission_value_id: UUID
) -> FormSubmissionValue:
    """Retrieve a single FormSubmissionValue by identifier."""
    value = db.get(FormSubmissionValue, form_submission_value_id)
    if value is None or value.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FormSubmissionValue not found",
        )
    return value


def list_form_submission_values(
    db: Session,
    tenant_id: UUID,
    form_submission_id: Optional[UUID] = None,
    field_instance_path: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[FormSubmissionValue], int]:
    """Return a paginated list of FormSubmissionValue records for a tenant."""
    base_stmt = select(FormSubmissionValue).where(FormSubmissionValue.tenant_id == tenant_id)
    if form_submission_id is not None:
        base_stmt = base_stmt.where(
            FormSubmissionValue.form_submission_id == form_submission_id
        )
    if field_instance_path is not None:
        base_stmt = base_stmt.where(
            FormSubmissionValue.field_instance_path == field_instance_path
        )
    try:
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total: int = db.execute(count_stmt).scalar_one()
        stmt = base_stmt.order_by(FormSubmissionValue.created_at.asc()).limit(limit).offset(offset)
        items = db.execute(stmt).scalars().all()
        return items, total
    except SQLAlchemyError:
        logger.exception(
            "Database error while listing FormSubmissionValues tenant_id=%s", tenant_id
        )
        raise HTTPException(
            status_code=500, detail="An error occurred while retrieving submission values."
        )


def update_form_submission_value(
    db: Session,
    tenant_id: UUID,
    form_submission_value_id: UUID,
    data: FormSubmissionValueUpdate,
    modified_by: str = "system",
) -> FormSubmissionValue:
    """Update an existing FormSubmissionValue record."""
    value = get_form_submission_value(db, tenant_id, form_submission_value_id)
    changes: Dict[str, Any] = {}
    if data.field_instance_path is not None and data.field_instance_path != value.field_instance_path:
        changes["field_instance_path"] = data.field_instance_path
        value.field_instance_path = data.field_instance_path
    if data.value is not None and data.value != value.value:
        changes["value"] = data.value
        value.value = data.value
    value.updated_at = datetime.utcnow()
    value.updated_by = data.updated_by or modified_by
    try:
        db.commit()
        db.refresh(value)
    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Database error while updating FormSubmissionValue id=%s tenant_id=%s",
            form_submission_value_id,
            tenant_id,
        )
        raise HTTPException(
            status_code=500, detail="An error occurred while updating the submission value."
        )
    if changes:
        payload = FormSubmissionValueOut.model_validate(value).model_dump(mode="json")
        FormSubmissionValueProducer.send_form_submission_value_updated(
            tenant_id=tenant_id,
            form_submission_value_id=form_submission_value_id,
            form_submission_id=value.form_submission_id,
            field_instance_path=value.field_instance_path,
            changes=changes,
            payload=payload,
        )
    return value


def delete_form_submission_value(
    db: Session, tenant_id: UUID, form_submission_value_id: UUID
) -> None:
    """Delete a FormSubmissionValue record and publish an event."""
    value = get_form_submission_value(db, tenant_id, form_submission_value_id)
    try:
        form_submission_id = value.form_submission_id
        path = value.field_instance_path
        db.delete(value)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Database error while deleting FormSubmissionValue id=%s tenant_id=%s",
            form_submission_value_id,
            tenant_id,
        )
        raise HTTPException(
            status_code=500, detail="An error occurred while deleting the submission value."
        )
    FormSubmissionValueProducer.send_form_submission_value_deleted(
        tenant_id=tenant_id,
        form_submission_value_id=form_submission_value_id,
        form_submission_id=form_submission_id,
        field_instance_path=path,
    )
    return None