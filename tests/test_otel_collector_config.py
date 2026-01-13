"""Test the OpenTelemetry collector configuration.

These tests verify that the collector is configured to export traces
via the OTLP exporter to the Jaeger service and that the pipeline
references the correct exporter.  They are string‑based tests rather
than YAML parsing tests to avoid introducing additional dependencies.
"""

from pathlib import Path


def test_collector_uses_otlp_exporter() -> None:
    """Ensure the collector config exports traces via the OTLP exporter.

    The configuration should define an ``otlp`` exporter pointing at
    ``jaeger:4317`` and the traces pipeline should reference this
    exporter.  We read the YAML file as a raw string and search for
    key lines instead of loading YAML to keep the test simple and
    dependency‑free.
    """
    # Locate the collector configuration relative to this test file.
    # ``tests`` lives at the project root level, so its parent is the
    # repository root.  The collector config resides under
    # ``docker/otel`` in the project root.
    root_dir = Path(__file__).resolve().parents[1]
    config_path = root_dir / "docker" / "otel" / "otel-collector-config.yml"
    content = config_path.read_text()
    assert "exporters" in content
    assert "otlp:" in content
    assert "endpoint: jaeger:4317" in content
    # Ensure the traces pipeline references the OTLP exporter
    assert "exporters: [otlp]" in content