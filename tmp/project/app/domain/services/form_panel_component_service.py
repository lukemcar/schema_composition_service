"""
Service functions for the FormPanelComponent domain.

CRUD operations for FormPanelComponent records. All operations are tenant
scoped. A FormPanelComponent represents an instance of a reusable
Component embedded into a specific FormPanel. Each placement may
override configuration and ordering. This service coordinates with
Celery producers to emit lifecycle events whenever records are created,
updated or deleted.
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

from app.domain.models import FormPanelComponent
from app.domain.schemas.form_panel_component import (
    FormPanelComponentCreate,
    FormPanelComponentUpdate,
    FormPanelComponentOut,
)
from app.messaging.producers.form_panel_component_producer import (
    FormPanelComponentProducer,
)


logger = logging.getLogger(__name__)


def create_form_panel_component(
    db: Session,
    tenant_id: UUID,
    data: FormPanelComponentCreate,
    created_by: str = "system",
) -> FormPanelComponent:
    """Create a new FormPanelComponent for a tenant.

    The ``tenant_id`` and ``form_panel_id`` indicate where this
    component instance lives. The ``component_id`` references the
    reusable Component definition. Configuration overrides and ordering
    can also be provided.
    """
    logger.info(
        "Creating FormPanelComponent tenant_id=%s form_panel_id=%s component_id=%s",
        tenant_id,
        data.form_panel_id,
        data.component_id,
    )
    placement = FormPanelComponent(
        tenant_id=tenant_id,
        form_panel_id=data.form_panel_id,
        component_id=data.component_id,
        config=data.config,
        component_order=data.component_order or 0,
        created_by=data.created_by or created_by,
    )
    db.add(placement)
    try:
        db.commit()
        db.refresh(placement)
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error while creating FormPanelComponent")
        raise HTTPException(
            status_code=500, detail="An error occurred while creating the panel component."
        )
    payload = FormPanelComponentOut.model_validate(placement).model_dump(mode="json")
    FormPanelComponentProducer.send_form_panel_component_created(
        tenant_id=tenant_id,
        form_panel_component_id=placement.form_panel_component_id,
        form_panel_id=placement.form_panel_id,
        component_id=placement.component_id,
        payload=payload,
    )
    return placement


def get_form_panel_component(
    db: Session, tenant_id: UUID, form_panel_component_id: UUID
) -> FormPanelComponent:
    """Retrieve a single FormPanelComponent by identifier.

    Ensures that the record belongs to the specified tenant, raising
    404 Not Found if not.
    """
    placement = db.get(FormPanelComponent, form_panel_component_id)
    if placement is None or placement.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FormPanelComponent not found",
        )
    return placement


def list_form_panel_components(
    db: Session,
    tenant_id: UUID,
    form_panel_id: Optional[UUID] = None,
    component_id: Optional[UUID] = None,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[FormPanelComponent], int]:
    """Return a paginated list of FormPanelComponent records for a tenant.

    Optional filters allow narrowing results to a specific panel or
    component.
    """
    base_stmt = select(FormPanelComponent).where(FormPanelComponent.tenant_id == tenant_id)
    if form_panel_id is not None:
        base_stmt = base_stmt.where(FormPanelComponent.form_panel_id == form_panel_id)
    if component_id is not None:
        base_stmt = base_stmt.where(FormPanelComponent.component_id == component_id)
    try:
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total: int = db.execute(count_stmt).scalar_one()
        stmt = base_stmt.order_by(FormPanelComponent.component_order.asc()).limit(limit).offset(offset)
        items = db.execute(stmt).scalars().all()
        return items, total
    except SQLAlchemyError:
        logger.exception(
            "Database error while listing FormPanelComponents tenant_id=%s", tenant_id
        )
        raise HTTPException(
            status_code=500, detail="An error occurred while retrieving panel components."
        )


def update_form_panel_component(
    db: Session,
    tenant_id: UUID,
    form_panel_component_id: UUID,
    data: FormPanelComponentUpdate,
    modified_by: str = "system",
) -> FormPanelComponent:
    """Update an existing FormPanelComponent record.

    Only fields provided in the update payload are modified. Any
    changes are captured and emitted in the corresponding update event.
    """
    placement = get_form_panel_component(db, tenant_id, form_panel_component_id)
    changes: Dict[str, Any] = {}
    if data.form_panel_id is not None and data.form_panel_id != placement.form_panel_id:
        changes["form_panel_id"] = str(data.form_panel_id)
        placement.form_panel_id = data.form_panel_id
    if data.component_id is not None and data.component_id != placement.component_id:
        changes["component_id"] = str(data.component_id)
        placement.component_id = data.component_id
    if data.config is not None and data.config != placement.config:
        changes["config"] = data.config
        placement.config = data.config
    if data.component_order is not None and data.component_order != placement.component_order:
        changes["component_order"] = data.component_order
        placement.component_order = data.component_order
    placement.updated_at = datetime.utcnow()
    placement.updated_by = data.updated_by or modified_by
    try:
        db.commit()
        db.refresh(placement)
    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Database error while updating FormPanelComponent id=%s tenant_id=%s",
            form_panel_component_id,
            tenant_id,
        )
        raise HTTPException(
            status_code=500, detail="An error occurred while updating the panel component."
        )
    if changes:
        payload = FormPanelComponentOut.model_validate(placement).model_dump(mode="json")
        FormPanelComponentProducer.send_form_panel_component_updated(
            tenant_id=tenant_id,
            form_panel_component_id=form_panel_component_id,
            form_panel_id=placement.form_panel_id,
            component_id=placement.component_id,
            changes=changes,
            payload=payload,
        )
    return placement


def delete_form_panel_component(
    db: Session, tenant_id: UUID, form_panel_component_id: UUID
) -> None:
    """Delete a FormPanelComponent record.

    After deletion an event is published to notify downstream consumers.
    """
    placement = get_form_panel_component(db, tenant_id, form_panel_component_id)
    try:
        form_panel_id = placement.form_panel_id
        component_id = placement.component_id
        db.delete(placement)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Database error while deleting FormPanelComponent id=%s tenant_id=%s",
            form_panel_component_id,
            tenant_id,
        )
        raise HTTPException(
            status_code=500, detail="An error occurred while deleting the panel component."
        )
    FormPanelComponentProducer.send_form_panel_component_deleted(
        tenant_id=tenant_id,
        form_panel_component_id=form_panel_component_id,
        form_panel_id=form_panel_id,
        component_id=component_id,
    )
    return None