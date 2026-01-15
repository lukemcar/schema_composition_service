from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    String,
    Integer,
    Boolean,
    DateTime,
    Index,
    UniqueConstraint,
    CheckConstraint,
    ForeignKeyConstraint,
    JSON,
    Enum,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as pgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base
from app.domain.models.enums import FieldDataType, FieldElementType, ArtifactSourceType


class FieldDef(Base):  # type: ignore[type-arg]
    """Tenant-scoped reusable field definition (catalog artifact)."""

    __tablename__ = "field_def"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="ux_field_def_id_tenant"),
        UniqueConstraint("tenant_id", "field_def_business_key", "field_def_version", name="uq_field_def_tenant_business_key_version"),
        ForeignKeyConstraint(
            ["tenant_id", "category_id"],
            ["form_catalog_category.tenant_id", "form_catalog_category.id"],
            name="fk_field_def_category_tenant",
            ondelete="SET NULL",
        ),
        CheckConstraint("length(btrim(field_def_business_key)) > 0", name="ck_field_def_business_key_nonblank"),
        CheckConstraint("field_def_version >= 1", name="ck_field_def_version_positive"),
        CheckConstraint("length(btrim(field_key)) > 0", name="chk_field_def_field_key_not_blank"),
        CheckConstraint("length(btrim(label)) > 0", name="chk_field_def_label_not_blank"),
        CheckConstraint(
            "(element_type = 'ACTION' AND data_type IS NULL) OR (element_type <> 'ACTION' AND data_type IS NOT NULL)",
            name="chk_field_def_action_requires_no_data_type"
        ),
        CheckConstraint(
            "(element_type = 'SELECT' AND data_type = 'SINGLESELECT') OR "
            "(element_type = 'MULTISELECT' AND data_type = 'MULTISELECT') OR "
            "(element_type NOT IN ('SELECT', 'MULTISELECT'))",
            name="chk_field_def_select_data_type_alignment"
        ),
        CheckConstraint("source_checksum IS NULL OR source_checksum ~ '^[0-9a-f]{64}$'", name="ck_field_def_source_checksum_format"),
        Index("ix_field_def_tenant_id", "tenant_id"),
        # Added indexes from Liquibase DDL to ensure full coverage and tenant-safe filtering
        Index("ix_field_def_tenant_field_key", "tenant_id", "field_key"),
        Index(
            "ix_field_def_tenant_category",
            "tenant_id",
            "category_id",
            postgresql_where=text("category_id IS NOT NULL"),
        ),
        Index("ix_field_def_tenant_element_type", "tenant_id", "element_type"),
        Index(
            "ix_field_def_tenant_data_type",
            "tenant_id",
            "data_type",
            postgresql_where=text("data_type IS NOT NULL"),
        ),
        # Expression indexes for case-insensitive label filtering
        Index(
            "ix_field_def_tenant_label",
            "tenant_id",
            text("lower(label)"),
        ),
        Index(
            "ix_field_def_tenant_category_label",
            "tenant_id",
            "category_id",
            text("lower(label)"),
            postgresql_where=text("category_id IS NOT NULL"),
        ),
        Index("ix_field_def_tenant_source_type", "tenant_id", "source_type"),
        Index(
            "ix_field_def_tenant_source_keys",
            "tenant_id",
            "source_package_key",
            "source_artifact_key",
            "source_artifact_version",
        ),
        {"schema": "schema_composition"},
    )

    id: Mapped[UUID] = mapped_column(pgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[UUID] = mapped_column(pgUUID(as_uuid=True), nullable=False)

    field_def_business_key: Mapped[str] = mapped_column(String(400), nullable=False)
    field_def_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000))
    field_key: Mapped[str] = mapped_column(String(100), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)

    category_id: Mapped[Optional[UUID]] = mapped_column(pgUUID(as_uuid=True), nullable=True)

    data_type: Mapped[Optional[FieldDataType]] = mapped_column(Enum(FieldDataType, name="field_data_type"))
    element_type: Mapped[FieldElementType] = mapped_column(Enum(FieldElementType, name="field_element_type"), nullable=False)

    validation: Mapped[Optional[dict]] = mapped_column(JSON)
    ui_config: Mapped[Optional[dict]] = mapped_column(JSON)

    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    source_type: Mapped[Optional[ArtifactSourceType]] = mapped_column(Enum(ArtifactSourceType, name="artifact_source_type"))
    source_package_key: Mapped[Optional[str]] = mapped_column(String(400))
    source_artifact_key: Mapped[Optional[str]] = mapped_column(String(400))
    source_artifact_version: Mapped[Optional[str]] = mapped_column(String(100))
    source_checksum: Mapped[Optional[str]] = mapped_column(String(64))
    installed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    installed_by: Mapped[Optional[str]] = mapped_column(String(100))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String(100))
    updated_by: Mapped[Optional[str]] = mapped_column(String(100))

    # Relationships
    options: Mapped[list["FieldDefOption"]] = relationship("FieldDefOption", backref="field_def", lazy="joined", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<FieldDef tenant_id={self.tenant_id} key={self.field_def_business_key}:{self.field_def_version}>"
