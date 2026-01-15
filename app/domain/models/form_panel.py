"""
SQLAlchemy model for the ``form_panel`` table.

This model mirrors the DDL for the ``schema_composition.form_panel`` table.  A
form panel represents a logical grouping within a specific form definition.
Panels are identified by a stable ``panel_key`` within a form and are
tenant‑scoped.  They support optional UI configuration but do not nest (no
parent_panel_id here; nesting is handled via components and component panels).

Constraints enforce tenant safety and prevent blank keys or labels.  Indexes
support common access patterns such as listing panels for a form and
recency queries.
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


class FormPanel(Base):  # type: ignore[type-arg]
    """Panel within a specific form definition.

    Panels group fields and embedded components on a form.  They are
    identified by a stable ``panel_key`` that is unique within each form.
    """

    __tablename__ = "form_panel"
    __table_args__ = (
        # Unique identity per tenant (supports tenant‑safe FKs from child tables).
        UniqueConstraint("tenant_id", "id", name="ux_form_panel_tenant_id"),
        # Prevent blank/whitespace panel_key.
        CheckConstraint(
            "length(btrim(panel_key)) > 0",
            name="ck_form_panel_key_nonblank",
        ),
        # Prevent blank/whitespace panel_label if provided.
        CheckConstraint(
            "panel_label IS NULL OR length(btrim(panel_label)) > 0",
            name="ck_form_panel_label_nonblank",
        ),
        # Stable identity within a form.
        UniqueConstraint(
            "tenant_id", "form_id", "panel_key",
            name="uq_form_panel_tenant_form_panel_key",
        ),
        # Tenant‑safe FK forcing form_id to belong to same tenant.
        ForeignKeyConstraint(
            ["tenant_id", "form_id"],
            ["form.tenant_id", "form.id"],
            name="fk_form_panel_form_tenant",
            ondelete="CASCADE",
        ),
        # Indexes
        Index("ix_form_panel_tenant_form", "tenant_id", "form_id"),
        Index(
            "ix_form_panel_tenant_form_updated_at",
            "tenant_id",
            "form_id",
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
    # Tenant boundary and owning form
    # ---------------------------------------------------------------------
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    form_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    # ---------------------------------------------------------------------
    # Stable identity and metadata
    # ---------------------------------------------------------------------
    panel_key: Mapped[str] = mapped_column(String(200), nullable=False)
    panel_label: Mapped[Optional[str]] = mapped_column(String(200))
    ui_config: Mapped[Optional[dict]] = mapped_column(JSONB)

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
            f"<FormPanel id={self.id} tenant_id={self.tenant_id} form_id={self.form_id} panel_key={self.panel_key}>"
        )


__all__ = ["FormPanel"]