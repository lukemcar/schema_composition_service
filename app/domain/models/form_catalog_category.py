"""
SQLAlchemy model for the ``form_catalog_category`` table.

This model represents a tenant‑scoped category used to organise
reusable form elements (fields and components) in builder UIs.  Each
category has a stable key and a human‑readable name that are both
unique within a tenant.  Categories can be activated or deactivated
via the ``is_active`` flag.  Audit columns track when records were
created or updated and by whom.

The underlying database table and constraints are defined in the
Liquibase migration ``002_create_form_catalog_category.sql``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class FormCatalogCategory(Base):
    """Tenant‑scoped form catalogue category.

    Fields:
      * ``form_catalog_category_id`` – primary key (UUID)
      * ``tenant_id`` – identifier of the tenant owning this category
      * ``category_key`` – stable identifier used for import/export and marketplace alignment
      * ``category_name`` – human‑readable label shown in builder UI
      * ``description`` – optional description
      * ``is_active`` – flag controlling availability in the UI
      * ``created_at`` / ``updated_at`` – timestamps managed by the DB
      * ``created_by`` / ``updated_by`` – audit trail for who performed the action
    """

    __tablename__ = "form_catalog_category"
    
    __table_args__ = (
        {"schema": "schema_composition"},
    )

    # Map primary key to the ``id`` column defined in the DDL.  Use a
    # domain‑specific attribute name for clarity in Python code.
    form_catalog_category_id: Mapped[UUID] = mapped_column(
        "id", PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )

    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False
    )

    category_key: Mapped[str] = mapped_column(
        String(200), nullable=False
    )

    category_name: Mapped[str] = mapped_column(
        String(50), nullable=False
    )

    description: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    created_by: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )

    updated_by: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )

    def __repr__(self) -> str:
        return (
            f"<FormCatalogCategory id={self.form_catalog_category_id} tenant_id={self.tenant_id} "
            f"key={self.category_key} name={self.category_name}>"
        )


__all__ = ["FormCatalogCategory"]