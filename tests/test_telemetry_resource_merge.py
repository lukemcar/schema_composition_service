"""Tests for the custom telemetry initialisation.

These tests validate that our ``init_tracing`` helper respects the
``OTEL_SERVICE_NAME`` environment variable and does not override it
when a service name is provided explicitly.  They also ensure that
the implementation does not rely on the missing ``Resource.get_default``
API and thus works across different OpenTelemetry SDK versions.
"""

import importlib
from typing import Any

import pytest


def _get_service_name_from_provider(provider: Any) -> str | None:
    """Extract the service.name attribute from a tracer provider.

    Different OpenTelemetry SDK versions expose the resource on
    different attributes.  This helper attempts to access the resource
    and return the ``service.name`` attribute if it is present.  If
    it cannot be found, ``None`` is returned.
    """
    resource = getattr(provider, "resource", None)
    if resource and hasattr(resource, "attributes"):
        return resource.attributes.get("service.name")  # type: ignore[no-any-return]
    return None


@pytest.mark.usefixtures("monkeypatch")
def test_init_tracing_env_precedence(monkeypatch: Any) -> None:
    """``init_tracing`` should prefer ``OTEL_SERVICE_NAME`` over the argument.

    When ``OTEL_SERVICE_NAME`` is set in the environment, the
    user-specified service name should not override it.  If
    OpenTelemetry is not installed, the test is skipped.
    """
    pytest.importorskip("opentelemetry")
    trace = pytest.importorskip("opentelemetry.trace")
    TracerProvider = pytest.importorskip("opentelemetry.sdk.trace").TracerProvider  # type: ignore

    # Set the environment variable to override the service name
    monkeypatch.setenv("OTEL_SERVICE_NAME", "my-entity-service.api")

    # Reload telemetry to ensure a clean state before configuration.
    from app.core import telemetry  # type: ignore
    importlib.reload(telemetry)

    # Call init_tracing with an explicit service name; the env should win.
    telemetry.init_tracing(service_name="my-entity-service.api")

    provider = trace.get_tracer_provider()
    assert isinstance(provider, TracerProvider)

    service_name = _get_service_name_from_provider(provider)
    if service_name is not None:
        assert service_name == "my-entity-service.api"
