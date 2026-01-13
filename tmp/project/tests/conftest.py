import os
import time
import subprocess
from pathlib import Path  # needed for REPO_ROOT

import psycopg2
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.util.liquibase import apply_changelog

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

# Project root (formless_agent_service/)
REPO_ROOT = Path(__file__).resolve().parents[1]

# Optional: load environment variables from .env.test using python-dotenv
# This keeps test DB config out of the code.
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


# ---------------------------------------------------------------------------
# Environment loading
# ---------------------------------------------------------------------------

# If python-dotenv is available and .env.test exists, load it
if load_dotenv is not None:
    env_file = REPO_ROOT / ".env.test"
    if env_file.exists():
        load_dotenv(env_file)


# ---------------------------------------------------------------------------
# Database configuration (test-only)
# ---------------------------------------------------------------------------
# These can be overridden via:
#   - Real environment variables, or
#   - A .env.test file at the project root.
#
# Defaults are sensible for local test runs.

DB_HOST = os.getenv("TEST_DB_HOST", "localhost")
DB_PORT = int(os.getenv("TEST_DB_PORT", "25433"))
DB_NAME = os.getenv("TEST_DB_NAME", "formless_agent_service")
DB_USER = os.getenv("TEST_DB_USER", "formless_agent_app")
DB_PASSWORD = os.getenv("TEST_DB_PASSWORD", "formless_agent_app_password")
LIQUIBASE_PROPERTY_FILE = os.getenv(
    "TEST_LIQUIBASE_PROPERTY_FILE",
    "docker-liquibase.properties",
)

# SQLAlchemy connection URL for the test database
TEST_DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:"
    f"{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


# ---------------------------------------------------------------------------
# Paths that depend on REPO_ROOT / LIQUIBASE_PROPERTY_FILE
# ---------------------------------------------------------------------------

# Path to docker-compose.test.yml (one level above tests/)
COMPOSE_FILE = os.path.join(
    REPO_ROOT,
    "docker-compose.test.yml",
)

# Path to Liquibase properties file
LIQUIBASE_DEFAULTS_FILE = os.path.join(
    REPO_ROOT,
    "migrations",
    "liquibase",
    LIQUIBASE_PROPERTY_FILE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _wait_for_postgres(
    host: str,
    port: int,
    user: str,
    password: str,
    db: str,
    timeout: int = 60,
) -> None:
    """
    Polls Postgres until it is ready to accept connections or the timeout expires.
    """
    start = time.time()
    while True:
        try:
            conn = psycopg2.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                dbname=db,
            )
            conn.close()
            return
        except Exception:
            if time.time() - start > timeout:
                raise RuntimeError("Timed out waiting for Postgres to be ready")
            time.sleep(1)


def _run_liquibase_update() -> None:
    """
    Runs Liquibase using the same pyliquibase-based helper that production uses,
    but with a test-specific Liquibase properties file.

    All connection details (URL, username, password) are defined in:
        migrations/liquibase/docker-liquibase.test.properties

    No environment overrides are applied here.
    """
    apply_changelog(property_file=str(LIQUIBASE_DEFAULTS_FILE))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def docker_compose():
    """
    Session-scoped fixture that starts the Postgres test container
    using docker compose and tears it down at the end of the test session.
    """
    # Bring up docker compose (build image if needed)
    subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE_FILE), "up", "--build", "-d"],
        check=True,
    )

    try:
        # Wait for Postgres to be ready
        _wait_for_postgres(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            db=DB_NAME,
        )
        yield
    finally:
        # Tear down everything, including volumes
        subprocess.run(
            ["docker", "compose", "-f", str(COMPOSE_FILE), "down", "-v"],
            check=True,
        )


@pytest.fixture(scope="session")
def liquibase_migrations(request, docker_compose):
    """
    Session-scoped fixture that runs Liquibase migrations once
    if any collected test is marked with @pytest.mark.liquibase.

    Ensures we do not run Liquibase unnecessarily when only pure
    unit tests are executed.
    """
    # Check if at least one test has the "liquibase" marker
    has_liquibase_tests = any(
        item.get_closest_marker("liquibase") is not None
        for item in request.session.items
    )

    if not has_liquibase_tests:
        # No tests require Liquibase; skip running migrations
        yield
        return

    # At least one test requires Liquibase; run migrations once
    _run_liquibase_update()
    yield


@pytest.fixture(scope="session")
def engine(docker_compose, liquibase_migrations):
    """
    Session-scoped SQLAlchemy engine backed by the Postgres test database.

    This fixture ensures:
    - Docker Compose is up and Postgres is ready.
    - Liquibase migrations have been applied if required.
    """
    engine = create_engine(TEST_DATABASE_URL, future=True)

    yield engine

    # Cleanly dispose of the engine at the end of the session
    engine.dispose()


@pytest.fixture
def db_session(engine) -> Session:
    """
    Per-test SQLAlchemy Session fixture.

    Each test gets:
    - A connection.
    - A started transaction.
    - A Session bound to that connection.

    After the test:
    - The Session is closed.
    - The transaction is rolled back.
    - The connection is closed.

    This pattern ensures that each test sees a clean database state
    (from the same schema) without dropping and recreating tables.
    """
    connection = engine.connect()
    transaction = connection.begin()

    TestingSessionLocal = sessionmaker(
        bind=connection,
        autoflush=False,
        autocommit=False,
        future=True,
    )

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
