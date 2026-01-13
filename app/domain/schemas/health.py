"""
Pydantic models for health check responses.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Represents the health status of the service."""

    status: str = Field(..., description="Overall service status")
    details: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional diagnostic details"
    )
