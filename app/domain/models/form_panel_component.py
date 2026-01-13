"""
SQLAlchemy model for the FormPanelComponent domain.

This table embeds a reusable Component into a FormPanel. Each component
placement may include configuration overrides and ordering information.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB

from .base import Base


class FormPanelComponent(Base):
    """Database model for embedding Components into FormPanels."""

    __tablename__ = "form_panel_component"

    form_panel_component_id: uuid.UUID = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    tenant_id: uuid.UUID = Column(UUID(as_uuid=True), nullable=False)
    form_panel_id: uuid.UUID = Column(UUID(as_uuid=True), nullable=False)
    component_id: uuid.UUID = Column(UUID(as_uuid=True), nullable=False)
    config: dict = Column(JSONB, nullable=True)
    component_order: int = Column(Integer, nullable=False, default=0)
    created_at: datetime = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by: str = Column(String(100), nullable=True)
    updated_by: str = Column(String(100), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<FormPanelComponent form_panel_component_id={self.form_panel_component_id} "
            f"form_panel_id={self.form_panel_id} component_id={self.component_id}>"
        )