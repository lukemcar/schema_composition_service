"""
Utilities for invoking Liquibase migrations from within the Formless Agent
Service.

This module defines a thin wrapper around the ``pyliquibase`` package that
executes database migrations defined in the ``migrations`` directory.  It
encapsulates logging and allows the caller to override the property file used
by Liquibase via the ``property_file`` argument.  By default the Docker
properties file is used, which mirrors our containerized deployment.
"""

import logging
from typing import Optional

try:
    # Import lazily to avoid import errors if pyliquibase is not installed in
    # certain environments (e.g. during unit tests where migrations are mocked).
    from pyliquibase import Pyliquibase  # type: ignore
except Exception as exc:  # pragma: no cover
    Pyliquibase = None  # type: ignore
    _import_error = exc


def apply_changelog(property_file: Optional[str] = None) -> None:
    """Run Liquibase to apply the database changelog.

    Parameters
    ----------
    property_file: Optional[str]
        The path to a Liquibase properties file.  If ``None`` the default
        ``migrations/liquibase/docker-liquibase.properties`` is used.
    """
    if Pyliquibase is None:
        raise ImportError(
            "pyliquibase is not installed; cannot apply Liquibase changelog"
        ) from _import_error

    prop_file = property_file or "migrations/liquibase/docker-liquibase.properties"
    logging.info("Starting Liquibase schema validation and update: %s", prop_file)

    liquibase = Pyliquibase(defaultsFile=prop_file)
    liquibase.validate()
    liquibase.status()
    liquibase.updateSQL()
    liquibase.update()
    logging.info("Liquibase update completed")
