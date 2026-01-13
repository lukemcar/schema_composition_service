"""
Service layer functions for the FormCatalogCategory domain.

This module implements the core business logic for creating,
retrieving, listing, updating and deleting FormCatalogCategory
records.  All database access is tenant-scoped: callers must
provide the tenant identifier explicitly.  When adding new domain
services follow the patterns used here and in ``my_entity_service``:
parameterise the tenant ID, perform simple query/update operations
using SQLAlchemy and raise appropriate HTTP exceptions when records
are not found or operations fail.  Events are published via the
producer after successful commits.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.domain.models import FormCatalogCategory
from app.domain.schemas.form_catalog_category import (
    FormCatalogCategoryCreate,
    FormCatalogCategoryUpdate,
    FormCatalogCategoryOut,
)
from app.messaging.producers.form_catalog_category_producer import (
    FormCatalogCategoryProducer,
)


logger = logging.getLogger(__name__)


def create_form_catalog_category(
    db: Session,
    tenant_id: UUID,
    data: FormCatalogCategoryCreate,
    created_by: str = "system",
) -> FormCatalogCategory:
    """Create a new FormCatalogCategory for the given tenant.

    On success the new record is committed and refreshed, then a
    ``form-catalog-category.created`` event is published via
    RabbitMQ.  If a database error occurs a 500 response is raised.
    """
    logger.info(
        "Creating FormCatalogCategory for tenant_id=%s key=%r name=%r user=%s",
        tenant_id,
        data.category_key,
        data.category_name,
        created_by,
    )
    category = FormCatalogCategory(
        tenant_id=tenant_id,
        category_key=data.category_key,
        category_name=data.category_name,
        description=data.description,
        is_active=data.is_active if data.is_active is not None else True,
        created_by=data.created_by or created_by,
        updated_by=data.created_by or created_by,
    )
    db.add(category)
    try:
        db.commit()
        db.refresh(category)
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error while creating FormCatalogCategory")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the category.",
        )
    # Publish event after commit
    payload = FormCatalogCategoryOut.model_validate(category).model_dump(mode="json")
    FormCatalogCategoryProducer.send_form_catalog_category_created(
        tenant_id=tenant_id,
        form_catalog_category_id=category.form_catalog_category_id,
        payload=payload,
    )
    return category


def get_form_catalog_category(
    db: Session,
    tenant_id: UUID,
    form_catalog_category_id: UUID,
) -> FormCatalogCategory:
    """Retrieve a single FormCatalogCategory by id and tenant.

    Raises a 404 if the category does not exist or does not belong to
    the tenant.
    """
    category = db.get(FormCatalogCategory, form_catalog_category_id)
    if category is None or category.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FormCatalogCategory not found",
        )
    return category


def list_form_catalog_categories(
    db: Session,
    tenant_id: UUID,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[FormCatalogCategory], int]:
    """List FormCatalogCategory records for a tenant with pagination.

    Returns a tuple of (items, total) where total is the total number
    of categories for the tenant independent of limit/offset.
    """
    base_stmt = select(FormCatalogCategory).where(FormCatalogCategory.tenant_id == tenant_id)
    try:
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total: int = db.execute(count_stmt).scalar_one()
        stmt = base_stmt.order_by(FormCatalogCategory.created_at.desc()).limit(limit).offset(offset)
        items = db.execute(stmt).scalars().all()
        return items, total
    except SQLAlchemyError:
        logger.exception(
            "Database error while listing FormCatalogCategory records for tenant_id=%s",
            tenant_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving categories.",
        )


def update_form_catalog_category(
    db: Session,
    tenant_id: UUID,
    form_catalog_category_id: UUID,
    data: FormCatalogCategoryUpdate,
    modified_by: str = "system",
) -> FormCatalogCategory:
    """Update a FormCatalogCategory record with provided fields.

    Only the provided fields in ``data`` are modified.  After update
    the changes are recorded in a dictionary and published in a
    ``form-catalog-category.updated`` event.  A 404 is raised if
    the record does not exist or does not belong to the tenant.
    """
    category = get_form_catalog_category(db, tenant_id, form_catalog_category_id)
    changes: Dict[str, any] = {}
    if data.category_key is not None and data.category_key != category.category_key:
        changes["category_key"] = data.category_key
        category.category_key = data.category_key
    if data.category_name is not None and data.category_name != category.category_name:
        changes["category_name"] = data.category_name
        category.category_name = data.category_name
    if data.description is not None and data.description != category.description:
        changes["description"] = data.description
        category.description = data.description
    if data.is_active is not None and data.is_active != category.is_active:
        changes["is_active"] = data.is_active
        category.is_active = data.is_active
    # Audit user
    if data.updated_by:
        category.updated_by = data.updated_by
    else:
        category.updated_by = modified_by
    category.updated_at = datetime.utcnow()
    try:
        db.commit()
        db.refresh(category)
    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Database error while updating FormCatalogCategory id=%s tenant_id=%s",
            form_catalog_category_id,
            tenant_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the category.",
        )
    if changes:
        payload = FormCatalogCategoryOut.model_validate(category).model_dump(mode="json")
        FormCatalogCategoryProducer.send_form_catalog_category_updated(
            tenant_id=tenant_id,
            form_catalog_category_id=form_catalog_category_id,
            changes=changes,
            payload=payload,
        )
    else:
        logger.info("FormCatalogCategory has no changes")
    return category


def delete_form_catalog_category(
    db: Session,
    tenant_id: UUID,
    form_catalog_category_id: UUID,
) -> None:
    """Delete a FormCatalogCategory record and publish a deletion event."""
    category = get_form_catalog_category(db, tenant_id, form_catalog_category_id)
    try:
        db.delete(category)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Database error while deleting FormCatalogCategory id=%s tenant_id=%s",
            form_catalog_category_id,
            tenant_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the category.",
        )
    # Publish deletion event after commit
    deleted_dt = datetime.utcnow().isoformat()
    FormCatalogCategoryProducer.send_form_catalog_category_deleted(
        tenant_id=tenant_id,
        form_catalog_category_id=form_catalog_category_id,
        deleted_dt=deleted_dt,
    )
    return None


__all__ = [
    "create_form_catalog_category",
    "get_form_catalog_category",
    "list_form_catalog_categories",
    "update_form_catalog_category",
    "delete_form_catalog_category",
]