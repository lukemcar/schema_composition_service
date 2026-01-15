"""
SQLAlchemy model for the Form domain.

This model represents a top‑level form definition. Each form has a stable
business key and version, a category, a human‑readable name, and optional
configuration stored as JSON. Publishing and draft flags allow the
application to distinguish between live and development versions.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB

from .base import Base


class Form(Base):
    """Database model for forms."""

    __tablename__ = "form"
    
    __table_args__ = (
        {"schema": "schema_composition"},
    )

    form_id: uuid.UUID = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    tenant_id: uuid.UUID = Column(UUID(as_uuid=True), nullable=False)
    form_key: str = Column(String(200), nullable=False)
    version: str = Column(String(50), nullable=False)
    form_name: str = Column(String(100), nullable=False)
    description: str = Column(String(255), nullable=True)
    category_id: uuid.UUID = Column(UUID(as_uuid=True), nullable=True)
    ui_config: dict = Column(JSONB, nullable=True)
    is_active: bool = Column(Boolean, nullable=False, default=True)
    is_published: bool = Column(Boolean, nullable=False, default=False)
    created_at: datetime = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by: str = Column(String(100), nullable=True)
    updated_by: str = Column(String(100), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Form form_id={self.form_id} tenant_id={self.tenant_id} "
            f"form_key={self.form_key} version={self.version}>"
        )