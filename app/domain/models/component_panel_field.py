"""
SQLAlchemy model for the ComponentPanelField domain.

This table defines the placement of a reusable field definition (field_def) onto
a specific component panel.

High-level intent:

- This is the "composition" layer: panel + field_def -> placed field instance.
- Each row represents one placed field on one panel.
- Ordering is scoped to the panel via field_order.
- ui_config is a per-placement override/augmentation (field_def also has ui_config).
- field_config is an imprinted snapshot of the effective field definition + options
  at time of placement. This is the editable copy that can diverge from the catalog.
- Hash columns support fast diff checks without deep JSON comparisons.

IMPORTANT:
- This ORM must match the DDL exactly. Any mismatch (missing columns, wrong names,
  wrong nullability) can break model import, migrations, and tests.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

from .base import Base


class ComponentPanelField(Base):
    """
    Database model for schema_composition.component_panel_field.

    Notes on naming:
    - DDL uses `id` as the primary key column. Keep the ORM attribute name aligned
      with the DB column name to avoid confusion and mismatch.
    - DDL uses `panel_id` (not `component_panel_id`). The ORM must use `panel_id`
      or explicitly map to the right column name.
    """

    __tablename__ = "component_panel_field"

    # __table_args__ contains constraints and indexes that must reference REAL columns.
    # If any referenced column name does not exist, SQLAlchemy will fail at import time
    # (during declarative mapping) and pytest will error during collection.
    __table_args__ = (
        # ---------------------------------------------------------------------
        # Uniqueness / invariants
        # ---------------------------------------------------------------------

        # Tenant-safe identity uniqueness. This is somewhat redundant given `id` is a PK,
        # but it is explicitly in your DDL, so we mirror it.
        UniqueConstraint("tenant_id", "id", name="ux_component_panel_field_tenant_id"),

        # Prevent duplicate placement of the same field_def on the same panel.
        UniqueConstraint(
            "tenant_id",
            "panel_id",
            "field_def_id",
            name="uq_component_panel_field_panel_field_def",
        ),

        # Optional: enforce unique ordering positions per panel when field_order is used.
        # Allows multiple NULL values (Postgres unique semantics allow multiple NULLs).
        UniqueConstraint(
            "tenant_id",
            "panel_id",
            "field_order",
            name="uq_component_panel_field_panel_order",
        ),

        # Defensive: field_order must be >= 0 when provided.
        CheckConstraint(
            "field_order IS NULL OR field_order >= 0",
            name="ck_component_panel_field_order_non_negative",
        ),

        # Hash formatting checks (sha256 hex) when present.
        CheckConstraint(
            "field_config_hash IS NULL OR field_config_hash ~ '^[0-9a-f]{64}$'",
            name="ck_component_panel_field_field_config_hash_format",
        ),
        CheckConstraint(
            "source_field_def_hash IS NULL OR source_field_def_hash ~ '^[0-9a-f]{64}$'",
            name="ck_component_panel_field_source_field_def_hash_format",
        ),

        # ---------------------------------------------------------------------
        # Indexes (mirrors your CREATE INDEX statements)
        # ---------------------------------------------------------------------

        # Fast joins to field_def (rendering / reset provenance).
        Index("ix_component_panel_field_field_def", "tenant_id", "field_def_id"),

        # Optional: accelerate recency queries / maintenance.
        Index(
            "ix_component_panel_field_tenant_panel_updated_at",
            "tenant_id",
            "panel_id",
            "updated_at",
        ),

        # Optional: accelerate hash comparisons for drift / override detection.
        Index(
            "ix_component_panel_field_hashes",
            "tenant_id",
            "field_config_hash",
            "source_field_def_hash",
        ),

        # NOTE: GIN indexes for JSONB (ui_config/field_config) are typically created
        # outside the ORM via migrations, because SQLAlchemy's Index(..., postgresql_using="gin")
        # is supported, but many teams prefer DDL/migrations as the source of truth.
        #
        # If you *do* want ORM-declared GIN indexes, uncomment these:
        #
        # Index(
        #     "ix_component_panel_field_ui_config_gin",
        #     "ui_config",
        #     postgresql_using="gin",
        # ),
        # Index(
        #     "ix_component_panel_field_field_config_gin",
        #     "field_config",
        #     postgresql_using="gin",
        # ),

        # Schema specification
        {"schema": "schema_composition"},
    )

    # -------------------------------------------------------------------------
    # Primary identity
    # -------------------------------------------------------------------------

    id: uuid.UUID = Column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        default=uuid.uuid4,
        comment="Primary key for the placed field instance (UUID).",
    )

    # -------------------------------------------------------------------------
    # Tenant boundary and owning panel
    # -------------------------------------------------------------------------

    tenant_id: uuid.UUID = Column(
        UUID(as_uuid=True),
        nullable=False,
        comment="Tenant boundary. All rows are scoped to a tenant_id.",
    )

    panel_id: uuid.UUID = Column(
        UUID(as_uuid=True),
        nullable=False,
        comment="Owning component panel this placed field belongs to.",
    )

    field_def_id: uuid.UUID = Column(
        UUID(as_uuid=True),
        nullable=False,
        comment=(
            "Catalog field definition used as provenance/reset source. "
            "The editable effective definition is stored in field_config."
        ),
    )

    # -------------------------------------------------------------------------
    # Ordering and UI overrides
    # -------------------------------------------------------------------------

    field_order: int = Column(
        Integer,
        nullable=True,  # DDL allows NULL
        comment=(
            "Display/tab order within the panel. NULL means 'unspecified' "
            "(service/UI may apply default ordering). Must be >= 0 when present."
        ),
    )

    ui_config: dict = Column(
        JSONB,
        nullable=True,
        comment=(
            "Per-placement UI configuration overrides/augmentations. "
            "Base UI config lives on field_def; this is applied in this panel context."
        ),
    )

    # -------------------------------------------------------------------------
    # Imprinted field definition snapshot
    # -------------------------------------------------------------------------

    field_config: dict = Column(
        JSONB,
        nullable=False,
        comment=(
            "Imprinted JSONB snapshot representing the effective field definition "
            "and options for this placement. This is the editable copy that may "
            "diverge from the catalog field_def."
        ),
    )

    field_config_hash: str = Column(
        String(64),
        nullable=True,
        comment=(
            "Hash of current field_config JSONB (typically sha256 hex, 64 chars). "
            "Used for fast diff checks without deep JSON comparison."
        ),
    )

    source_field_def_hash: str = Column(
        String(64),
        nullable=True,
        comment=(
            "Hash of canonical source snapshot from field_def + field_def_option used "
            "to imprint field_config (typically sha256 hex, 64 chars). Used to detect "
            "catalog drift since imprint."
        ),
    )

    last_imprinted_at: datetime = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when field_config was last imprinted from the catalog source.",
    )

    # -------------------------------------------------------------------------
    # Audit columns
    # -------------------------------------------------------------------------

    created_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="Creation timestamp (UTC). DDL uses NOW() at the DB layer.",
    )

    updated_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="Last update timestamp (UTC). DDL uses NOW() at the DB layer.",
    )

    created_by: str = Column(
        String(100),
        nullable=True,
        comment="Optional actor identifier for create (user/service).",
    )

    updated_by: str = Column(
        String(100),
        nullable=True,
        comment="Optional actor identifier for last update (user/service).",
    )

    def __repr__(self) -> str:  # pragma: no cover
        # Keep repr short and stable; avoid dumping JSON fields.
        return (
            f"<ComponentPanelField id={self.id} tenant_id={self.tenant_id} "
            f"panel_id={self.panel_id} field_def_id={self.field_def_id} "
            f"field_order={self.field_order}>"
        )
