"""
Pydantic schemas for the MyEntity API.

These models define the shape of data accepted and returned by the
MyEntity endpoints.  Use ``MyEntityCreate`` for creating new
instances, ``MyEntityUpdate`` for partial updates and
``MyEntityOut`` for responses.  When adding a new domain copy this
module and adjust the fields accordingly.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MyEntityBase(BaseModel):
    """Shared attributes for MyEntity creation and update."""

    name: str = Field(..., description="Name of the entity")
    data: Optional[Dict[str, Any]] = Field(
        default=None, description="Arbitrary JSON payload for the entity"
    )
    created_by: Optional[str] = Field(
        default=None, description="Identifier of the user who created the entity"
    )
    updated_by: Optional[str] = Field(
        default=None, description="Identifier of the user who last updated the entity"
    )


class MyEntityCreate(MyEntityBase):
    """Payload for creating a new MyEntity.

    The tenant identifier is provided via the path in the API route.
    """

    pass


class MyEntityUpdate(BaseModel):
    """Partial update model for MyEntity.

    All fields are optional to allow partial updates via PATCH.  Only
    provided fields will be updated on the model.
    """

    name: Optional[str] = Field(default=None, description="Updated name")
    data: Optional[Dict[str, Any]] = Field(
        default=None, description="Updated JSON payload"
    )
    updated_by: Optional[str] = Field(
        default=None, description="Identifier of the user performing the update"
    )


class MyEntityOut(MyEntityBase):
    """Response model for a MyEntity instance.

    The ``model_config.from_attributes`` option tells Pydantic to read
    values directly from the SQLAlchemy model instance when returning
    responses from the service layer.  This avoids the need to
    manually convert models to dicts.
    """

    model_config = ConfigDict(from_attributes=True)

    my_entity_id: UUID = Field(..., description="Primary key of the entity")
    tenant_id: UUID = Field(..., description="Tenant that owns the entity")
    created_at: datetime = Field(..., description="Timestamp when the entity was created")
    updated_at: datetime = Field(..., description="Timestamp when the entity was last updated")


# -----------------------------------------------------------------------------
# Pagination model
#
# Many list endpoints return a paginated collection of resources.  Use the
# generic ``PaginationEnvelope`` from ``app.domain.schemas.common`` with
# ``MyEntityOut`` as the item type.  When adding a new domain object define
# a similar ``<Domain>ListResponse`` class inheriting from
# ``PaginationEnvelope[<DomainOut>]``.

from app.domain.schemas.common import PaginationEnvelope


class MyEntityListResponse(PaginationEnvelope[MyEntityOut]):
    """Paginated response body for a list of MyEntity instances.

    Inherits from ``PaginationEnvelope`` to include standard pagination
    metadata such as ``total``, ``limit`` and ``offset``.  The ``items``
    field contains a list of ``MyEntityOut`` objects.

    """

    pass

# ---------------------------------------------------------------------------
# JSON Patch notes (used by service + API docs)
#
# MyEntity supports JSON Patch for:
#   /name
#   /data
#   /data/<nested...>
#
# See app/domain/schemas/json_patch.py for the patch request model.
# ---------------------------------------------------------------------------

MY_ENTITY_JSON_PATCH_ALLOWED_PATH_PREFIXES = ("/name", "/data")
