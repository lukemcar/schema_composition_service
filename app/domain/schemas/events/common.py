"""
Common event envelope definitions for messaging.

All events published to the messaging system should be wrapped in an
``EventEnvelope``. The envelope captures metadata such as a unique
``event_id``, the ``event_type`` (task name), the schema version of
the payload, and identifiers used for correlating messages across
systems (correlation and causation IDs). The actual domain payload
is stored in the ``data`` field.

Using a consistent envelope simplifies versioning and allows
consumers to validate metadata before processing the embedded domain
payload. New fields can be added to the envelope without breaking
existing consumers.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field


class EventEnvelope(BaseModel):
    """Standard wrapper for all published events."""

    event_id: UUID = Field(..., description="Unique identifier for this event")
    event_type: str = Field(..., description="Task name / routing key for this event")
    schema_version: int = Field(
        1, description="Version of the event payload schema"
    )
    occurred_at: datetime = Field(
        ..., description="Time when the event occurred or was published"
    )
    producer: str = Field(..., description="Name of the producing service")
    tenant_id: UUID = Field(..., description="Tenant identifier")
    correlation_id: Optional[Union[UUID, str]] = Field(
        None,
        description="Correlation identifier linking a chain of events or requests",
    )
    causation_id: Optional[UUID] = Field(
        None, description="Identifier of the event that directly triggered this event"
    )
    traceparent: Optional[str] = Field(
        None,
        description="W3C traceparent header for distributed tracing",
    )
    data: Dict[str, Any] = Field(
        ..., description="Domain payload for the event"
    )