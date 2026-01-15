"""
SQLAlchemy model for the ComponentPanel domain.

Component panels represent logical groupings of fields inside a Component.
Panels can be nested hierarchically via a parent_panel_id. This simplified
model captures only basic relationships and ordering information.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB

from .base import Base


class ComponentPanel(Base):
    """Database model for component panels."""

    __tablename__ = "component_panel"
    
    __table_args__ = (
        {"schema": "schema_composition"},
    )

    component_panel_id: uuid.UUID = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    tenant_id: uuid.UUID = Column(UUID(as_uuid=True), nullable=False)
    component_id: uuid.UUID = Column(UUID(as_uuid=True), nullable=False)
    parent_panel_id: uuid.UUID = Column(UUID(as_uuid=True), nullable=True)
    panel_key: str = Column(String(200), nullable=False)
    panel_label: str = Column(String(100), nullable=True)
    ui_config: dict = Column(JSONB, nullable=True)
    panel_order: int = Column(Integer, nullable=False, default=0)
    created_at: datetime = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by: str = Column(String(100), nullable=True)
    updated_by: str = Column(String(100), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<ComponentPanel component_panel_id={self.component_panel_id} "
            f"component_id={self.component_id} tenant_id={self.tenant_id} "
            f"panel_key={self.panel_key}>"
        )