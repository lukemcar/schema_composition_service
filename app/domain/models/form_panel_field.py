"""
SQLAlchemy model for the ``form_panel_field`` table.

This model corresponds exactly to the DDL for
``schema_composition.form_panel_field``.  It defines non‑reusable field
instances placed directly onto a form panel.  Each record stores an
imprinted ``field_config`` snapshot (with enforced JSON schema), optional
UI overrides, ordering information, and provenance hashes.  Tenant safety
is enforced via composite foreign keys.
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
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class FormPanelField(Base):  # type: ignore[type-arg]
    """Non‑reusable field placement on a form panel.

    Each row represents one field instance placed directly on a form panel.  The
    effective field definition is stored in ``field_config`` and may diverge
    from the source catalog ``field_def``.  The JSON schema of ``field_config``
    is enforced via a check constraint using ``public.jsonb_matches_schema``.
    """

    __tablename__ = "form_panel_field"
    __table_args__ = (
        # ------------------------------------------------------------------
        # Uniqueness / invariants
        # ------------------------------------------------------------------
        UniqueConstraint("tenant_id", "id", name="ux_form_panel_field_tenant_id"),
        CheckConstraint(
            "field_order IS NULL OR field_order >= 0",
            name="ck_form_panel_field_order_non_negative",
        ),
        UniqueConstraint(
            "tenant_id", "panel_id", "field_def_id",
            name="uq_form_panel_field_panel_field_def",
        ),
        UniqueConstraint(
            "tenant_id", "panel_id", "field_order",
            name="uq_form_panel_field_panel_order",
        ),
        CheckConstraint(
            "field_config_hash IS NULL OR field_config_hash ~ '^[0-9a-f]{64}$'",
            name="ck_form_panel_field_field_config_hash_format",
        ),
        CheckConstraint(
            "source_field_def_hash IS NULL OR source_field_def_hash ~ '^[0-9a-f]{64}$'",
            name="ck_form_panel_field_source_field_def_hash_format",
        ),
        # Enforce field_config JSON schema via jsonb_matches_schema.
        CheckConstraint(
            '''
            public.jsonb_matches_schema(
                $${
                  "$schema": "http://json-schema.org/draft-07/schema#",
                  "title": "DynoCRM Form Panel Field Config",
                  "type": "object",
                  "additionalProperties": false,
                  "required": ["schema_version", "field"],
                  "properties": {
                    "schema_version": { "type": "integer", "minimum": 1 },

                    "field": {
                      "type": "object",
                      "additionalProperties": false,
                      "required": ["field_key", "label", "element_type"],
                      "properties": {
                        "field_def_business_key": { "type": "string", "minLength": 1, "maxLength": 400 },
                        "field_def_version": { "type": "integer", "minimum": 1 },

                        "name": { "type": "string", "minLength": 1, "maxLength": 100 },
                        "description": { "type": ["string", "null"], "maxLength": 1000 },

                        "field_key": { "type": "string", "minLength": 1, "maxLength": 100 },
                        "label": { "type": "string", "minLength": 1, "maxLength": 255 },

                        "category_id": { "type": ["string", "null"], "pattern": "^[0-9a-fA-F-]{36}$" },

                        "data_type": {
                          "type": ["string", "null"],
                          "enum": ["TEXT","NUMBER","BOOLEAN","DATE","DATETIME","SINGLESELECT","MULTISELECT", null]
                        },

                        "element_type": {
                          "type": "string",
                          "enum": ["TEXT","TEXTAREA","DATE","DATETIME","SELECT","MULTISELECT","ACTION"]
                        },

                        "validation": { "type": ["object", "null"] },
                        "ui_config": { "type": ["object", "null"] }
                      }
                    },

                    "options": {
                      "type": ["array", "null"],
                      "items": {
                        "type": "object",
                        "additionalProperties": false,
                        "required": ["option_key", "option_label", "option_order"],
                        "properties": {
                          "option_key": { "type": "string", "minLength": 1, "maxLength": 200 },
                          "option_label": { "type": "string", "minLength": 1, "maxLength": 400 },
                          "option_order": { "type": "integer", "minimum": 0 }
                        }
                      }
                    }
                  }
                }$$::json,
                field_config
            )
            ''',
            name="ck_form_panel_field_field_config_schema",
        ),
        # ------------------------------------------------------------------
        # Foreign keys (tenant‑safe)
        # ------------------------------------------------------------------
        ForeignKeyConstraint(
            ["tenant_id", "panel_id"],
            ["form_panel.tenant_id", "form_panel.id"],
            name="fk_form_panel_field_panel_tenant",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "field_def_id"],
            ["field_def.tenant_id", "field_def.id"],
            name="fk_form_panel_field_field_def_tenant",
            ondelete="RESTRICT",
        ),
        # ------------------------------------------------------------------
        # Indexes
        # ------------------------------------------------------------------
        Index("ix_form_panel_field_field_def", "tenant_id", "field_def_id"),
        Index(
            "ix_form_panel_field_tenant_panel_updated_at",
            "tenant_id",
            "panel_id",
            "updated_at",
        ),
        Index(
            "ix_form_panel_field_hashes",
            "tenant_id",
            "field_config_hash",
            "source_field_def_hash",
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
    # Tenant boundary and owning form panel
    # ---------------------------------------------------------------------
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    panel_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    field_def_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    # ---------------------------------------------------------------------
    # Ordering and UI overrides
    # ---------------------------------------------------------------------
    field_order: Mapped[Optional[int]] = mapped_column(Integer)
    ui_config: Mapped[Optional[dict]] = mapped_column(JSONB)

    # ---------------------------------------------------------------------
    # Imprinted field definition snapshot
    # ---------------------------------------------------------------------
    field_config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    field_config_hash: Mapped[Optional[str]] = mapped_column(String(64))
    source_field_def_hash: Mapped[Optional[str]] = mapped_column(String(64))
    last_imprinted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

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
            f"<FormPanelField id={self.id} tenant_id={self.tenant_id} panel_id={self.panel_id} field_def_id={self.field_def_id}>"
        )


__all__ = ["FormPanelField"]