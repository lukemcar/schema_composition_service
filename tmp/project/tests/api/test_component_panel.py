"""
API tests for the ComponentPanel domain.

These tests confirm that the component panel routes interact correctly
with the service layer.  They patch service functions to capture
arguments and ensure that the endpoints pass along tenant context,
filter parameters and payloads as expected.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.component_panel import (
    ComponentPanelCreate,
    ComponentPanelUpdate,
    ComponentPanelOut,
    ComponentPanelListResponse,
)
from app.domain.services import component_panel_service

from app.api.routes.component_panel import (
    list_component_panels,
    create_component_panel,
    get_component_panel,
    update_component_panel,
    delete_component_panel,
)


class DummySession(Session):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _fake_panel_out(
    *,
    tenant_id: uuid.UUID,
    component_panel_id: uuid.UUID,
    component_id: uuid.UUID,
    panel_key: str,
    panel_label: str = "",
    parent_panel_id: uuid.UUID | None = None,
) -> ComponentPanelOut:
    now = _now()
    return ComponentPanelOut(
        component_panel_id=component_panel_id,
        tenant_id=tenant_id,
        component_id=component_id,
        parent_panel_id=parent_panel_id,
        panel_key=panel_key,
        panel_label=panel_label,
        ui_config=None,
        panel_order=0,
        created_by="tester",
        created_at=now,
        updated_at=now,
    )


def test_list_component_panels_calls_service_and_wraps_response(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    comp_id = uuid.uuid4()
    fake_db = DummySession()

    p1 = _fake_panel_out(
        tenant_id=tenant_id,
        component_panel_id=uuid.uuid4(),
        component_id=comp_id,
        panel_key="p1",
        panel_label="Panel 1",
    )
    fake_items = [p1]
    fake_total = 1

    captured: dict = {}

    def fake_list(**kwargs):
        captured.update(kwargs)
        return fake_items, fake_total

    monkeypatch.setattr(component_panel_service, "list_component_panels", fake_list)

    resp: ComponentPanelListResponse = list_component_panels(
        tenant_id=tenant_id,
        component_id=comp_id,
        parent_panel_id=None,
        limit=50,
        offset=0,
        db=fake_db,
        current_user={"sub": "user", "tenant_id": str(tenant_id)},
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["component_id"] == comp_id
    assert captured["parent_panel_id"] is None
    assert captured["limit"] == 50
    assert captured["offset"] == 0

    assert resp.total == fake_total
    assert resp.items == fake_items
    assert resp.limit == 50
    assert resp.offset == 0


def test_create_component_panel_uses_current_user_sub_as_created_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    comp_id = uuid.uuid4()
    fake_db = DummySession()

    payload = ComponentPanelCreate(
        component_id=comp_id,
        parent_panel_id=None,
        panel_key="key",
        panel_label="Panel",
        ui_config=None,
        panel_order=0,
        created_by=None,
    )

    fake_panel = _fake_panel_out(
        tenant_id=tenant_id,
        component_panel_id=uuid.uuid4(),
        component_id=comp_id,
        panel_key=payload.panel_key,
        panel_label=payload.panel_label,
    )

    captured: dict = {}

    def fake_create(**kwargs):
        captured.update(kwargs)
        return fake_panel

    monkeypatch.setattr(component_panel_service, "create_component_panel", fake_create)

    result = create_component_panel(
        tenant_id=tenant_id,
        panel_in=payload,
        db=fake_db,
        current_user={"sub": "creator", "tenant_id": str(tenant_id)},
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["data"] == payload
    assert captured["created_by"] == "creator"
    assert result is fake_panel


def test_get_component_panel_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    panel_id = uuid.uuid4()
    comp_id = uuid.uuid4()
    fake_db = DummySession()

    fake_panel = _fake_panel_out(
        tenant_id=tenant_id,
        component_panel_id=panel_id,
        component_id=comp_id,
        panel_key="p",
        panel_label="Panel",
    )

    captured: dict = {}

    def fake_get(**kwargs):
        captured.update(kwargs)
        return fake_panel

    monkeypatch.setattr(component_panel_service, "get_component_panel", fake_get)

    result = get_component_panel(
        tenant_id=tenant_id,
        component_panel_id=panel_id,
        db=fake_db,
        current_user={"sub": "u", "tenant_id": str(tenant_id)},
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["component_panel_id"] == panel_id
    assert result is fake_panel


def test_update_component_panel_put_uses_current_user_sub_as_modified_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    panel_id = uuid.uuid4()
    comp_id = uuid.uuid4()
    fake_db = DummySession()

    payload = ComponentPanelUpdate(
        panel_label="Updated",
        updated_by=None,
    )

    fake_panel = _fake_panel_out(
        tenant_id=tenant_id,
        component_panel_id=panel_id,
        component_id=comp_id,
        panel_key="key",
        panel_label="Updated",
    )

    captured: dict = {}

    def fake_update(**kwargs):
        captured.update(kwargs)
        return fake_panel

    monkeypatch.setattr(component_panel_service, "update_component_panel", fake_update)

    result = update_component_panel(
        tenant_id=tenant_id,
        component_panel_id=panel_id,
        panel_in=payload,
        db=fake_db,
        current_user={"sub": "modifier", "tenant_id": str(tenant_id)},
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["component_panel_id"] == panel_id
    assert captured["data"] == payload
    assert captured["modified_by"] == "modifier"
    assert result is fake_panel


def test_delete_component_panel_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    panel_id = uuid.uuid4()
    fake_db = DummySession()

    called: dict = {}

    def fake_delete(**kwargs):
        called.update(kwargs)
        return None

    monkeypatch.setattr(component_panel_service, "delete_component_panel", fake_delete)

    result = delete_component_panel(
        tenant_id=tenant_id,
        component_panel_id=panel_id,
        db=fake_db,
        current_user={"sub": "deleter", "tenant_id": str(tenant_id)},
    )

    assert called["db"] is fake_db
    assert called["tenant_id"] == tenant_id
    assert called["component_panel_id"] == panel_id
    assert result is None