"""
Service functions for the FormPanelField domain.

A FormPanelField represents a non‑reusable instance of a field
definition placed directly on a FormPanel. This service provides
CRUD operations scoped to a tenant and publishes lifecycle events
to the message broker. Operations mirror those found in other
services: create, retrieve, list, update, and delete.
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

from app.domain.models import FormPanelField
from app.domain.schemas.form_panel_field import (
    FormPanelFieldCreate,
    FormPanelFieldUpdate,
    FormPanelFieldOut,
)
from app.messaging.producers.form_panel_field_producer import (
    FormPanelFieldProducer,
)


logger = logging.getLogger(__name__)


def create_form_panel_field(
    db: Session,
    tenant_id: UUID,
    data: FormPanelFieldCreate,
    created_by: str = "system",
) -> FormPanelField:
    """Create a new FormPanelField for a tenant.

    This instantiates a field instance on a specific FormPanel with
    optional overrides and ordering.
    """
    logger.info(
        "Creating FormPanelField tenant_id=%s form_panel_id=%s field_def_id=%s",
        tenant_id,
        data.form_panel_id,
        data.field_def_id,
    )
    instance = FormPanelField(
        tenant_id=tenant_id,
        form_panel_id=data.form_panel_id,
        field_def_id=data.field_def_id,
        overrides=data.overrides,
        field_order=data.field_order or 0,
        is_required=data.is_required or False,
        created_by=data.created_by or created_by,
    )
    db.add(instance)
    try:
        db.commit()
        db.refresh(instance)
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error while creating FormPanelField")
        raise HTTPException(
            status_code=500, detail="An error occurred while creating the panel field."
        )
    payload = FormPanelFieldOut.model_validate(instance).model_dump(mode="json")
    FormPanelFieldProducer.send_form_panel_field_created(
        tenant_id=tenant_id,
        form_panel_field_id=instance.form_panel_field_id,
        form_panel_id=instance.form_panel_id,
        field_def_id=instance.field_def_id,
        payload=payload,
    )
    return instance


def get_form_panel_field(
    db: Session, tenant_id: UUID, form_panel_field_id: UUID
) -> FormPanelField:
    """Retrieve a single FormPanelField by identifier for the given tenant."""
    instance = db.get(FormPanelField, form_panel_field_id)
    if instance is None or instance.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FormPanelField not found",
        )
    return instance


def list_form_panel_fields(
    db: Session,
    tenant_id: UUID,
    form_panel_id: Optional[UUID] = None,
    field_def_id: Optional[UUID] = None,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[FormPanelField], int]:
    """Return a paginated list of FormPanelField records for a tenant."""
    base_stmt = select(FormPanelField).where(FormPanelField.tenant_id == tenant_id)
    if form_panel_id is not None:
        base_stmt = base_stmt.where(FormPanelField.form_panel_id == form_panel_id)
    if field_def_id is not None:
        base_stmt = base_stmt.where(FormPanelField.field_def_id == field_def_id)
    try:
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total: int = db.execute(count_stmt).scalar_one()
        stmt = base_stmt.order_by(FormPanelField.field_order.asc()).limit(limit).offset(offset)
        items = db.execute(stmt).scalars().all()
        return items, total
    except SQLAlchemyError:
        logger.exception(
            "Database error while listing FormPanelFields tenant_id=%s", tenant_id
        )
        raise HTTPException(
            status_code=500, detail="An error occurred while retrieving panel fields."
        )


def update_form_panel_field(
    db: Session,
    tenant_id: UUID,
    form_panel_field_id: UUID,
    data: FormPanelFieldUpdate,
    modified_by: str = "system",
) -> FormPanelField:
    """Update an existing FormPanelField record."""
    instance = get_form_panel_field(db, tenant_id, form_panel_field_id)
    changes: Dict[str, Any] = {}
    if data.form_panel_id is not None and data.form_panel_id != instance.form_panel_id:
        changes["form_panel_id"] = str(data.form_panel_id)
        instance.form_panel_id = data.form_panel_id
    if data.field_def_id is not None and data.field_def_id != instance.field_def_id:
        changes["field_def_id"] = str(data.field_def_id)
        instance.field_def_id = data.field_def_id
    if data.overrides is not None and data.overrides != instance.overrides:
        changes["overrides"] = data.overrides
        instance.overrides = data.overrides
    if data.field_order is not None and data.field_order != instance.field_order:
        changes["field_order"] = data.field_order
        instance.field_order = data.field_order
    if data.is_required is not None and data.is_required != instance.is_required:
        changes["is_required"] = data.is_required
        instance.is_required = data.is_required
    instance.updated_at = datetime.utcnow()
    instance.updated_by = data.updated_by or modified_by
    try:
        db.commit()
        db.refresh(instance)
    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Database error while updating FormPanelField id=%s tenant_id=%s",
            form_panel_field_id,
            tenant_id,
        )
        raise HTTPException(
            status_code=500, detail="An error occurred while updating the panel field."
        )
    if changes:
        payload = FormPanelFieldOut.model_validate(instance).model_dump(mode="json")
        FormPanelFieldProducer.send_form_panel_field_updated(
            tenant_id=tenant_id,
            form_panel_field_id=form_panel_field_id,
            form_panel_id=instance.form_panel_id,
            field_def_id=instance.field_def_id,
            changes=changes,
            payload=payload,
        )
    return instance


def delete_form_panel_field(
    db: Session, tenant_id: UUID, form_panel_field_id: UUID
) -> None:
    """Delete a FormPanelField record and publish an event."""
    instance = get_form_panel_field(db, tenant_id, form_panel_field_id)
    try:
        form_panel_id = instance.form_panel_id
        field_def_id = instance.field_def_id
        db.delete(instance)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Database error while deleting FormPanelField id=%s tenant_id=%s",
            form_panel_field_id,
            tenant_id,
        )
        raise HTTPException(
            status_code=500, detail="An error occurred while deleting the panel field."
        )
    FormPanelFieldProducer.send_form_panel_field_deleted(
        tenant_id=tenant_id,
        form_panel_field_id=form_panel_field_id,
        form_panel_id=form_panel_id,
        field_def_id=field_def_id,
    )
    return None