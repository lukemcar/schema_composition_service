"""
Service layer functions for the FieldDef domain.

This module implements the core business logic for creating,
retrieving, listing, updating and deleting FieldDef records.  All
database access is tenant‑scoped: callers must provide the tenant
identifier explicitly.  When adding new domain services follow the
patterns used here: parameterise the tenant ID, perform simple
CRUD operations using SQLAlchemy and raise appropriate HTTP exceptions
when records are not found or operations fail.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.domain.models import FieldDef
from app.domain.schemas.field_def import FieldDefCreate, FieldDefUpdate, FieldDefOut
from app.messaging.producers.field_def_producer import FieldDefProducer

logger = logging.getLogger(__name__)


def create_field_def(
    db: Session,
    tenant_id: UUID,
    data: FieldDefCreate,
    created_by: str = "system",
) -> FieldDef:
    """Create a new FieldDef for the given tenant.

    On success the new record is committed and refreshed, then a
    ``field-def.created`` event is published via RabbitMQ.  If a
    database error occurs a 500 response is raised.
    """
    logger.info(
        "Creating FieldDef for tenant_id=%s business_key=%r user=%s",
        tenant_id,
        data.field_def_business_key,
        created_by,
    )
    entity = FieldDef(
        tenant_id=tenant_id,
        field_def_business_key=data.field_def_business_key,
        field_def_version=data.field_def_version,
        name=data.name,
        description=data.description,
        field_key=data.field_key,
        label=data.label,
        category_id=data.category_id,
        data_type=data.data_type,
        element_type=data.element_type,
        validation=data.validation,
        ui_config=data.ui_config,
        is_published=data.is_published,
        published_at=data.published_at,
        is_archived=data.is_archived,
        archived_at=data.archived_at,
        source_type=data.source_type,
        source_package_key=data.source_package_key,
        source_artifact_key=data.source_artifact_key,
        source_artifact_version=data.source_artifact_version,
        source_checksum=data.source_checksum,
        installed_at=data.installed_at,
        installed_by=data.installed_by,
        created_by=data.created_by or created_by,
        updated_by=data.created_by or created_by,
    )
    db.add(entity)
    try:
        db.commit()
        db.refresh(entity)
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error while creating FieldDef")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the field definition.",
        )
    # Publish event after commit
    payload = FieldDefOut.model_validate(entity).model_dump(mode="json")
    FieldDefProducer.send_field_def_created(
        tenant_id=tenant_id,
        field_def_id=entity.field_def_id,
        payload=payload,
    )
    return entity


def get_field_def(
    db: Session,
    tenant_id: UUID,
    field_def_id: UUID,
) -> FieldDef:
    """Retrieve a single FieldDef by id and tenant.

    Raises a 404 if the record does not exist or does not belong to
    the tenant.
    """
    entity = db.get(FieldDef, field_def_id)
    if entity is None or entity.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FieldDef not found",
        )
    return entity


def list_field_defs(
    db: Session,
    tenant_id: UUID,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[FieldDef], int]:
    """List FieldDef records for a tenant with simple pagination.

    Returns a tuple of (items, total) where total is the total number
    of definitions for the tenant independent of limit/offset.
    """
    base_stmt = select(FieldDef).where(FieldDef.tenant_id == tenant_id)
    try:
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total: int = db.execute(count_stmt).scalar_one()
        stmt = base_stmt.order_by(FieldDef.created_at.desc()).limit(limit).offset(offset)
        items = db.execute(stmt).scalars().all()
        return items, total
    except SQLAlchemyError:
        logger.exception(
            "Database error while listing FieldDef records for tenant_id=%s",
            tenant_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving field definitions.",
        )


def update_field_def(
    db: Session,
    tenant_id: UUID,
    field_def_id: UUID,
    data: FieldDefUpdate,
    modified_by: str = "system",
) -> FieldDef:
    """Update a FieldDef record.

    Only the provided fields in ``data`` are modified.  After update
    the changes are recorded in a dictionary and published in a
    ``field-def.updated`` event.  A 404 is raised if the record does
    not exist or does not belong to the tenant.
    """
    entity = get_field_def(db, tenant_id, field_def_id)
    changes: Dict[str, Any] = {}

    # Update fields conditionally
    for attr in [
        "field_def_business_key",
        "field_def_version",
        "name",
        "description",
        "field_key",
        "label",
        "category_id",
        "data_type",
        "element_type",
        "validation",
        "ui_config",
        "is_published",
        "published_at",
        "is_archived",
        "archived_at",
        "source_type",
        "source_package_key",
        "source_artifact_key",
        "source_artifact_version",
        "source_checksum",
        "installed_at",
        "installed_by",
    ]:
        value = getattr(data, attr)
        if value is not None and value != getattr(entity, attr):
            changes[attr] = value
            setattr(entity, attr, value)

    # Update audit fields
    if data.updated_by:
        entity.updated_by = data.updated_by
    else:
        entity.updated_by = modified_by
    entity.updated_at = datetime.utcnow()

    try:
        db.commit()
        db.refresh(entity)
    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Database error while updating FieldDef id=%s tenant_id=%s",
            field_def_id,
            tenant_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the field definition.",
        )

    if changes:
        payload = FieldDefOut.model_validate(entity).model_dump(mode="json")
        FieldDefProducer.send_field_def_updated(
            tenant_id=tenant_id,
            field_def_id=field_def_id,
            changes=changes,
            payload=payload,
        )
    else:
        logger.info("FieldDef has no changes")
    return entity


def delete_field_def(
    db: Session,
    tenant_id: UUID,
    field_def_id: UUID,
) -> None:
    """Delete a FieldDef record and publish a deletion event."""
    entity = get_field_def(db, tenant_id, field_def_id)
    try:
        db.delete(entity)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Database error while deleting FieldDef id=%s tenant_id=%s",
            field_def_id,
            tenant_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the field definition.",
        )
    # Publish deletion event.  Include a deletion timestamp as a string
    deleted_dt = datetime.utcnow().isoformat()
    FieldDefProducer.send_field_def_deleted(
        tenant_id=tenant_id,
        field_def_id=field_def_id,
        deleted_dt=deleted_dt,
    )
    return None
