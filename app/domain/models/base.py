from __future__ import annotations

from typing import Any

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase


# Naming convention only affects constraints created by SQLAlchemy itself.
# Since Liquibase manages the schema, this is just a safety net.
metadata = MetaData(
    naming_convention={
        "pk": "pk_%(table_name)s",
        "fk": "fk_%(table_name)s_%(referred_table_name)s",
        "ix": "idx_%(table_name)s_%(column_0_name)s",
        "uq": "ux_%(table_name)s_%(column_0_name)s",
    }
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models.

    NOTE: The database schema is managed by Liquibase migrations.
    Do NOT call `Base.metadata.create_all()` in application code.
    """

    metadata = metadata
