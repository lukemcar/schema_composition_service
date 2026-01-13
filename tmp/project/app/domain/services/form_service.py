"""
Service functions for the Form domain.

Provides CRUD operations for Forms, ensuring tenant scoping and
publishing events via FormProducer.
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

from app.domain.models import Form
from app.domain.schemas.form import FormCreate, FormUpdate, FormOut
from app.messaging.producers.form_producer import FormProducer


logger = logging.getLogger(__name__)


def create_form(db: Session, tenant_id: UUID, data: FormCreate, created_by: str = "system") -> Form:
    logger.info(
        "Creating Form tenant_id=%s key=%s version=%s",
        tenant_id,
        data.form_key,
        data.version,
    )
    form = Form(
        tenant_id=tenant_id,
        form_key=data.form_key,
        version=data.version,
        form_name=data.form_name,
        description=data.description,
        category_id=data.category_id,
        ui_config=data.ui_config,
        is_active=data.is_active if data.is_active is not None else True,
        is_published=data.is_published if data.is_published is not None else False,
        created_by=data.created_by or created_by,
    )
    db.add(form)
    try:
        db.commit()
        db.refresh(form)
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error while creating Form")
        raise HTTPException(status_code=500, detail="An error occurred while creating the form.")
    payload = FormOut.model_validate(form).model_dump(mode="json")
    FormProducer.send_form_created(
        tenant_id=tenant_id,
        form_id=form.form_id,
        payload=payload,
    )
    return form


def get_form(db: Session, tenant_id: UUID, form_id: UUID) -> Form:
    form = db.get(Form, form_id)
    if form is None or form.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Form not found")
    return form


def list_forms(
    db: Session,
    tenant_id: UUID,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[Form], int]:
    base_stmt = select(Form).where(Form.tenant_id == tenant_id)
    try:
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total: int = db.execute(count_stmt).scalar_one()
        stmt = base_stmt.order_by(Form.form_name.asc()).limit(limit).offset(offset)
        items = db.execute(stmt).scalars().all()
        return items, total
    except SQLAlchemyError:
        logger.exception("Database error while listing Forms tenant_id=%s", tenant_id)
        raise HTTPException(status_code=500, detail="An error occurred while retrieving forms.")


def update_form(
    db: Session,
    tenant_id: UUID,
    form_id: UUID,
    data: FormUpdate,
    modified_by: str = "system",
) -> Form:
    form = get_form(db, tenant_id, form_id)
    changes: Dict[str, Any] = {}
    if data.form_key is not None and data.form_key != form.form_key:
        changes["form_key"] = data.form_key
        form.form_key = data.form_key
    if data.version is not None and data.version != form.version:
        changes["version"] = data.version
        form.version = data.version
    if data.form_name is not None and data.form_name != form.form_name:
        changes["form_name"] = data.form_name
        form.form_name = data.form_name
    if data.description is not None and data.description != form.description:
        changes["description"] = data.description
        form.description = data.description
    if data.category_id is not None and data.category_id != form.category_id:
        changes["category_id"] = str(data.category_id)
        form.category_id = data.category_id
    if data.ui_config is not None and data.ui_config != form.ui_config:
        changes["ui_config"] = data.ui_config
        form.ui_config = data.ui_config
    if data.is_active is not None and data.is_active != form.is_active:
        changes["is_active"] = data.is_active
        form.is_active = data.is_active
    if data.is_published is not None and data.is_published != form.is_published:
        changes["is_published"] = data.is_published
        form.is_published = data.is_published
    form.updated_at = datetime.utcnow()
    form.updated_by = data.updated_by or modified_by
    try:
        db.commit()
        db.refresh(form)
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error while updating Form id=%s tenant_id=%s", form_id, tenant_id)
        raise HTTPException(status_code=500, detail="An error occurred while updating the form.")
    if changes:
        payload = FormOut.model_validate(form).model_dump(mode="json")
        FormProducer.send_form_updated(
            tenant_id=tenant_id,
            form_id=form_id,
            changes=changes,
            payload=payload,
        )
    return form


def delete_form(db: Session, tenant_id: UUID, form_id: UUID) -> None:
    form = get_form(db, tenant_id, form_id)
    try:
        db.delete(form)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error while deleting Form id=%s tenant_id=%s", form_id, tenant_id)
        raise HTTPException(status_code=500, detail="An error occurred while deleting the form.")
    FormProducer.send_form_deleted(
        tenant_id=tenant_id,
        form_id=form_id,
    )