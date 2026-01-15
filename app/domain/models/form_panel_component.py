"""
SQLAlchemy model for the ``form_panel_component`` table.

This model corresponds to the DDL for
``schema_composition.form_panel_component``.  It places a reusable component
onto a specific form panel, supporting per‑panel ordering, per‑placement
UI configuration overrides, and nested override patches for customizing
embedded catalog components.  Tenant safety is enforced via composite
foreign keys.

The ``nested_overrides`` JSONB column stores PATCH-style override
instructions.  A check constraint ensures that when provided, the
document adheres to the Nested Overrides JSON schema using
``public.jsonb_matches_schema``.
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


class FormPanelComponent(Base):  # type: ignore[type-arg]
    """Reusable component placement on a form panel.

    Each row represents one instance of a catalog ``component`` placed directly
    on a form panel.  Supports ordering, UI overrides, and nested override
    patches to customize embedded components, panels, and fields without
    modifying catalog definitions.
    """

    __tablename__ = "form_panel_component"
    __table_args__ = (
        # Unique identity per tenant (supports tenant‑safe FKs from child tables).
        UniqueConstraint("tenant_id", "id", name="ux_form_panel_component_tenant_id"),
        # Ordering must be non‑negative when provided.
        CheckConstraint(
            "component_order IS NULL OR component_order >= 0",
            name="ck_form_panel_component_order_non_negative",
        ),
        # Prevent duplicate placement of the same component on the same panel.
        UniqueConstraint(
            "tenant_id", "panel_id", "component_id",
            name="uq_form_panel_component_panel_component",
        ),
        # Enforce unique ordering positions per panel when component_order is used.
        UniqueConstraint(
            "tenant_id", "panel_id", "component_order",
            name="uq_form_panel_component_panel_order",
        ),
        # Enforce nested_overrides JSON schema when present.
        CheckConstraint(
            '''
            nested_overrides IS NULL
            OR public.jsonb_matches_schema(
                $${
                  "$schema": "http://json-schema.org/draft-07/schema#",
                  "title": "DynoCRM Nested Overrides",
                  "type": "object",
                  "additionalProperties": false,
                  "required": ["schema_version", "overrides"],
                  "properties": {
                    "schema_version": { "type": "integer", "minimum": 1 },
                    "overrides": {
                      "type": "array",
                      "items": { "$ref": "#/definitions/override_entry" }
                    }
                  },
                  "definitions": {
                    "override_entry": {
                      "type": "object",
                      "additionalProperties": false,
                      "required": ["selector"],
                      "properties": {
                        "selector": {
                          "type": "string",
                          "minLength": 2,
                          "maxLength": 800,
                          "description": "Dot-separated path. If it starts with '.', it is relative to the current embedded component context; otherwise absolute from the form root.",
                          "pattern": "^(\\.|[A-Za-z0-9_\\-]+)(\\.[A-Za-z0-9_\\-]+)+$"
                        },
                        "field_config": { "$ref": "#/definitions/field_config_patch" },
                        "panel_config": { "$ref": "#/definitions/panel_config_patch" }
                      },
                      "anyOf": [
                        { "required": ["field_config"] },
                        { "required": ["panel_config"] }
                      ]
                    },
                    "field_config_patch": {
                      "type": "object",
                      "additionalProperties": false,
                      "properties": {
                        "field": { "$ref": "#/definitions/field_patch" },
                        "options": { "$ref": "#/definitions/options_patch" }
                      },
                      "minProperties": 1,
                      "description": "PATCH object merged into the target field_config."
                    },
                    "field_patch": {
                      "type": "object",
                      "additionalProperties": true,
                      "description": "Partial patch of the field definition portion. Permissive for forward compatibility.",
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
                    "options_patch": {
                      "type": "array",
                      "description": "Full replacement of the option list within the field_config (still PATCH semantics at the override entry level).",
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
                    },
                    "panel_config_patch": {
                      "type": "object",
                      "additionalProperties": false,
                      "properties": {
                        "panel_label": { "type": ["string", "null"], "maxLength": 200 },
                        "ui_config": { "type": ["object", "null"] },
                        "panel_actions": { "type": ["object", "null"] }
                      },
                      "minProperties": 1,
                      "description": "PATCH object merged into the target panel config."
                    }
                  }
                }$$::json,
                nested_overrides
            )
            ''',
            name="ck_form_panel_nested_overrides_schema",
        ),
        # ------------------------------------------------------------------
        # Foreign keys (tenant‑safe)
        # ------------------------------------------------------------------
        # Basic FK to panel ID (non‑composite) used by some queries.
        ForeignKeyConstraint(
            ["panel_id"],
            ["form_panel.id"],
            name="fk_form_panel_component_panel",
            ondelete="CASCADE",
        ),
        # Composite tenant‑safe FK to panel.
        ForeignKeyConstraint(
            ["tenant_id", "panel_id"],
            ["form_panel.tenant_id", "form_panel.id"],
            name="fk_form_panel_component_panel_tenant",
            ondelete="CASCADE",
        ),
        # Basic FK to component ID (non‑composite).
        ForeignKeyConstraint(
            ["component_id"],
            ["component.id"],
            name="fk_form_panel_component_component",
            ondelete="RESTRICT",
        ),
        # Composite tenant‑safe FK to component.
        ForeignKeyConstraint(
            ["tenant_id", "component_id"],
            ["component.tenant_id", "component.id"],
            name="fk_form_panel_component_component_tenant",
            ondelete="RESTRICT",
        ),
        # ------------------------------------------------------------------
        # Indexes
        # ------------------------------------------------------------------
        Index("ix_form_panel_component_tenant_id", "tenant_id"),
        Index(
            "ix_form_panel_component_panel_order",
            "tenant_id",
            "panel_id",
            "component_order",
        ),
        Index(
            "ix_form_panel_component_component",
            "tenant_id",
            "component_id",
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
    # Tenant boundary and owning form panel / component
    # ---------------------------------------------------------------------
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    panel_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    component_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    # ---------------------------------------------------------------------
    # Ordering and UI overrides
    # ---------------------------------------------------------------------
    component_order: Mapped[Optional[int]] = mapped_column(Integer)
    ui_config: Mapped[Optional[dict]] = mapped_column(JSONB)
    nested_overrides: Mapped[Optional[dict]] = mapped_column(JSONB)

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
            f"<FormPanelComponent id={self.id} tenant_id={self.tenant_id} panel_id={self.panel_id} component_id={self.component_id}>"
        )


__all__ = ["FormPanelComponent"]