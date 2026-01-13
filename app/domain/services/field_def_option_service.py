"""
Service layer functions for the FieldDefOption domain.

This module implements CRUD operations for FieldDefOption records.  All
database access is tenant‑scoped: callers must provide the tenant identifier.
After successful create, update or delete operations, events are published
via the FieldDefOptionProducer.
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

from app.domain.models import FieldDefOption
from app.domain.schemas.field_def_option import (
    FieldDefOptionCreate,
    FieldDefOptionUpdate,
    FieldDefOptionOut,
)
from app.messaging.producers.field_def_option_producer import FieldDefOptionProducer


logger = logging.getLogger(__name__)


def create_field_def_option(
    db: Session,
    tenant_id: UUID,
    field_def_id: UUID,
    data: FieldDefOptionCreate,
    created_by: str = "system",
) -> FieldDefOption:
    """Create a new FieldDefOption for the given field definition."""
    logger.info(
        "Creating FieldDefOption for tenant_id=%s field_def_id=%s option_key=%r",
        tenant_id,
        field_def_id,
        data.option_key,
    )
    option = FieldDefOption(
        tenant_id=tenant_id,
        field_def_id=field_def_id,
        option_key=data.option_key,
        option_label=data.option_label,
        option_order=data.option_order or 0,
        created_by=data.created_by or created_by,
    )
    db.add(option)
    try:
        db.commit()
        db.refresh(option)
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error while creating FieldDefOption")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the option.",
        )

    payload = FieldDefOptionOut.model_validate(option).model_dump(mode="json")
    FieldDefOptionProducer.send_field_def_option_created(
        tenant_id=tenant_id,
        field_def_option_id=option.field_def_option_id,
        field_def_id=field_def_id,
        payload=payload,
    )
    return option


def get_field_def_option(
    db: Session,
    tenant_id: UUID,
    field_def_option_id: UUID,
) -> FieldDefOption:
    """Retrieve a single FieldDefOption by id and tenant."""
    option = db.get(FieldDefOption, field_def_option_id)
    if option is None or option.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FieldDefOption not found",
        )
    return option


def list_field_def_options(
    db: Session,
    tenant_id: UUID,
    field_def_id: Optional[UUID] = None,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[FieldDefOption], int]:
    """List FieldDefOption records for a tenant (optionally filtered by field_def_id)."""
    base_stmt = select(FieldDefOption).where(FieldDefOption.tenant_id == tenant_id)
    if field_def_id is not None:
        base_stmt = base_stmt.where(FieldDefOption.field_def_id == field_def_id)
    try:
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total: int = db.execute(count_stmt).scalar_one()
        stmt = base_stmt.order_by(FieldDefOption.option_order.asc()).limit(limit).offset(offset)
        items = db.execute(stmt).scalars().all()
        return items, total
    except SQLAlchemyError:
        logger.exception(
            "Database error while listing FieldDefOption records for tenant_id=%s", tenant_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving options.",
        )


def update_field_def_option(
    db: Session,
    tenant_id: UUID,
    field_def_option_id: UUID,
    data: FieldDefOptionUpdate,
    modified_by: str = "system",
) -> FieldDefOption:
    """Update a FieldDefOption record."""
    option = get_field_def_option(db, tenant_id, field_def_option_id)
    changes: Dict[str, Any] = {}
    if data.option_key is not None and data.option_key != option.option_key:
        changes["option_key"] = data.option_key
        option.option_key = data.option_key
    if data.option_label is not None and data.option_label != option.option_label:
        changes["option_label"] = data.option_label
        option.option_label = data.option_label
    if data.option_order is not None and data.option_order != option.option_order:
        changes["option_order"] = data.option_order
        option.option_order = data.option_order
    if data.updated_by:
        option.created_by = data.updated_by  # No separate updated_by field defined
    else:
        option.created_by = modified_by
    option.created_at = datetime.utcnow()  # Without updated_at field, reuse created_at
    try:
        db.commit()
        db.refresh(option)
    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Database error while updating FieldDefOption id=%s tenant_id=%s",
            field_def_option_id,
            tenant_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the option.",
        )
    if changes:
        payload = FieldDefOptionOut.model_validate(option).model_dump(mode="json")
        FieldDefOptionProducer.send_field_def_option_updated(
            tenant_id=tenant_id,
            field_def_option_id=field_def_option_id,
            field_def_id=option.field_def_id,
            changes=changes,
            payload=payload,
        )
    else:
        logger.info("FieldDefOption has no changes")
    return option


def delete_field_def_option(
    db: Session,
    tenant_id: UUID,
    field_def_option_id: UUID,
) -> None:
    """Delete a FieldDefOption record and publish a deletion event."""
    option = get_field_def_option(db, tenant_id, field_def_option_id)
    try:
        field_def_id = option.field_def_id
        db.delete(option)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Database error while deleting FieldDefOption id=%s tenant_id=%s",
            field_def_option_id,
            tenant_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the option.",
        )
    FieldDefOptionProducer.send_field_def_option_deleted(
        tenant_id=tenant_id,
        field_def_option_id=field_def_option_id,
        field_def_id=field_def_id,
    )