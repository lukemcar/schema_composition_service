"""
SQLAlchemy model for the FormPanelField domain.

This table places a field definition directly onto a form panel (a non‑reusable
field instance). Each placement includes ordering and optional overrides.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import UUID, JSONB

from .base import Base


class FormPanelField(Base):
    """Database model for field instances placed directly on a FormPanel."""

    __tablename__ = "form_panel_field"
    
    __table_args__ = (
        {"schema": "schema_composition"},
    )

    form_panel_field_id: uuid.UUID = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    tenant_id: uuid.UUID = Column(UUID(as_uuid=True), nullable=False)
    form_panel_id: uuid.UUID = Column(UUID(as_uuid=True), nullable=False)
    field_def_id: uuid.UUID = Column(UUID(as_uuid=True), nullable=False)
    overrides: dict = Column(JSONB, nullable=True)
    field_order: int = Column(Integer, nullable=False, default=0)
    is_required: bool = Column(Boolean, nullable=False, default=False)
    created_at: datetime = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by: str = Column(String(100), nullable=True)
    updated_by: str = Column(String(100), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<FormPanelField form_panel_field_id={self.form_panel_field_id} "
            f"form_panel_id={self.form_panel_id} field_def_id={self.field_def_id}>"
        )