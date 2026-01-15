"""
SQLAlchemy model for the ``component_panel`` table.

This model mirrors the Liquibase DDL defined in
``migrations/liquibase/sql/001_init_schema.sql``.  A component panel is a
hierarchical grouping inside a reusable component.  Panels can nest via
``parent_panel_id`` and are strictly scoped to a single component and tenant.

Key invariants enforced via constraints:
  - Tenant boundary via ``tenant_id``.
  - Parent/child integrity enforced by a self‑referencing composite
    foreign key on (tenant_id, component_id, parent_panel_id).
  - ``panel_key`` is a stable key, non‑blank, and unique per component.
  - ``panel_label`` (if provided) cannot be blank.
  - A panel cannot parent itself.

Index definitions mirror those in the DDL to support common access patterns
like fetching children for a parent or listing panels for a component ordered
by ``updated_at``.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class ComponentPanel(Base):  # type: ignore[type-arg]
    """Hierarchical panel within a reusable component.

    Each panel belongs to exactly one component and tenant.  Panels may
    reference a parent panel (forming a tree) via ``parent_panel_id``.
    All invariants and foreign keys are defined to be tenant‑safe.
    """

    __tablename__ = "component_panel"
    __table_args__ = (
        # Unique identity per tenant (supports tenant‑safe FKs from child tables).
        UniqueConstraint("tenant_id", "id", name="ux_component_panel_id_tenant"),
        # Unique identity per component (supports self‑referencing FK below).
        UniqueConstraint("tenant_id", "component_id", "id", name="ux_component_panel_tenant_component_id"),
        # Self‑referencing composite FK to enforce parent hierarchy within same tenant and component.
        ForeignKeyConstraint(
            ["tenant_id", "component_id", "parent_panel_id"],
            ["component_panel.tenant_id", "component_panel.component_id", "component_panel.id"],
            name="fk_component_panel_parent_panel_tenant_component",
            ondelete="CASCADE",
        ),
        # Prevent blank/whitespace panel_key.
        CheckConstraint(
            "length(btrim(panel_key)) > 0",
            name="ck_component_panel_key_nonblank",
        ),
        # Prevent blank/whitespace panel_label if provided.
        CheckConstraint(
            "panel_label IS NULL OR length(btrim(panel_label)) > 0",
            name="ck_component_panel_label_nonblank",
        ),
        # Prevent self‑parenting.
        CheckConstraint(
            "parent_panel_id IS NULL OR parent_panel_id <> id",
            name="ck_component_panel_no_self_parent",
        ),
        # Stable identity within a component: panel_key unique per component.
        UniqueConstraint(
            "tenant_id", "component_id", "panel_key",
            name="uq_component_panel_tenant_component_panel_key",
        ),
        # Tenant‑safe FK forcing component_id to belong to same tenant.
        ForeignKeyConstraint(
            ["tenant_id", "component_id"],
            ["component.tenant_id", "component.id"],
            name="fk_component_panel_component_tenant",
            ondelete="CASCADE",
        ),
        # Indexes
        Index(
            "ix_component_panel_parent",
            "tenant_id",
            "component_id",
            "parent_panel_id",
        ),
        Index(
            "ix_component_panel_tenant_component_updated_at",
            "tenant_id",
            "component_id",
            "updated_at",
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
    # Tenant boundary and owning component
    # ---------------------------------------------------------------------
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    component_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    parent_panel_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))

    # ---------------------------------------------------------------------
    # Stable identity and metadata
    # ---------------------------------------------------------------------
    panel_key: Mapped[str] = mapped_column(String(200), nullable=False)
    panel_label: Mapped[Optional[str]] = mapped_column(String(200))
    ui_config: Mapped[Optional[dict]] = mapped_column(JSONB)
    panel_actions: Mapped[Optional[dict]] = mapped_column(JSONB)

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
            f"<ComponentPanel id={self.id} tenant_id={self.tenant_id} component_id={self.component_id} "
            f"panel_key={self.panel_key}>"
        )


__all__ = ["ComponentPanel"]