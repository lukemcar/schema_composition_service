"""
SQLAlchemy model definition for the FieldDefOption domain.

This model represents an option belonging to a FieldDef.  Each option is
tenant‑scoped and scoped to a specific field definition.  The combination
of ``tenant_id``, ``field_def_id`` and ``option_key`` is unique to prevent
duplicate options for the same field.

The table stores a UUID primary key for convenience rather than using the
composite primary key from the original schema.  Additional columns include
a display label, order within the options list, creation timestamp and
optional actor metadata.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import String, Integer, DateTime, Index, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID as pgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models.base import Base


class FieldDefOption(Base):  # type: ignore[type-arg]
    """Option value belonging to a field definition.

    Each option is scoped to a tenant and a specific FieldDef.  The
    combination of ``tenant_id``, ``field_def_id`` and ``option_key`` must be
    unique.  The ``option_order`` controls display ordering within the list
    of options.
    """

    __tablename__ = "field_def_option"
    __table_args__ = (
        UniqueConstraint("tenant_id", "field_def_id", "option_key", name="uq_field_def_option_tenant_field_key"),
        UniqueConstraint("tenant_id", "field_def_id", "option_order", name="uq_field_def_option_tenant_field_order"),
        Index("ix_field_def_option_tenant_field_order", "tenant_id", "field_def_id", "option_order"),
        Index("ix_field_def_option_label", "tenant_id", text("lower(option_label)")),
        {"schema": "schema_composition"},
    )

    field_def_option_id: Mapped[UUID] = mapped_column(
        "id", pgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[UUID] = mapped_column(pgUUID(as_uuid=True), nullable=False, index=True)
    field_def_id: Mapped[UUID] = mapped_column(pgUUID(as_uuid=True), nullable=False, index=True)

    option_key: Mapped[str] = mapped_column(String(200), nullable=False)
    option_label: Mapped[str] = mapped_column(String(400), nullable=False)
    option_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<FieldDefOption tenant_id={self.tenant_id} field_def_id={self.field_def_id} "
            f"option_key={self.option_key}>"
        )