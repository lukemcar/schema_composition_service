"""
Service functions for the ComponentPanelField domain.

Handles CRUD operations for field placements on component panels.
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

from app.domain.models import ComponentPanelField
from app.domain.schemas.component_panel_field import (
    ComponentPanelFieldCreate,
    ComponentPanelFieldUpdate,
    ComponentPanelFieldOut,
)
from app.messaging.producers.component_panel_field_producer import ComponentPanelFieldProducer


logger = logging.getLogger(__name__)


def create_component_panel_field(
    db: Session,
    tenant_id: UUID,
    data: ComponentPanelFieldCreate,
    created_by: str = "system",
) -> ComponentPanelField:
    logger.info(
        "Creating ComponentPanelField tenant_id=%s panel_id=%s field_def_id=%s",
        tenant_id,
        data.component_panel_id,
        data.field_def_id,
    )
    record = ComponentPanelField(
        tenant_id=tenant_id,
        component_panel_id=data.component_panel_id,
        field_def_id=data.field_def_id,
        overrides=data.overrides,
        field_order=data.field_order or 0,
        is_required=data.is_required if data.is_required is not None else False,
        created_by=data.created_by or created_by,
    )
    db.add(record)
    try:
        db.commit()
        db.refresh(record)
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error while creating ComponentPanelField")
        raise HTTPException(status_code=500, detail="An error occurred while creating the field placement.")
    payload = ComponentPanelFieldOut.model_validate(record).model_dump(mode="json")
    ComponentPanelFieldProducer.send_component_panel_field_created(
        tenant_id=tenant_id,
        component_panel_field_id=record.component_panel_field_id,
        component_panel_id=record.component_panel_id,
        field_def_id=record.field_def_id,
        payload=payload,
    )
    return record


def get_component_panel_field(
    db: Session,
    tenant_id: UUID,
    component_panel_field_id: UUID,
) -> ComponentPanelField:
    item = db.get(ComponentPanelField, component_panel_field_id)
    if item is None or item.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ComponentPanelField not found")
    return item


def list_component_panel_fields(
    db: Session,
    tenant_id: UUID,
    component_panel_id: Optional[UUID] = None,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[ComponentPanelField], int]:
    base_stmt = select(ComponentPanelField).where(ComponentPanelField.tenant_id == tenant_id)
    if component_panel_id is not None:
        base_stmt = base_stmt.where(ComponentPanelField.component_panel_id == component_panel_id)
    try:
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total: int = db.execute(count_stmt).scalar_one()
        stmt = base_stmt.order_by(ComponentPanelField.field_order.asc()).limit(limit).offset(offset)
        items = db.execute(stmt).scalars().all()
        return items, total
    except SQLAlchemyError:
        logger.exception("Database error while listing ComponentPanelFields tenant_id=%s", tenant_id)
        raise HTTPException(status_code=500, detail="An error occurred while retrieving panel fields.")


def update_component_panel_field(
    db: Session,
    tenant_id: UUID,
    component_panel_field_id: UUID,
    data: ComponentPanelFieldUpdate,
    modified_by: str = "system",
) -> ComponentPanelField:
    item = get_component_panel_field(db, tenant_id, component_panel_field_id)
    changes: Dict[str, Any] = {}
    if data.component_panel_id is not None and data.component_panel_id != item.component_panel_id:
        changes["component_panel_id"] = str(data.component_panel_id)
        item.component_panel_id = data.component_panel_id
    if data.field_def_id is not None and data.field_def_id != item.field_def_id:
        changes["field_def_id"] = str(data.field_def_id)
        item.field_def_id = data.field_def_id
    if data.overrides is not None and data.overrides != item.overrides:
        changes["overrides"] = data.overrides
        item.overrides = data.overrides
    if data.field_order is not None and data.field_order != item.field_order:
        changes["field_order"] = data.field_order
        item.field_order = data.field_order
    if data.is_required is not None and data.is_required != item.is_required:
        changes["is_required"] = data.is_required
        item.is_required = data.is_required
    item.updated_at = datetime.utcnow()
    item.updated_by = data.updated_by or modified_by
    try:
        db.commit()
        db.refresh(item)
    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Database error while updating ComponentPanelField id=%s tenant_id=%s",
            component_panel_field_id,
            tenant_id,
        )
        raise HTTPException(status_code=500, detail="An error occurred while updating the panel field.")
    if changes:
        payload = ComponentPanelFieldOut.model_validate(item).model_dump(mode="json")
        ComponentPanelFieldProducer.send_component_panel_field_updated(
            tenant_id=tenant_id,
            component_panel_field_id=component_panel_field_id,
            component_panel_id=item.component_panel_id,
            field_def_id=item.field_def_id,
            changes=changes,
            payload=payload,
        )
    return item


def delete_component_panel_field(
    db: Session, tenant_id: UUID, component_panel_field_id: UUID
) -> None:
    item = get_component_panel_field(db, tenant_id, component_panel_field_id)
    try:
        component_panel_id = item.component_panel_id
        field_def_id = item.field_def_id
        db.delete(item)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Database error while deleting ComponentPanelField id=%s tenant_id=%s",
            component_panel_field_id,
            tenant_id,
        )
        raise HTTPException(status_code=500, detail="An error occurred while deleting the panel field.")
    ComponentPanelFieldProducer.send_component_panel_field_deleted(
        tenant_id=tenant_id,
        component_panel_field_id=component_panel_field_id,
        component_panel_id=component_panel_id,
        field_def_id=field_def_id,
    )