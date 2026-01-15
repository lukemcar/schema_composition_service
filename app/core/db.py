"""
Database layer for the SchemaComposition Service.

This module lazily initializes the SQLAlchemy engine and session factory.
Why:
- Tests often set DATABASE_URL at runtime; import-time engine creation would
  capture the wrong value.
- Lazy init guarantees the engine is created using the current environment
  variables at first use.

Rules:
- Do NOT call Base.metadata.create_all(); Liquibase manages schema.
- All DB access should go through get_db() (FastAPI) or get_cm_db() (workers).
"""

from __future__ import annotations

import logging
import threading
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.orm.session import Session

from app.core.config import Config

logger = logging.getLogger(__name__)

# SQLAlchemy base (safe to create at import time)
Base = declarative_base()

# Import models so SQLAlchemy knows about them (safe at import time).
# Liquibase owns schema, but SQLAlchemy still needs model registration for ORM usage.
try:
    # Import domain models to register them with SQLAlchemy.  Additional
    # models should be imported here when new domains are added.  The
    # enums module is imported indirectly via the models package.\
    from app.domain.models import FormCatalogCategory  # noqa: F401
    from app.domain.models import FieldDef  # noqa: F401
    from app.domain.models import FieldDefOption  # noqa: F401
    from app.domain.models import Component  # noqa: F401
    from app.domain.models import ComponentPanel  # noqa: F401
    from app.domain.models import ComponentPanelField  # noqa: F401
    from app.domain.models import Form  # noqa: F401
    from app.domain.models import FormPanel  # noqa: F401
    from app.domain.models import FormPanelComponent  # noqa: F401
    from app.domain.models import FormPanelField  # noqa: F401
    from app.domain.models import FormSubmission  # noqa: F401
    from app.domain.models import FormSubmissionValue  # noqa: F401
except Exception:
    pass

# Lazy globals
_engine: Optional[Engine] = None
_SessionLocal: Optional[sessionmaker] = None

# Guard to ensure single init in multi-threaded contexts
_init_lock = threading.Lock()


def _init_engine_and_session() -> None:
    """Initialize SQLAlchemy engine + SessionLocal exactly once (lazy)."""
    global _engine, _SessionLocal

    if _engine is not None and _SessionLocal is not None:
        return

    with _init_lock:
        if _engine is not None and _SessionLocal is not None:
            return

        db_url = Config.database_url()
        logger.info("Initializing SQLAlchemy engine with DATABASE_URL=%s", db_url)

        engine = create_engine(db_url, pool_pre_ping=True)

        # Instrument SQLAlchemy engine for tracing (best-effort).
        try:
            from app.core.telemetry import instrument_sqlalchemy  # type: ignore

            instrument_sqlalchemy(engine)
        except Exception:
            # Never fail app startup due to tracing
            logger.debug("SQLAlchemy instrumentation not available", exc_info=True)

        _engine = engine
        _SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)


def get_engine() -> Engine:
    """Return the initialized SQLAlchemy engine (initializes lazily)."""
    _init_engine_and_session()
    assert _engine is not None
    return _engine


def get_sessionmaker() -> sessionmaker:
    """Return the initialized sessionmaker (initializes lazily)."""
    _init_engine_and_session()
    assert _SessionLocal is not None
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a DB session per request."""
    SessionLocal = get_sessionmaker()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_cm_db() -> Generator[Session, None, None]:
    """
    Context manager for non-FastAPI code (e.g., Celery workers).

    Usage:
        with get_cm_db() as db:
            ...
    """
    SessionLocal = get_sessionmaker()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_connection() -> bool:
    """Verify the database connection is available by executing a trivial query."""
    try:
        engine = get_engine()
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logging.getLogger("schema_composition_service.db").error(
            "Database readiness check failed", exc_info=exc
        )
        raise


# Optional: test helper
def reset_db_for_tests() -> None:
    """
    Reset cached engine/sessionmaker.

    Useful for tests that change DATABASE_URL between test modules.
    Call this only in tests.
    """
    global _engine, _SessionLocal
    with _init_lock:
        _engine = None
        _SessionLocal = None

__all__ = [
    "Base",
    "get_engine",
    "get_sessionmaker",
    "get_db",
    "get_cm_db",
    "check_database_connection",
    "reset_db_for_tests",
    # Export models for type hints and convenience
    "FormCatalogCategory",
    "FieldDef",
    "FieldDefOption",
    "Component",
    "ComponentPanel",
    "ComponentPanelField",
    "Form",
    "FormPanel",
    "FormPanelComponent",
    "FormPanelField",
    "FormSubmission",
    "FormSubmissionValue",
]
