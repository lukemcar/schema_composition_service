"""
SQLAlchemy model for the ``component`` table.

This model is fully aligned with the Liquibase DDL defined in
``migrations/liquibase/sql/001_init_schema.sql``.  It represents a
reusable, tenant-scoped catalog component that can be embedded into
forms.  All columns, constraints, and indexes mirror the DDL exactly.

Key concepts:
  - ``id`` is the immutable primary key (UUID).
  - ``component_business_key`` and ``component_version`` provide a
    versioned business identity unique within a tenant.
  - ``component_key`` is a stable tenant-scoped key used by APIs and
    automations.
  - Lifecycle flags (``is_published``, ``is_archived``) control
    visibility in catalog UIs.  Timestamps must align with the flags.
  - All data is scoped to a tenant via ``tenant_id`` and tenant-safe
    composite foreign keys.

Do not modify the structure of this model without updating the
Liquibase migration accordingly.  Liquibase remains the source of
truth for the database schema.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    Index,
    Integer,
    String,
    UniqueConstraint,
    ForeignKeyConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.domain.models.enums import ArtifactSourceType


class Component(Base):  # type: ignore[type-arg]
    """Tenant‑scoped reusable catalog component.

    This table stores reusable UI components that can be embedded in forms.
    It mirrors the ``schema_composition.component`` DDL definition exactly.
    """

    __tablename__ = "component"
    __table_args__ = (
        # ------------------------------------------------------------------
        # Uniqueness / invariants
        # ------------------------------------------------------------------
        UniqueConstraint("tenant_id", "id", name="ux_component_id_tenant"),
        CheckConstraint("component_version >= 1", name="ck_component_version_positive"),
        CheckConstraint("length(btrim(component_business_key)) > 0", name="ck_component_business_key_nonblank"),
        CheckConstraint("length(btrim(component_key)) > 0", name="ck_component_key_nonblank"),
        CheckConstraint("length(btrim(name)) > 0", name="ck_component_name_nonblank"),
        # Tenant‑safe FK to builder palette category.  Requires a unique/PK on
        # form_catalog_category(tenant_id, id).  NULL category_id is allowed.
        ForeignKeyConstraint(
            ["tenant_id", "category_id"],
            ["form_catalog_category.tenant_id", "form_catalog_category.id"],
            name="fk_component_category_tenant",
            ondelete="SET NULL",
        ),
        # Publishing timestamp must align with the published flag.
        CheckConstraint(
            "(is_published = TRUE  AND published_at IS NOT NULL) OR (is_published = FALSE AND published_at IS NULL)",
            name="ck_component_published_at_consistency",
        ),
        # Archiving timestamp must align with the archived flag.
        CheckConstraint(
            "(is_archived = TRUE  AND archived_at IS NOT NULL) OR (is_archived = FALSE AND archived_at IS NULL)",
            name="ck_component_archived_at_consistency",
        ),
        # Versioned catalog identity within tenant.
        UniqueConstraint(
            "tenant_id", "component_business_key", "component_version",
            name="uq_component_tenant_business_key_version",
        ),
        # Stable runtime identity within tenant.
        UniqueConstraint(
            "tenant_id", "component_key", "component_version",
            name="uq_component_tenant_component_key_version",
        ),
        # Check SHA-256 checksum format when provided.
        CheckConstraint(
            "source_checksum IS NULL OR source_checksum ~ '^[0-9a-f]{64}$'",
            name="ck_component_source_checksum_format",
        ),
        # ------------------------------------------------------------------
        # Indexes
        # ------------------------------------------------------------------
        Index("ix_component_tenant_source_type", "tenant_id", "source_type"),
        Index(
            "ix_component_tenant_source_keys",
            "tenant_id",
            "source_package_key",
            "source_artifact_key",
            "source_artifact_version",
        ),
        Index("ix_component_tenant_category", "tenant_id", "category_id"),
        Index("ix_component_tenant_name", "tenant_id", "name"),
        Index("ix_component_tenant_catalog_state", "tenant_id", "is_published", "is_archived"),
        Index(
            "ix_component_tenant_category_name",
            "tenant_id",
            "category_id",
            "name",
            postgresql_where=text("category_id IS NOT NULL"),
        ),
        # Schema specification
        {"schema": "schema_composition"},
    )

    # ---------------------------------------------------------------------
    # Primary identity
    # ---------------------------------------------------------------------
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    # ---------------------------------------------------------------------
    # Tenant boundary
    # ---------------------------------------------------------------------
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    # ---------------------------------------------------------------------
    # Catalog identity (versioning)
    # ---------------------------------------------------------------------
    component_business_key: Mapped[str] = mapped_column(String(400), nullable=False)
    component_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # ---------------------------------------------------------------------
    # Human‑facing metadata (admin/catalog UI)
    # ---------------------------------------------------------------------
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000))

    # ---------------------------------------------------------------------
    # Stable runtime identifier (tenant‑scoped)
    # ---------------------------------------------------------------------
    component_key: Mapped[str] = mapped_column(String(100), nullable=False)
    component_label: Mapped[Optional[str]] = mapped_column(String(255))
    category_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))

    # ---------------------------------------------------------------------
    # UI and behavior configuration
    # ---------------------------------------------------------------------
    ui_config: Mapped[Optional[dict]] = mapped_column(JSONB)

    # ---------------------------------------------------------------------
    # Lifecycle / catalog availability
    # ---------------------------------------------------------------------
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # ---------------------------------------------------------------------
    # Source/provenance metadata
    # ---------------------------------------------------------------------
    source_type: Mapped[Optional[ArtifactSourceType]] = mapped_column(
        Enum(ArtifactSourceType, name="artifact_source_type")
    )
    source_package_key: Mapped[Optional[str]] = mapped_column(String(400))
    source_artifact_key: Mapped[Optional[str]] = mapped_column(String(400))
    source_artifact_version: Mapped[Optional[str]] = mapped_column(String(100))
    source_checksum: Mapped[Optional[str]] = mapped_column(String(64))
    installed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    installed_by: Mapped[Optional[str]] = mapped_column(String(100))

    # ---------------------------------------------------------------------
    # Audit columns
    # ---------------------------------------------------------------------
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(100))
    updated_by: Mapped[Optional[str]] = mapped_column(String(100))

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Component id={self.id} tenant_id={self.tenant_id} "
            f"key={self.component_key} version={self.component_version}>"
        )


__all__ = ["Component"]