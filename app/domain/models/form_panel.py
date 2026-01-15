"""
SQLAlchemy model for the FormPanel domain.

Forms consist of one or more panels that organise fields and embedded
components. Panels can be nested via a parent_panel_id. This simplified
model includes ordering information and optional configuration.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB

from .base import Base


class FormPanel(Base):
    """Database model for panels within a form."""

    __tablename__ = "form_panel"
    
    __table_args__ = (
        {"schema": "schema_composition"},
    )

    form_panel_id: uuid.UUID = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    tenant_id: uuid.UUID = Column(UUID(as_uuid=True), nullable=False)
    form_id: uuid.UUID = Column(UUID(as_uuid=True), nullable=False)
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
            f"<FormPanel form_panel_id={self.form_panel_id} form_id={self.form_id} "
            f"panel_key={self.panel_key}>"
        )