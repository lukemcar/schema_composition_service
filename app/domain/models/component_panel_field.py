"""
SQLAlchemy model for the ComponentPanelField domain.

This table places a field definition onto a ComponentPanel. Each record
associates a field_def_id with a component panel and allows simple
configuration overrides on a per‑placement basis. For simplicity, only
the essential relationships and ordering attributes are included.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB

from .base import Base


class ComponentPanelField(Base):
    """Database model for fields placed on a ComponentPanel."""

    __tablename__ = "component_panel_field"

    component_panel_field_id: uuid.UUID = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    tenant_id: uuid.UUID = Column(UUID(as_uuid=True), nullable=False)
    component_panel_id: uuid.UUID = Column(UUID(as_uuid=True), nullable=False)
    field_def_id: uuid.UUID = Column(UUID(as_uuid=True), nullable=False)
    # Field instance overrides stored as JSONB (label overrides, validation, etc.)
    overrides: dict = Column(JSONB, nullable=True)
    field_order: int = Column(Integer, nullable=False, default=0)
    is_required: bool = Column(Boolean, nullable=False, default=False)
    created_at: datetime = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by: str = Column(String(100), nullable=True)
    updated_by: str = Column(String(100), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<ComponentPanelField component_panel_field_id={self.component_panel_field_id} "
            f"component_panel_id={self.component_panel_id} field_def_id={self.field_def_id}>"
        )