"""
Pydantic schemas for the FieldDef API.

These models define the shape of data accepted and returned by the
FieldDef endpoints.  ``FieldDefCreate`` captures the required
attributes for creating a new definition, ``FieldDefUpdate`` allows
partial updates via PUT, and ``FieldDefOut`` mirrors the SQLAlchemy
model for responses.  When listing definitions use
``FieldDefListResponse`` which wraps a paginated collection of
``FieldDefOut`` objects.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.models.enums import (
    FieldDataType,
    FieldElementType,
    ArtifactSourceType,
)
from app.domain.schemas.common import PaginationEnvelope


class FieldDefBase(BaseModel):
    """Shared attributes for FieldDef creation and update."""

    field_def_business_key: str = Field(
        ..., description="Stable business key identifying the field definition"
    )
    field_def_version: int = Field(
        default=1, description="Version number for the field definition"
    )
    name: str = Field(..., description="Internal name for the field definition")
    description: Optional[str] = Field(
        default=None, description="Optional description of the field definition"
    )
    field_key: str = Field(
        ..., description="Default key for the field when placed on a form"
    )
    label: str = Field(
        ..., description="Human‑readable label shown in UI"
    )
    category_id: Optional[UUID] = Field(
        default=None, description="Optional category grouping identifier"
    )
    data_type: Optional[FieldDataType] = Field(
        default=None,
        description="Semantic data shape stored for this field; required unless element_type=ACTION",
    )
    element_type: FieldElementType = Field(
        ..., description="UI element type controlling rendering and behaviour"
    )
    validation: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional JSON object describing validation rules",
    )
    ui_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional JSON object containing UI configuration and hints",
    )
    is_published: bool = Field(
        default=False, description="Whether the field definition is published"
    )
    published_at: Optional[datetime] = Field(
        default=None, description="Timestamp when the definition was published"
    )
    is_archived: bool = Field(
        default=False, description="Whether the field definition is archived"
    )
    archived_at: Optional[datetime] = Field(
        default=None, description="Timestamp when the definition was archived"
    )
    source_type: Optional[ArtifactSourceType] = Field(
        default=None, description="Origin of the field definition"
    )
    source_package_key: Optional[str] = Field(
        default=None, description="Key of the source package for this definition"
    )
    source_artifact_key: Optional[str] = Field(
        default=None, description="Key of the source artifact within the package"
    )
    source_artifact_version: Optional[str] = Field(
        default=None, description="Version of the source artifact"
    )
    source_checksum: Optional[str] = Field(
        default=None, description="Checksum of the source artifact"
    )
    installed_at: Optional[datetime] = Field(
        default=None, description="Timestamp when the definition was installed"
    )
    installed_by: Optional[str] = Field(
        default=None, description="Actor that installed the definition"
    )
    created_by: Optional[str] = Field(
        default=None, description="Identifier of the user creating the definition"
    )
    updated_by: Optional[str] = Field(
        default=None, description="Identifier of the user who last updated the definition"
    )


class FieldDefCreate(FieldDefBase):
    """Payload for creating a new FieldDef.

    The tenant identifier is provided via the path in the API route.
    """

    pass


class FieldDefUpdate(BaseModel):
    """Partial update model for FieldDef.

    All fields are optional to allow partial updates via PUT.  Only
    provided fields will be updated on the model.
    """

    field_def_business_key: Optional[str] = Field(
        default=None, description="New business key"
    )
    field_def_version: Optional[int] = Field(
        default=None, description="New version number"
    )
    name: Optional[str] = Field(
        default=None, description="Updated internal name"
    )
    description: Optional[str] = Field(
        default=None, description="Updated description"
    )
    field_key: Optional[str] = Field(
        default=None, description="Updated default field key"
    )
    label: Optional[str] = Field(
        default=None, description="Updated UI label"
    )
    category_id: Optional[UUID] = Field(
        default=None, description="Updated category ID"
    )
    data_type: Optional[FieldDataType] = Field(
        default=None, description="Updated data type"
    )
    element_type: Optional[FieldElementType] = Field(
        default=None, description="Updated element type"
    )
    validation: Optional[Dict[str, Any]] = Field(
        default=None, description="Updated validation configuration"
    )
    ui_config: Optional[Dict[str, Any]] = Field(
        default=None, description="Updated UI configuration"
    )
    is_published: Optional[bool] = Field(
        default=None, description="Publish or unpublish the definition"
    )
    published_at: Optional[datetime] = Field(
        default=None, description="Updated publication timestamp"
    )
    is_archived: Optional[bool] = Field(
        default=None, description="Archive or unarchive the definition"
    )
    archived_at: Optional[datetime] = Field(
        default=None, description="Updated archive timestamp"
    )
    source_type: Optional[ArtifactSourceType] = Field(
        default=None, description="Updated source type"
    )
    source_package_key: Optional[str] = Field(
        default=None, description="Updated source package key"
    )
    source_artifact_key: Optional[str] = Field(
        default=None, description="Updated source artifact key"
    )
    source_artifact_version: Optional[str] = Field(
        default=None, description="Updated source artifact version"
    )
    source_checksum: Optional[str] = Field(
        default=None, description="Updated checksum"
    )
    installed_at: Optional[datetime] = Field(
        default=None, description="Updated installation timestamp"
    )
    installed_by: Optional[str] = Field(
        default=None, description="Updated installed by"
    )
    updated_by: Optional[str] = Field(
        default=None, description="Identifier of the user performing the update"
    )


class FieldDefOut(FieldDefBase):
    """Response model for a FieldDef instance.

    The ``model_config.from_attributes`` option tells Pydantic to read
    values directly from the SQLAlchemy model instance when returning
    responses from the service layer.  This avoids the need to
    manually convert models to dicts.
    """

    model_config = ConfigDict(from_attributes=True)

    field_def_id: UUID = Field(
        ..., description="Primary key of the field definition"
    )
    tenant_id: UUID = Field(
        ..., description="Tenant that owns the field definition"
    )
    created_at: datetime = Field(
        ..., description="Timestamp when the definition was created"
    )
    updated_at: datetime = Field(
        ..., description="Timestamp when the definition was last updated"
    )


class FieldDefListResponse(PaginationEnvelope[FieldDefOut]):
    """Paginated response body for a list of FieldDef instances."""

    pass


__all__ = [
    "FieldDefCreate",
    "FieldDefUpdate",
    "FieldDefOut",
    "FieldDefListResponse",
]