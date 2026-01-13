"""
API tests for the Component domain.

These tests verify that the component routes defined in
``app/api/routes/component.py`` properly interact with the component
service layer.  Each test ensures that the correct arguments are
forwarded and that responses are returned unchanged.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.component import (
    ComponentCreate,
    ComponentUpdate,
    ComponentOut,
    ComponentListResponse,
)
from app.domain.services import component_service

from app.api.routes.component import (
    list_components,
    create_component,
    get_component,
    update_component,
    delete_component,
)


class DummySession(Session):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _fake_component_out(
    *,
    tenant_id: uuid.UUID,
    component_id: uuid.UUID,
    component_key: str,
    version: str,
    component_name: str,
) -> ComponentOut:
    now = _now()
    return ComponentOut(
        component_id=component_id,
        tenant_id=tenant_id,
        component_key=component_key,
        version=version,
        component_name=component_name,
        description=None,
        category_id=None,
        ui_config=None,
        is_active=True,
        created_by="tester",
        created_at=now,
        updated_at=now,
    )


def test_list_components_calls_service_and_wraps_response(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fake_db = DummySession()

    c1 = _fake_component_out(
        tenant_id=tenant_id,
        component_id=uuid.uuid4(),
        component_key="comp1",
        version="1.0",
        component_name="Component One",
    )
    fake_items = [c1]
    fake_total = 1

    captured: dict = {}

    def fake_list(**kwargs):
        captured.update(kwargs)
        return fake_items, fake_total

    monkeypatch.setattr(component_service, "list_components", fake_list)

    resp: ComponentListResponse = list_components(
        tenant_id=tenant_id,
        limit=10,
        offset=5,
        db=fake_db,
        current_user={"sub": "user", "tenant_id": str(tenant_id)},
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["limit"] == 10
    assert captured["offset"] == 5

    assert resp.total == fake_total
    assert resp.items == fake_items
    assert resp.limit == 10
    assert resp.offset == 5


def test_create_component_uses_current_user_sub_as_created_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fake_db = DummySession()

    payload = ComponentCreate(
        component_key="comp",
        version="1.0",
        component_name="Comp",
        description=None,
        category_id=None,
        ui_config=None,
        is_active=True,
        created_by=None,
    )

    fake_component = _fake_component_out(
        tenant_id=tenant_id,
        component_id=uuid.uuid4(),
        component_key=payload.component_key,
        version=payload.version,
        component_name=payload.component_name,
    )

    captured: dict = {}

    def fake_create(**kwargs):
        captured.update(kwargs)
        return fake_component

    monkeypatch.setattr(component_service, "create_component", fake_create)

    current_user = {"sub": "creator", "tenant_id": str(tenant_id)}

    result = create_component(
        tenant_id=tenant_id,
        component_in=payload,
        db=fake_db,
        current_user=current_user,
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["data"] == payload
    assert captured["created_by"] == "creator"
    assert result is fake_component


def test_get_component_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    comp_id = uuid.uuid4()
    fake_db = DummySession()

    fake_component = _fake_component_out(
        tenant_id=tenant_id,
        component_id=comp_id,
        component_key="k",
        version="1.0",
        component_name="Name",
    )

    captured: dict = {}

    def fake_get(**kwargs):
        captured.update(kwargs)
        return fake_component

    monkeypatch.setattr(component_service, "get_component", fake_get)

    result = get_component(
        tenant_id=tenant_id,
        component_id=comp_id,
        db=fake_db,
        current_user={"sub": "u", "tenant_id": str(tenant_id)},
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["component_id"] == comp_id
    assert result is fake_component


def test_update_component_put_uses_current_user_sub_as_modified_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    comp_id = uuid.uuid4()
    fake_db = DummySession()

    payload = ComponentUpdate(
        component_name="Updated",
        updated_by=None,
    )

    fake_component = _fake_component_out(
        tenant_id=tenant_id,
        component_id=comp_id,
        component_key="comp",
        version="1.0",
        component_name="Updated",
    )

    captured: dict = {}

    def fake_update(**kwargs):
        captured.update(kwargs)
        return fake_component

    monkeypatch.setattr(component_service, "update_component", fake_update)

    result = update_component(
        tenant_id=tenant_id,
        component_id=comp_id,
        component_in=payload,
        db=fake_db,
        current_user={"sub": "modifier", "tenant_id": str(tenant_id)},
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["component_id"] == comp_id
    assert captured["data"] == payload
    assert captured["modified_by"] == "modifier"
    assert result is fake_component


def test_delete_component_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    comp_id = uuid.uuid4()
    fake_db = DummySession()

    called: dict = {}

    def fake_delete(**kwargs):
        called.update(kwargs)
        return None

    monkeypatch.setattr(component_service, "delete_component", fake_delete)

    result = delete_component(
        tenant_id=tenant_id,
        component_id=comp_id,
        db=fake_db,
        current_user={"sub": "deleter", "tenant_id": str(tenant_id)},
    )

    assert called["db"] is fake_db
    assert called["tenant_id"] == tenant_id
    assert called["component_id"] == comp_id
    assert result is None