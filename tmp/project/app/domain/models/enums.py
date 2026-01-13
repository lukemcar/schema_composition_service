"""
Enumerated types defined in the Dyno Form schema.

This module centralises database ENUM definitions so that they are
declared exactly once across the service.  These enums correspond to
the Postgres types defined in ``form_schema_v02.sql``.  They are
exposed as Python ``Enum`` classes to simplify usage in Pydantic
schemas and improve type safety.  When adding additional enums to
the schema, declare them here and use the Python enum values in
schemas and models.  Note that ENUMs are not treated as domain
objects; they do not require API routes or CRUD services.
"""

from __future__ import annotations

from enum import Enum


class FieldDataType(str, Enum):
    """Semantic data shapes that a field can store.

    Do not include UI widgets here; these are purely about the shape
    of the stored value.  UI behaviour is defined by
    ``FieldElementType``.
    """

    TEXT = "TEXT"
    NUMBER = "NUMBER"
    BOOLEAN = "BOOLEAN"
    DATE = "DATE"
    DATETIME = "DATETIME"
    SINGLESELECT = "SINGLESELECT"
    MULTISELECT = "MULTISELECT"


class FieldElementType(str, Enum):
    """UI element types controlling rendering and behaviour.

    The ``ACTION`` element does not store any data; when using
    ``ACTION`` the corresponding ``data_type`` should be ``None``.
    SELECT and MULTISELECT widgets store option keys; the shape of
    the stored value is determined by the ``FieldDataType``.
    """

    TEXT = "TEXT"
    TEXTAREA = "TEXTAREA"
    DATE = "DATE"
    DATETIME = "DATETIME"
    SELECT = "SELECT"
    MULTISELECT = "MULTISELECT"
    ACTION = "ACTION"


class ArtifactSourceType(str, Enum):
    """Origin of a marketplace artifact installed into a tenant.

    This enumeration tracks the provenance of catalog artifacts.  It
    mirrors the ``artifact_source_type`` type defined in the schema.
    """

    MARKETPLACE = "MARKETPLACE"
    PROVIDER = "PROVIDER"
    TENANT = "TENANT"
    SYSTEM = "SYSTEM"


__all__ = [
    "FieldDataType",
    "FieldElementType",
    "ArtifactSourceType",
]