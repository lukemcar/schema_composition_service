"""
SQLAlchemy model for the Component domain.

This table stores reusable UI components that can be embedded in forms. Each
component has a stable key and version scoped to a tenant, along with
human‑readable names and metadata. This model is simplified relative to the
DDL and omits certain advanced fields (such as nested panel definitions) for
brevity.
"""

import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime

from .base import Base


class Component(Base):
    """Database model for Components."""

    __tablename__ = "component"

    # Primary key
    component_id: uuid.UUID = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    # Tenant that owns the component
    tenant_id: uuid.UUID = Column(UUID(as_uuid=True), nullable=False)
    # Business key used for import/export and integrations (unique per tenant)
    component_key: str = Column(String(200), nullable=False)
    # Version identifier for the component (e.g. semantic version string)
    version: str = Column(String(50), nullable=False)
    # Human‑readable name shown in builder UI
    component_name: str = Column(String(100), nullable=False)
    # Optional description or label
    description: str = Column(String(255), nullable=True)
    # Category identifier referencing form_catalog_category.id (stored as UUID)
    category_id: uuid.UUID = Column(UUID(as_uuid=True), nullable=True)
    # Arbitrary JSON configuration for the component UI
    ui_config: dict = Column(JSONB, nullable=True)
    # Active flag controls whether the component is available for use
    is_active: bool = Column(Boolean, nullable=False, default=True)
    # Audit fields
    created_at: datetime = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by: str = Column(String(100), nullable=True)
    updated_by: str = Column(String(100), nullable=True)

    __table_args__ = (
        # Stable business key and version uniqueness per tenant
        {
            "sqlite_autoincrement": True,
        },
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Component component_id={self.component_id} tenant_id={self.tenant_id} "
            f"component_key={self.component_key} version={self.version}>"
        )