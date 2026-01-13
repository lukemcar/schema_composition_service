"""
Common Pydantic schemas shared across the Dyno Conversa service.

This module defines reusable objects for error responses and pagination
envelopes used by list endpoints.
"""

from __future__ import annotations

from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorResponseBody(BaseModel):
    """Standard error response body.

    All error responses should return this schema with a machine-readable
    ``code`` and a human-readable ``message``.  Additional fields may
    be added in future but clients should rely on these two keys.
    """

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")


class PaginationEnvelope(BaseModel, Generic[T]):
    """Wrapper for paginated list responses.

    ``items`` contains the list of returned resources, ``total`` is the
    total number of matching records, and ``limit``/``offset`` echo the
    request parameters.
    """

    items: List[T]
    total: int
    limit: Optional[int] = None
    offset: Optional[int] = None
