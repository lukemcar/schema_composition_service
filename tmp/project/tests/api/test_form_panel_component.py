"""
API tests for the FormPanelComponent domain.

These tests ensure that the form panel component routes pass
parameters correctly to the service layer and wrap responses
appropriately.  Only the routing logic is verified.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.form_panel_component import (
    FormPanelComponentCreate,
    FormPanelComponentUpdate,
    FormPanelComponentOut,
    FormPanelComponentListResponse,
)
from app.domain.services import form_panel_component_service

from app.api.routes.form_panel_component import (
    list_form_panel_components,
    create_form_panel_component,
    get_form_panel_component,
    update_form_panel_component,
    delete_form_panel_component,
)


class DummySession(Session):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _fake_fpc_out(
    *,
    tenant_id: uuid.UUID,
    form_panel_component_id: uuid.UUID,
    form_panel_id: uuid.UUID,
    component_id: uuid.UUID,
    config: dict | None = None,
    component_order: int = 0,
) -> FormPanelComponentOut:
    now = _now()
    return FormPanelComponentOut(
        form_panel_component_id=form_panel_component_id,
        tenant_id=tenant_id,
        form_panel_id=form_panel_id,
        component_id=component_id,
        config=config,
        component_order=component_order,
        created_by="tester",
        created_at=now,
        updated_at=now,
    )


def test_list_form_panel_components_calls_service_and_wraps_response(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    form_panel_id = uuid.uuid4()
    fake_db = DummySession()

    fpc = _fake_fpc_out(
        tenant_id=tenant_id,
        form_panel_component_id=uuid.uuid4(),
        form_panel_id=form_panel_id,
        component_id=uuid.uuid4(),
        config=None,
        component_order=1,
    )
    fake_items = [fpc]
    fake_total = 1

    captured: dict = {}

    def fake_list(**kwargs):
        captured.update(kwargs)
        return fake_items, fake_total

    monkeypatch.setattr(form_panel_component_service, "list_form_panel_components", fake_list)

    resp: FormPanelComponentListResponse = list_form_panel_components(
        tenant_id=tenant_id,
        form_panel_id=form_panel_id,
        component_id=None,
        limit=10,
        offset=0,
        db=fake_db,
        current_user={"sub": "u", "tenant_id": str(tenant_id)},
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["form_panel_id"] == form_panel_id
    assert captured["component_id"] is None
    assert captured["limit"] == 10
    assert captured["offset"] == 0

    assert resp.total == fake_total
    assert resp.items == fake_items
    assert resp.limit == 10
    assert resp.offset == 0


def test_create_form_panel_component_uses_current_user_sub_as_created_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fp_id = uuid.uuid4()
    comp_id = uuid.uuid4()
    fake_db = DummySession()

    payload = FormPanelComponentCreate(
        form_panel_id=fp_id,
        component_id=comp_id,
        config=None,
        component_order=0,
        created_by=None,
    )

    fake_fpc = _fake_fpc_out(
        tenant_id=tenant_id,
        form_panel_component_id=uuid.uuid4(),
        form_panel_id=fp_id,
        component_id=comp_id,
        config=None,
        component_order=0,
    )

    captured: dict = {}

    def fake_create(**kwargs):
        captured.update(kwargs)
        return fake_fpc

    monkeypatch.setattr(form_panel_component_service, "create_form_panel_component", fake_create)

    result = create_form_panel_component(
        tenant_id=tenant_id,
        panel_component_in=payload,
        db=fake_db,
        current_user={"sub": "creator", "tenant_id": str(tenant_id)},
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["data"] == payload
    assert captured["created_by"] == "creator"
    assert result is fake_fpc


def test_get_form_panel_component_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fpc_id = uuid.uuid4()
    fp_id = uuid.uuid4()
    comp_id = uuid.uuid4()
    fake_db = DummySession()

    fake_fpc = _fake_fpc_out(
        tenant_id=tenant_id,
        form_panel_component_id=fpc_id,
        form_panel_id=fp_id,
        component_id=comp_id,
    )

    captured: dict = {}

    def fake_get(**kwargs):
        captured.update(kwargs)
        return fake_fpc

    monkeypatch.setattr(form_panel_component_service, "get_form_panel_component", fake_get)

    result = get_form_panel_component(
        tenant_id=tenant_id,
        form_panel_component_id=fpc_id,
        db=fake_db,
        current_user={"sub": "u", "tenant_id": str(tenant_id)},
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["form_panel_component_id"] == fpc_id
    assert result is fake_fpc


def test_update_form_panel_component_put_uses_current_user_sub_as_modified_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fpc_id = uuid.uuid4()
    fp_id = uuid.uuid4()
    comp_id = uuid.uuid4()
    fake_db = DummySession()

    payload = FormPanelComponentUpdate(
        config={"a": 1},
        updated_by=None,
    )

    fake_fpc = _fake_fpc_out(
        tenant_id=tenant_id,
        form_panel_component_id=fpc_id,
        form_panel_id=fp_id,
        component_id=comp_id,
        config={"a": 1},
        component_order=0,
    )

    captured: dict = {}

    def fake_update(**kwargs):
        captured.update(kwargs)
        return fake_fpc

    monkeypatch.setattr(form_panel_component_service, "update_form_panel_component", fake_update)

    result = update_form_panel_component(
        tenant_id=tenant_id,
        form_panel_component_id=fpc_id,
        panel_component_in=payload,
        db=fake_db,
        current_user={"sub": "mod", "tenant_id": str(tenant_id)},
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["form_panel_component_id"] == fpc_id
    assert captured["data"] == payload
    assert captured["modified_by"] == "mod"
    assert result is fake_fpc


def test_delete_form_panel_component_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fpc_id = uuid.uuid4()
    fake_db = DummySession()

    called: dict = {}

    def fake_delete(**kwargs):
        called.update(kwargs)
        return None

    monkeypatch.setattr(form_panel_component_service, "delete_form_panel_component", fake_delete)

    result = delete_form_panel_component(
        tenant_id=tenant_id,
        form_panel_component_id=fpc_id,
        db=fake_db,
        current_user={"sub": "del", "tenant_id": str(tenant_id)},
    )

    assert called["db"] is fake_db
    assert called["tenant_id"] == tenant_id
    assert called["form_panel_component_id"] == fpc_id
    assert result is None