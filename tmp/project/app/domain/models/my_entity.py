"""
SQLAlchemy model for the ``my_entity`` table.

This model demonstrates a simple, tenant‑scoped entity with audit
fields.  To add a new domain model copy this file and adjust the
``__tablename__`` and column definitions accordingly.  All models
should inherit from ``app.domain.models.base.Base`` so that they
participate in the shared naming convention and metadata.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class MyEntity(Base):
    """Tenant‑scoped entity definition.

    Fields:
      * ``my_entity_id`` – primary key (UUID)
      * ``tenant_id`` – identifier of the tenant owning this entity
      * ``name`` – a human‑friendly name for the entity
      * ``data`` – arbitrary JSON payload associated with the entity
      * ``created_at`` / ``updated_at`` – timestamps managed by the DB
      * ``created_by`` / ``updated_by`` – audit trail for who performed the action

    When extending this model consider indexing frequently queried
    columns (e.g. ``tenant_id``) in your Liquibase migration.  Avoid
    embedding business logic in the model; put that in the service layer.
    """

    __tablename__ = "my_entity"

    my_entity_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    created_by: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    updated_by: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<MyEntity id={self.my_entity_id} tenant_id={self.tenant_id} "
            f"name={self.name}>"
        )