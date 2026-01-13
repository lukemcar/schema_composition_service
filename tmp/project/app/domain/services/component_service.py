"""
Service layer functions for the Component domain.

This module provides CRUD operations for Component records. All operations
are tenant‑scoped. After create, update or delete, an event is published
via the ComponentProducer.
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

from app.domain.models import Component
from app.domain.schemas.component import ComponentCreate, ComponentUpdate, ComponentOut
from app.messaging.producers.component_producer import ComponentProducer


logger = logging.getLogger(__name__)


def create_component(
    db: Session,
    tenant_id: UUID,
    data: ComponentCreate,
    created_by: str = "system",
) -> Component:
    """Create a new Component."""
    logger.info(
        "Creating Component tenant_id=%s key=%s version=%s",
        tenant_id,
        data.component_key,
        data.version,
    )
    component = Component(
        tenant_id=tenant_id,
        component_key=data.component_key,
        version=data.version,
        component_name=data.component_name,
        description=data.description,
        category_id=data.category_id,
        ui_config=data.ui_config,
        is_active=data.is_active if data.is_active is not None else True,
        created_by=data.created_by or created_by,
    )
    db.add(component)
    try:
        db.commit()
        db.refresh(component)
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error while creating Component")
        raise HTTPException(status_code=500, detail="An error occurred while creating the component.")
    payload = ComponentOut.model_validate(component).model_dump(mode="json")
    ComponentProducer.send_component_created(
        tenant_id=tenant_id,
        component_id=component.component_id,
        payload=payload,
    )
    return component


def get_component(db: Session, tenant_id: UUID, component_id: UUID) -> Component:
    """Retrieve a Component by id and tenant."""
    component = db.get(Component, component_id)
    if component is None or component.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Component not found")
    return component


def list_components(
    db: Session,
    tenant_id: UUID,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[Component], int]:
    """List Components for a tenant with pagination."""
    base_stmt = select(Component).where(Component.tenant_id == tenant_id)
    try:
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total: int = db.execute(count_stmt).scalar_one()
        stmt = base_stmt.order_by(Component.component_name.asc()).limit(limit).offset(offset)
        items = db.execute(stmt).scalars().all()
        return items, total
    except SQLAlchemyError:
        logger.exception("Database error while listing Components for tenant_id=%s", tenant_id)
        raise HTTPException(status_code=500, detail="An error occurred while retrieving components.")


def update_component(
    db: Session,
    tenant_id: UUID,
    component_id: UUID,
    data: ComponentUpdate,
    modified_by: str = "system",
) -> Component:
    """Update a Component record."""
    component = get_component(db, tenant_id, component_id)
    changes: Dict[str, Any] = {}
    if data.component_key is not None and data.component_key != component.component_key:
        changes["component_key"] = data.component_key
        component.component_key = data.component_key
    if data.version is not None and data.version != component.version:
        changes["version"] = data.version
        component.version = data.version
    if data.component_name is not None and data.component_name != component.component_name:
        changes["component_name"] = data.component_name
        component.component_name = data.component_name
    if data.description is not None and data.description != component.description:
        changes["description"] = data.description
        component.description = data.description
    if data.category_id is not None and data.category_id != component.category_id:
        changes["category_id"] = str(data.category_id)
        component.category_id = data.category_id
    if data.ui_config is not None and data.ui_config != component.ui_config:
        changes["ui_config"] = data.ui_config
        component.ui_config = data.ui_config
    if data.is_active is not None and data.is_active != component.is_active:
        changes["is_active"] = data.is_active
        component.is_active = data.is_active
    # Update audit fields
    component.updated_at = datetime.utcnow()
    component.updated_by = data.updated_by or modified_by
    try:
        db.commit()
        db.refresh(component)
    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Database error while updating Component id=%s tenant_id=%s", component_id, tenant_id
        )
        raise HTTPException(status_code=500, detail="An error occurred while updating the component.")
    if changes:
        payload = ComponentOut.model_validate(component).model_dump(mode="json")
        ComponentProducer.send_component_updated(
            tenant_id=tenant_id,
            component_id=component_id,
            changes=changes,
            payload=payload,
        )
    return component


def delete_component(db: Session, tenant_id: UUID, component_id: UUID) -> None:
    """Delete a Component and publish an event."""
    component = get_component(db, tenant_id, component_id)
    try:
        db.delete(component)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Database error while deleting Component id=%s tenant_id=%s", component_id, tenant_id
        )
        raise HTTPException(status_code=500, detail="An error occurred while deleting the component.")
    ComponentProducer.send_component_deleted(
        tenant_id=tenant_id,
        component_id=component_id,
    )