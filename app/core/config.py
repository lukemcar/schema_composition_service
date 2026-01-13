"""
Centralised configuration settings for the Formless Agent Service.
"""

import os


class Config:
    """Configuration helper for reading environment variables."""

    @staticmethod
    def database_url() -> str:
        """Return the SQLAlchemy database URL.

        Defaults to a local Postgres instance named ``my_entity_service``.  You
        can override this via the ``DATABASE_URL`` environment variable.
        """
        return os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg2://postgres:postgres@localhost:5432/my_entity_service",
        )

    @staticmethod
    def liquibase_enabled() -> bool:
        value = os.getenv("LIQUIBASE_ENABLED", "true").lower()
        return value in {"true", "1", "yes", "y"}

    @staticmethod
    def liquibase_property_file() -> str:
        return os.getenv(
            "LIQUIBASE_PROPERTY_FILE",
            "migrations/liquibase/docker-liquibase.properties",
        )

    @staticmethod
    def jwt_secret() -> str:
        return os.getenv("JWT_SECRET", "2zacRJ76Oj0o5RRyg7nAHtXy09bl6FzS")

    @staticmethod
    def auth0_domain() -> str:
        return os.getenv(
            "AUTH0_DOMAIN", "dev-5f2qcnpxxmrvpvjy.us.auth0.com"
        )

    @staticmethod
    def jwt_algorithm() -> str:
        return os.getenv("JWT_ALGORITHM", "HS256")
    
    @staticmethod
    def cohere_api_key() -> str:
        return os.getenv("COHERE_API_KEY", "FoQhIP2wnEyr6zwnVFMCDLs6GSl0o7AEoO01D6vV")
    
    @staticmethod
    def celery_broker_url() -> str:
        """Return the Celery broker URL.

        By default connects to a local RabbitMQ instance using the
        ``my_entity`` user and vhost.  Override via the ``CELERY_BROKER_URL``
        environment variable if needed.
        """
        return os.getenv(
            "CELERY_BROKER_URL",
            "amqp://my_entity:my_entity@localhost:5672/my_entity",
        )
    
    @staticmethod
    def celery_result_backend() -> str:
        return os.getenv("CELERY_RESULT_BACKEND", "rpc://")
    
    
    @staticmethod
    def ipinfo_token() -> str:
        return os.getenv("IPINFO_TOKEN", "a0dfdf5587d22d")
    
    @staticmethod
    def ipinfo_url() -> str:
        return os.getenv("IPINFO_URL", "https://ipinfo.io")
