"""
Service functions for the FormSubmission domain.

FormSubmission records encapsulate an instance of data entry against a
Form. They capture the overall submission envelope, status (e.g.
draft, submitted) and audit metadata. Values for individual fields
within a submission are stored in the FormSubmissionValue table.

This module exposes CRUD operations for submissions and publishes
corresponding events via Celery.
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

from app.domain.models import FormSubmission
from app.domain.schemas.form_submission import (
    FormSubmissionCreate,
    FormSubmissionUpdate,
    FormSubmissionOut,
)
from app.messaging.producers.form_submission_producer import FormSubmissionProducer


logger = logging.getLogger(__name__)


def create_form_submission(
    db: Session,
    tenant_id: UUID,
    data: FormSubmissionCreate,
    created_by: str = "system",
) -> FormSubmission:
    """Create a new FormSubmission record for a tenant."""
    logger.info(
        "Creating FormSubmission tenant_id=%s form_id=%s", tenant_id, data.form_id
    )
    submission = FormSubmission(
        tenant_id=tenant_id,
        form_id=data.form_id,
        submission_status=data.submission_status or "draft",
        submitted_at=data.submitted_at,
        submitted_by=data.submitted_by,
        created_by=data.created_by or created_by,
    )
    db.add(submission)
    try:
        db.commit()
        db.refresh(submission)
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error while creating FormSubmission")
        raise HTTPException(
            status_code=500, detail="An error occurred while creating the submission."
        )
    payload = FormSubmissionOut.model_validate(submission).model_dump(mode="json")
    FormSubmissionProducer.send_form_submission_created(
        tenant_id=tenant_id,
        form_submission_id=submission.form_submission_id,
        form_id=submission.form_id,
        payload=payload,
    )
    return submission


def get_form_submission(
    db: Session, tenant_id: UUID, form_submission_id: UUID
) -> FormSubmission:
    """Retrieve a single FormSubmission by identifier, ensuring tenant ownership."""
    submission = db.get(FormSubmission, form_submission_id)
    if submission is None or submission.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FormSubmission not found",
        )
    return submission


def list_form_submissions(
    db: Session,
    tenant_id: UUID,
    form_id: Optional[UUID] = None,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[FormSubmission], int]:
    """Return a paginated list of FormSubmission records for a tenant."""
    base_stmt = select(FormSubmission).where(FormSubmission.tenant_id == tenant_id)
    if form_id is not None:
        base_stmt = base_stmt.where(FormSubmission.form_id == form_id)
    try:
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total: int = db.execute(count_stmt).scalar_one()
        stmt = base_stmt.order_by(FormSubmission.created_at.desc()).limit(limit).offset(offset)
        items = db.execute(stmt).scalars().all()
        return items, total
    except SQLAlchemyError:
        logger.exception(
            "Database error while listing FormSubmissions tenant_id=%s", tenant_id
        )
        raise HTTPException(
            status_code=500, detail="An error occurred while retrieving submissions."
        )


def update_form_submission(
    db: Session,
    tenant_id: UUID,
    form_submission_id: UUID,
    data: FormSubmissionUpdate,
    modified_by: str = "system",
) -> FormSubmission:
    """Update a FormSubmission record (e.g. change status, submitted_at)."""
    submission = get_form_submission(db, tenant_id, form_submission_id)
    changes: Dict[str, Any] = {}
    if data.submission_status is not None and data.submission_status != submission.submission_status:
        changes["submission_status"] = data.submission_status
        submission.submission_status = data.submission_status
    if data.submitted_at is not None and data.submitted_at != submission.submitted_at:
        changes["submitted_at"] = data.submitted_at.isoformat() if data.submitted_at else None
        submission.submitted_at = data.submitted_at
    if data.submitted_by is not None and data.submitted_by != submission.submitted_by:
        changes["submitted_by"] = data.submitted_by
        submission.submitted_by = data.submitted_by
    submission.updated_at = datetime.utcnow()
    submission.updated_by = data.updated_by or modified_by
    try:
        db.commit()
        db.refresh(submission)
    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Database error while updating FormSubmission id=%s tenant_id=%s",
            form_submission_id,
            tenant_id,
        )
        raise HTTPException(
            status_code=500, detail="An error occurred while updating the submission."
        )
    if changes:
        payload = FormSubmissionOut.model_validate(submission).model_dump(mode="json")
        FormSubmissionProducer.send_form_submission_updated(
            tenant_id=tenant_id,
            form_submission_id=form_submission_id,
            form_id=submission.form_id,
            changes=changes,
            payload=payload,
        )
    return submission


def delete_form_submission(db: Session, tenant_id: UUID, form_submission_id: UUID) -> None:
    """Delete a FormSubmission record and publish a deletion event."""
    submission = get_form_submission(db, tenant_id, form_submission_id)
    try:
        form_id = submission.form_id
        db.delete(submission)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Database error while deleting FormSubmission id=%s tenant_id=%s",
            form_submission_id,
            tenant_id,
        )
        raise HTTPException(
            status_code=500, detail="An error occurred while deleting the submission."
        )
    FormSubmissionProducer.send_form_submission_deleted(
        tenant_id=tenant_id,
        form_submission_id=form_submission_id,
        form_id=form_id,
    )
    return None