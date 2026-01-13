"""
Event payloads for FormCatalogCategory domain events.

These message classes define the structure of the payloads sent and
received over the message bus for FormCatalogCategory lifecycle
events.  Consumers of these events should depend on these models
when validating incoming messages.  Each message embeds the
identifiers required to uniquely identify the category and, for
updates, a ``changes`` dictionary describing which fields were
modified.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel


class FormCatalogCategoryBaseMessage(BaseModel):
    tenant_id: UUID
    form_catalog_category_id: UUID


class FormCatalogCategoryCreatedMessage(FormCatalogCategoryBaseMessage):
    payload: Dict[str, Any]


class FormCatalogCategoryUpdatedMessage(FormCatalogCategoryBaseMessage):
    changes: Dict[str, Any]
    payload: Dict[str, Any]


class FormCatalogCategoryDeletedMessage(FormCatalogCategoryBaseMessage):
    deleted_dt: Optional[str] = None


__all__ = [
    "FormCatalogCategoryCreatedMessage",
    "FormCatalogCategoryUpdatedMessage",
    "FormCatalogCategoryDeletedMessage",
]