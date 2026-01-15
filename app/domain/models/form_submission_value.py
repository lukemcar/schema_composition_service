"""
SQLAlchemy model for the ``form_submission_value`` table.

This model mirrors the DDL for ``schema_composition.form_submission_value``
exactly.  It stores captured values for each field instance within a form
submission.  Each row identifies its origin via a fully qualified path
(``field_path``) and either a direct placement reference or a component
placement reference.  A value may be ``NULL`` (e.g., optional fields) or
contain structured JSON data.  Tenant safety is enforced via composite
foreign keys, and numerous check constraints ensure correct path semantics
and JSON schema compliance.

Do not modify this model without updating the corresponding Liquibase
migration.  Liquibase remains the source of truth for the database
schema.
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
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class FormSubmissionValue(Base):  # type: ignore[type-arg]
    """Captured values for a specific field instance within a submission.

    Each row corresponds to one field instance captured during a form
    submission.  The instance is uniquely identified by ``field_path``
    within the submission, and must originate from exactly one placement
    path: either a direct ``form_panel_field`` or a component path
    (``form_panel_component`` + ``component_panel_field``).  A rich set
    of constraints enforces path exclusivity, non‑blank formatting, and
    JSON schema compliance for the ``value`` column.  Composite foreign
    keys ensure tenant isolation and referential integrity across the
    submission, field definition, and placement tables.
    """

    __tablename__ = "form_submission_value"
    __table_args__ = (
        # ------------------------------------------------------------------
        # Check constraints
        # ------------------------------------------------------------------
        # The captured value must either be NULL or match the defined JSON schema.
        CheckConstraint(
            '''
            value IS NULL
            OR public.jsonb_matches_schema(
                $${
                    "$schema": "http://json-schema.org/draft-07/schema#",
                    "title": "DynoCRM Form Submission Value",
                    "type": "object",
                    "additionalProperties": false,
                    "required": ["data_type", "value"],
                    "properties": {
                        "data_type": {
                            "type": "string",
                            "enum": [
                                "TEXT",
                                "NUMBER",
                                "BOOLEAN",
                                "DATE",
                                "DATETIME",
                                "SINGLESELECT",
                                "MULTISELECT"
                            ]
                        },
                        "value": {}
                    },
                    "allOf": [
                        {
                            "if": { "properties": { "data_type": { "const": "TEXT" } } },
                            "then": { "properties": { "value": { "type": "string" } } }
                        },
                        {
                            "if": { "properties": { "data_type": { "const": "DATE" } } },
                            "then": { "properties": { "value": { "type": "string" } } }
                        },
                        {
                            "if": { "properties": { "data_type": { "const": "DATETIME" } } },
                            "then": { "properties": { "value": { "type": "string" } } }
                        },
                        {
                            "if": { "properties": { "data_type": { "const": "SINGLESELECT" } } },
                            "then": { "properties": { "value": { "type": "string", "minLength": 1, "maxLength": 200 } } }
                        },
                        {
                            "if": { "properties": { "data_type": { "const": "MULTISELECT" } } },
                            "then": {
                                "properties": {
                                    "value": {
                                        "type": "array",
                                        "items": { "type": "string", "minLength": 1, "maxLength": 200 },
                                        "maxItems": 1000
                                    }
                                }
                            }
                        },
                        {
                            "if": { "properties": { "data_type": { "const": "NUMBER" } } },
                            "then": { "properties": { "value": { "type": "number" } } }
                        },
                        {
                            "if": { "properties": { "data_type": { "const": "BOOLEAN" } } },
                            "then": { "properties": { "value": { "type": "boolean" } } }
                        }
                    ]
                }$$::json,
                value
            )
            ''',
            name="ck_form_submission_value_schema",
        ),
        # Prevent empty or whitespace‑only paths.
        CheckConstraint(
            "length(btrim(field_path)) > 0",
            name="ck_form_submission_value_field_path_nonblank",
        ),
        # Enforce a basic dot‑separated key format (allows hyphens and underscores).
        CheckConstraint(
            "field_path ~ '^[A-Za-z0-9_\\-]+(\\.[A-Za-z0-9_\\-]+)+$'",
            name="ck_form_submission_value_field_path_format",
        ),
        # Exactly one placement path must be set (direct vs component).
        CheckConstraint(
            "(form_panel_field_id IS NOT NULL AND form_panel_component_id IS NULL AND component_panel_field_id IS NULL)"
            " OR (form_panel_field_id IS NULL AND form_panel_component_id IS NOT NULL AND component_panel_field_id IS NOT NULL)",
            name="ck_form_submission_value_path_exclusive",
        ),
        # ------------------------------------------------------------------
        # Uniqueness constraints
        # ------------------------------------------------------------------
        UniqueConstraint(
            "tenant_id",
            "form_submission_id",
            "field_path",
            name="uq_form_submission_value_submission_field_path",
            deferrable=True,
            initially="DEFERRED",
        ),
        UniqueConstraint(
            "tenant_id",
            "form_submission_id",
            "form_panel_field_id",
            name="uq_form_submission_value_direct",
            deferrable=True,
            initially="DEFERRED",
        ),
        UniqueConstraint(
            "tenant_id",
            "form_submission_id",
            "form_panel_component_id",
            "component_panel_field_id",
            name="uq_form_submission_value_component",
            deferrable=True,
            initially="DEFERRED",
        ),
        # ------------------------------------------------------------------
        # Foreign keys (tenant‑safe)
        # ------------------------------------------------------------------
        ForeignKeyConstraint(
            ["tenant_id", "form_submission_id"],
            ["form_submission.tenant_id", "form_submission.id"],
            name="fk_form_submission_value_submission_tenant",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "field_def_id"],
            ["field_def.tenant_id", "field_def.id"],
            name="fk_form_submission_value_field_def_tenant",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "form_panel_field_id"],
            ["form_panel_field.tenant_id", "form_panel_field.id"],
            name="fk_form_submission_value_form_panel_field_tenant",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "form_panel_component_id"],
            ["form_panel_component.tenant_id", "form_panel_component.id"],
            name="fk_form_submission_value_form_panel_component_tenant",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "component_panel_field_id"],
            ["component_panel_field.tenant_id", "component_panel_field.id"],
            name="fk_form_submission_value_component_panel_field_tenant",
            ondelete="RESTRICT",
        ),
        # ------------------------------------------------------------------
        # Indexes
        # ------------------------------------------------------------------
        Index("ix_form_submission_value_tenant_id", "tenant_id"),
        Index(
            "ix_form_submission_value_submission",
            "tenant_id",
            "form_submission_id",
        ),
        Index(
            "ix_form_submission_value_submission_field_path",
            "tenant_id",
            "form_submission_id",
            "field_path",
        ),
        Index(
            "ix_form_submission_value_field_def",
            "tenant_id",
            "field_def_id",
        ),
        Index(
            "ix_form_submission_value_panel_field",
            "tenant_id",
            "form_panel_field_id",
            postgresql_where=text("form_panel_field_id IS NOT NULL"),
        ),
        Index(
            "ix_form_submission_value_component_field",
            "tenant_id",
            "form_panel_component_id",
            "component_panel_field_id",
            postgresql_where=text("form_panel_component_id IS NOT NULL"),
        ),
        Index(
            "ix_form_submission_value_value_gin",
            "value",
            postgresql_using="gin",
        ),
        Index(
            "ix_form_submission_value_tenant_submission_updated_at",
            "tenant_id",
            "form_submission_id",
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
    # Tenant boundary and owning submission
    # ---------------------------------------------------------------------
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    form_submission_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    field_def_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    # ---------------------------------------------------------------------
    # Fully qualified field instance path
    # ---------------------------------------------------------------------
    field_path: Mapped[str] = mapped_column(String(800), nullable=False)

    # ---------------------------------------------------------------------
    # Placement references (exactly one must be non‑null)
    # ---------------------------------------------------------------------
    form_panel_field_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))
    form_panel_component_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))
    component_panel_field_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))

    # ---------------------------------------------------------------------
    # Captured value and search surface
    # ---------------------------------------------------------------------
    value: Mapped[Optional[dict]] = mapped_column(JSONB)
    value_search_text: Mapped[Optional[str]] = mapped_column(Text)

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
            f"<FormSubmissionValue id={self.id} tenant_id={self.tenant_id} "
            f"submission_id={self.form_submission_id} path={self.field_path}>"
        )


__all__ = ["FormSubmissionValue"]