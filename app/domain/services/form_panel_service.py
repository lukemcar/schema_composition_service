"""
Service functions for the FormPanel domain.

CRUD operations for FormPanel records. All operations are tenant scoped.
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

from app.domain.models import FormPanel
from app.domain.schemas.form_panel import FormPanelCreate, FormPanelUpdate, FormPanelOut
from app.messaging.producers.form_panel_producer import FormPanelProducer


logger = logging.getLogger(__name__)


def create_form_panel(
    db: Session,
    tenant_id: UUID,
    data: FormPanelCreate,
    created_by: str = "system",
) -> FormPanel:
    logger.info(
        "Creating FormPanel tenant_id=%s form_id=%s panel_key=%s",
        tenant_id,
        data.form_id,
        data.panel_key,
    )
    panel = FormPanel(
        tenant_id=tenant_id,
        form_id=data.form_id,
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
        logger.exception("Database error while creating FormPanel")
        raise HTTPException(status_code=500, detail="An error occurred while creating the panel.")
    payload = FormPanelOut.model_validate(panel).model_dump(mode="json")
    FormPanelProducer.send_form_panel_created(
        tenant_id=tenant_id,
        form_panel_id=panel.form_panel_id,
        form_id=panel.form_id,
        payload=payload,
    )
    return panel


def get_form_panel(db: Session, tenant_id: UUID, form_panel_id: UUID) -> FormPanel:
    panel = db.get(FormPanel, form_panel_id)
    if panel is None or panel.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FormPanel not found")
    return panel


def list_form_panels(
    db: Session,
    tenant_id: UUID,
    form_id: Optional[UUID] = None,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[FormPanel], int]:
    base_stmt = select(FormPanel).where(FormPanel.tenant_id == tenant_id)
    if form_id is not None:
        base_stmt = base_stmt.where(FormPanel.form_id == form_id)
    try:
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total: int = db.execute(count_stmt).scalar_one()
        stmt = base_stmt.order_by(FormPanel.panel_order.asc()).limit(limit).offset(offset)
        items = db.execute(stmt).scalars().all()
        return items, total
    except SQLAlchemyError:
        logger.exception("Database error while listing FormPanels tenant_id=%s", tenant_id)
        raise HTTPException(status_code=500, detail="An error occurred while retrieving panels.")


def update_form_panel(
    db: Session,
    tenant_id: UUID,
    form_panel_id: UUID,
    data: FormPanelUpdate,
    modified_by: str = "system",
) -> FormPanel:
    panel = get_form_panel(db, tenant_id, form_panel_id)
    changes: Dict[str, Any] = {}
    if data.form_id is not None and data.form_id != panel.form_id:
        changes["form_id"] = str(data.form_id)
        panel.form_id = data.form_id
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
            "Database error while updating FormPanel id=%s tenant_id=%s", form_panel_id, tenant_id
        )
        raise HTTPException(status_code=500, detail="An error occurred while updating the panel.")
    if changes:
        payload = FormPanelOut.model_validate(panel).model_dump(mode="json")
        FormPanelProducer.send_form_panel_updated(
            tenant_id=tenant_id,
            form_panel_id=form_panel_id,
            form_id=panel.form_id,
            changes=changes,
            payload=payload,
        )
    return panel


def delete_form_panel(db: Session, tenant_id: UUID, form_panel_id: UUID) -> None:
    panel = get_form_panel(db, tenant_id, form_panel_id)
    try:
        form_id = panel.form_id
        db.delete(panel)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Database error while deleting FormPanel id=%s tenant_id=%s", form_panel_id, tenant_id
        )
        raise HTTPException(status_code=500, detail="An error occurred while deleting the panel.")
    FormPanelProducer.send_form_panel_deleted(
        tenant_id=tenant_id,
        form_panel_id=form_panel_id,
        form_id=form_id,
    )