"""
API tests for the ComponentPanelField domain.

These tests validate that the component panel field routes delegate
operations to the service layer with the correct arguments and return
the responses unchanged.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, Any

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.component_panel_field import (
    ComponentPanelFieldCreate,
    ComponentPanelFieldUpdate,
    ComponentPanelFieldOut,
    ComponentPanelFieldListResponse,
)
from app.domain.services import component_panel_field_service

from app.api.routes.component_panel_field import (
    list_component_panel_fields,
    create_component_panel_field,
    get_component_panel_field,
    update_component_panel_field,
    delete_component_panel_field,
)


class DummySession(Session):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _fake_cpf_out(
    *,
    tenant_id: uuid.UUID,
    component_panel_field_id: uuid.UUID,
    component_panel_id: uuid.UUID,
    field_def_id: uuid.UUID,
    overrides: Dict[str, Any] | None = None,
    field_order: int = 0,
    is_required: bool = False,
) -> ComponentPanelFieldOut:
    now = _now()
    return ComponentPanelFieldOut(
        component_panel_field_id=component_panel_field_id,
        tenant_id=tenant_id,
        component_panel_id=component_panel_id,
        field_def_id=field_def_id,
        overrides=overrides,
        field_order=field_order,
        is_required=is_required,
        created_by="tester",
        created_at=now,
        updated_at=now,
    )


def test_list_component_panel_fields_calls_service_and_wraps_response(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    panel_id = uuid.uuid4()
    field_id = uuid.uuid4()
    fake_db = DummySession()

    cpf = _fake_cpf_out(
        tenant_id=tenant_id,
        component_panel_field_id=uuid.uuid4(),
        component_panel_id=panel_id,
        field_def_id=field_id,
        overrides=None,
        field_order=1,
        is_required=True,
    )
    fake_items = [cpf]
    fake_total = 1

    captured: dict = {}

    def fake_list(**kwargs):
        captured.update(kwargs)
        return fake_items, fake_total

    monkeypatch.setattr(component_panel_field_service, "list_component_panel_fields", fake_list)

    resp: ComponentPanelFieldListResponse = list_component_panel_fields(
        tenant_id=tenant_id,
        component_panel_id=panel_id,
        field_def_id=field_id,
        limit=25,
        offset=0,
        db=fake_db,
        current_user={"sub": "user", "tenant_id": str(tenant_id)},
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["component_panel_id"] == panel_id
    assert captured["field_def_id"] == field_id
    assert captured["limit"] == 25
    assert captured["offset"] == 0

    assert resp.total == fake_total
    assert resp.items == fake_items
    assert resp.limit == 25
    assert resp.offset == 0


def test_create_component_panel_field_uses_current_user_sub_as_created_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    panel_id = uuid.uuid4()
    field_id = uuid.uuid4()
    fake_db = DummySession()

    payload = ComponentPanelFieldCreate(
        component_panel_id=panel_id,
        field_def_id=field_id,
        overrides={"x": "y"},
        field_order=0,
        is_required=False,
        created_by=None,
    )

    fake_cpf = _fake_cpf_out(
        tenant_id=tenant_id,
        component_panel_field_id=uuid.uuid4(),
        component_panel_id=panel_id,
        field_def_id=field_id,
        overrides={"x": "y"},
        field_order=0,
        is_required=False,
    )

    captured: dict = {}

    def fake_create(**kwargs):
        captured.update(kwargs)
        return fake_cpf

    monkeypatch.setattr(component_panel_field_service, "create_component_panel_field", fake_create)

    result = create_component_panel_field(
        tenant_id=tenant_id,
        panel_field_in=payload,
        db=fake_db,
        current_user={"sub": "creator", "tenant_id": str(tenant_id)},
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["data"] == payload
    assert captured["created_by"] == "creator"
    assert result is fake_cpf


def test_get_component_panel_field_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    cpf_id = uuid.uuid4()
    panel_id = uuid.uuid4()
    field_id = uuid.uuid4()
    fake_db = DummySession()

    fake_cpf = _fake_cpf_out(
        tenant_id=tenant_id,
        component_panel_field_id=cpf_id,
        component_panel_id=panel_id,
        field_def_id=field_id,
        overrides=None,
    )

    captured: dict = {}

    def fake_get(**kwargs):
        captured.update(kwargs)
        return fake_cpf

    monkeypatch.setattr(component_panel_field_service, "get_component_panel_field", fake_get)

    result = get_component_panel_field(
        tenant_id=tenant_id,
        component_panel_field_id=cpf_id,
        db=fake_db,
        current_user={"sub": "u", "tenant_id": str(tenant_id)},
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["component_panel_field_id"] == cpf_id
    assert result is fake_cpf


def test_update_component_panel_field_put_uses_current_user_sub_as_modified_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    cpf_id = uuid.uuid4()
    panel_id = uuid.uuid4()
    field_id = uuid.uuid4()
    fake_db = DummySession()

    payload = ComponentPanelFieldUpdate(
        overrides={"a": "b"},
        updated_by=None,
    )

    fake_cpf = _fake_cpf_out(
        tenant_id=tenant_id,
        component_panel_field_id=cpf_id,
        component_panel_id=panel_id,
        field_def_id=field_id,
        overrides={"a": "b"},
        field_order=0,
        is_required=False,
    )

    captured: dict = {}

    def fake_update(**kwargs):
        captured.update(kwargs)
        return fake_cpf

    monkeypatch.setattr(component_panel_field_service, "update_component_panel_field", fake_update)

    result = update_component_panel_field(
        tenant_id=tenant_id,
        component_panel_field_id=cpf_id,
        panel_field_in=payload,
        db=fake_db,
        current_user={"sub": "mod", "tenant_id": str(tenant_id)},
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["component_panel_field_id"] == cpf_id
    assert captured["data"] == payload
    assert captured["modified_by"] == "mod"
    assert result is fake_cpf


def test_delete_component_panel_field_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    cpf_id = uuid.uuid4()
    fake_db = DummySession()

    called: dict = {}

    def fake_delete(**kwargs):
        called.update(kwargs)
        return None

    monkeypatch.setattr(component_panel_field_service, "delete_component_panel_field", fake_delete)

    result = delete_component_panel_field(
        tenant_id=tenant_id,
        component_panel_field_id=cpf_id,
        db=fake_db,
        current_user={"sub": "del", "tenant_id": str(tenant_id)},
    )

    assert called["db"] is fake_db
    assert called["tenant_id"] == tenant_id
    assert called["component_panel_field_id"] == cpf_id
    assert result is None