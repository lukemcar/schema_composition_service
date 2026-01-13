"""
Service layer functions for the ComponentPanel domain.

CRUD operations for ComponentPanel records. All operations are tenant‑scoped.
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

from app.domain.models import ComponentPanel
from app.domain.schemas.component_panel import ComponentPanelCreate, ComponentPanelUpdate, ComponentPanelOut
from app.messaging.producers.component_panel_producer import ComponentPanelProducer


logger = logging.getLogger(__name__)


def create_component_panel(
    db: Session,
    tenant_id: UUID,
    data: ComponentPanelCreate,
    created_by: str = "system",
) -> ComponentPanel:
    """Create a new ComponentPanel."""
    logger.info(
        "Creating ComponentPanel tenant_id=%s component_id=%s panel_key=%s",
        tenant_id,
        data.component_id,
        data.panel_key,
    )
    panel = ComponentPanel(
        tenant_id=tenant_id,
        component_id=data.component_id,
        parent_panel_id=data.parent_panel_id,
        panel_key=data.panel_key,
        panel_label=data.panel_label,
        ui_config=data.ui_config,
        panel_order=data.panel_order or 0,
        created_by=data.created_by or created_by,
    )
    db.add(panel)
    try:
        db.commit()
        db.refresh(panel)
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error while creating ComponentPanel")
        raise HTTPException(status_code=500, detail="An error occurred while creating the panel.")
    payload = ComponentPanelOut.model_validate(panel).model_dump(mode="json")
    ComponentPanelProducer.send_component_panel_created(
        tenant_id=tenant_id,
        component_panel_id=panel.component_panel_id,
        component_id=panel.component_id,
        payload=payload,
    )
    return panel


def get_component_panel(db: Session, tenant_id: UUID, component_panel_id: UUID) -> ComponentPanel:
    panel = db.get(ComponentPanel, component_panel_id)
    if panel is None or panel.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ComponentPanel not found")
    return panel


def list_component_panels(
    db: Session,
    tenant_id: UUID,
    component_id: Optional[UUID] = None,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[ComponentPanel], int]:
    base_stmt = select(ComponentPanel).where(ComponentPanel.tenant_id == tenant_id)
    if component_id is not None:
        base_stmt = base_stmt.where(ComponentPanel.component_id == component_id)
    try:
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total: int = db.execute(count_stmt).scalar_one()
        stmt = base_stmt.order_by(ComponentPanel.panel_order.asc()).limit(limit).offset(offset)
        items = db.execute(stmt).scalars().all()
        return items, total
    except SQLAlchemyError:
        logger.exception("Database error while listing ComponentPanels for tenant_id=%s", tenant_id)
        raise HTTPException(status_code=500, detail="An error occurred while retrieving panels.")


def update_component_panel(
    db: Session,
    tenant_id: UUID,
    component_panel_id: UUID,
    data: ComponentPanelUpdate,
    modified_by: str = "system",
) -> ComponentPanel:
    panel = get_component_panel(db, tenant_id, component_panel_id)
    changes: Dict[str, Any] = {}
    if data.component_id is not None and data.component_id != panel.component_id:
        changes["component_id"] = str(data.component_id)
        panel.component_id = data.component_id
    if data.parent_panel_id is not None and data.parent_panel_id != panel.parent_panel_id:
        changes["parent_panel_id"] = str(data.parent_panel_id)
        panel.parent_panel_id = data.parent_panel_id
    if data.panel_key is not None and data.panel_key != panel.panel_key:
        changes["panel_key"] = data.panel_key
        panel.panel_key = data.panel_key
    if data.panel_label is not None and data.panel_label != panel.panel_label:
        changes["panel_label"] = data.panel_label
        panel.panel_label = data.panel_label
    if data.ui_config is not None and data.ui_config != panel.ui_config:
        changes["ui_config"] = data.ui_config
        panel.ui_config = data.ui_config
    if data.panel_order is not None and data.panel_order != panel.panel_order:
        changes["panel_order"] = data.panel_order
        panel.panel_order = data.panel_order
    panel.updated_at = datetime.utcnow()
    panel.updated_by = data.updated_by or modified_by
    try:
        db.commit()
        db.refresh(panel)
    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Database error while updating ComponentPanel id=%s tenant_id=%s", component_panel_id, tenant_id
        )
        raise HTTPException(status_code=500, detail="An error occurred while updating the panel.")
    if changes:
        payload = ComponentPanelOut.model_validate(panel).model_dump(mode="json")
        ComponentPanelProducer.send_component_panel_updated(
            tenant_id=tenant_id,
            component_panel_id=component_panel_id,
            component_id=panel.component_id,
            changes=changes,
            payload=payload,
        )
    return panel


def delete_component_panel(db: Session, tenant_id: UUID, component_panel_id: UUID) -> None:
    panel = get_component_panel(db, tenant_id, component_panel_id)
    try:
        component_id = panel.component_id
        db.delete(panel)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Database error while deleting ComponentPanel id=%s tenant_id=%s", component_panel_id, tenant_id
        )
        raise HTTPException(status_code=500, detail="An error occurred while deleting the panel.")
    ComponentPanelProducer.send_component_panel_deleted(
        tenant_id=tenant_id,
        component_panel_id=component_panel_id,
        component_id=component_id,
    )