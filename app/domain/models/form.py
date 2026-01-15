"""
SQLAlchemy model for the ``form`` table.

This model is aligned with the Liquibase DDL in
``migrations/liquibase/sql/001_init_schema.sql``.  A form defines a
tenant‑scoped, versioned form definition used for collecting submissions.  It
supports lifecycle management (publish/archiving) and provenance metadata.

Core concepts:
  - ``id`` is the immutable primary key (UUID).
  - ``form_business_key`` + ``form_version`` provide a stable business
    identity unique within a tenant.
  - ``name`` and ``description`` are used in builder/admin UIs.
  - Lifecycle flags and timestamps enforce consistency (published/archived).
  - Source metadata describes where the form originated (marketplace,
    provider, tenant, etc.) and is optional.

All columns, constraints, and indexes are copied verbatim from the DDL.
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
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.domain.models.enums import ArtifactSourceType


class Form(Base):  # type: ignore[type-arg]
    """Tenant‑scoped versioned form definition.

    Represents an actual form definition used for collecting submissions.  This
    model mirrors the structure of ``schema_composition.form``.
    """

    __tablename__ = "form"
    __table_args__ = (
        # ------------------------------------------------------------------
        # Uniqueness / invariants
        # ------------------------------------------------------------------
        UniqueConstraint("tenant_id", "id", name="ux_form_id_tenant"),
        CheckConstraint("form_version >= 1", name="ck_form_version_positive"),
        CheckConstraint("length(btrim(form_business_key)) > 0", name="ck_form_business_key_nonblank"),
        CheckConstraint("length(btrim(name)) > 0", name="ck_form_name_nonblank"),
        UniqueConstraint(
            "tenant_id", "form_business_key", "form_version",
            name="uq_form_tenant_business_key_version",
        ),
        CheckConstraint(
            "(is_published = TRUE  AND published_at IS NOT NULL) OR (is_published = FALSE AND published_at IS NULL)",
            name="ck_form_published_at_consistency",
        ),
        CheckConstraint(
            "(is_archived = TRUE  AND archived_at IS NOT NULL) OR (is_archived = FALSE AND archived_at IS NULL)",
            name="ck_form_archived_at_consistency",
        ),
        CheckConstraint(
            "source_checksum IS NULL OR source_checksum ~ '^[0-9a-f]{64}$'",
            name="ck_form_source_checksum_format",
        ),
        # ------------------------------------------------------------------
        # Indexes
        # ------------------------------------------------------------------
        Index("ux_form_tenant_name", "tenant_id", "name", unique=True),
        Index("ix_form_tenant_catalog_state", "tenant_id", "is_published", "is_archived"),
        Index(
            "ix_form_tenant_name_lower", "tenant_id", text("lower(name)"),
        ),
        Index("ix_form_tenant_source_type", "tenant_id", "source_type"),
        Index(
            "ix_form_tenant_source_keys",
            "tenant_id",
            "source_package_key",
            "source_artifact_key",
            "source_artifact_version",
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
    # Versioned business identity
    # ---------------------------------------------------------------------
    form_business_key: Mapped[str] = mapped_column(String(400), nullable=False)
    form_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # ---------------------------------------------------------------------
    # Human‑facing metadata
    # ---------------------------------------------------------------------
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))

    # ---------------------------------------------------------------------
    # Lifecycle / availability
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
            f"<Form id={self.id} tenant_id={self.tenant_id} "
            f"business_key={self.form_business_key}:{self.form_version}>"
        )


__all__ = ["Form"]