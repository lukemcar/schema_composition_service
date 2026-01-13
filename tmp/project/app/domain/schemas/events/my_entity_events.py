"""
Event payloads for MyEntity domain events.

Consumers of MyEntity events should depend on these models when
validating incoming messages.  Each message embeds the identifiers
required to uniquely identify the entity and, for updates, a
``changes`` dictionary describing which fields were modified.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel


class MyEntityBaseMessage(BaseModel):
    tenant_id: UUID
    my_entity_id: UUID


class MyEntityCreatedMessage(MyEntityBaseMessage):
    payload: Dict[str, Any]


class MyEntityUpdatedMessage(MyEntityBaseMessage):
    changes: Dict[str, Any]
    payload: Dict[str, Any]


class MyEntityDeletedMessage(MyEntityBaseMessage):
    deleted_dt: Optional[str] = None