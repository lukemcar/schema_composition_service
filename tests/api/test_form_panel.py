"""
API tests for the FormPanel domain.

These tests ensure that the FormPanel routes delegate to the service
layer with the correct parameters and wrap list responses.  They do
not exercise persistence or event publication.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.form_panel import (
    FormPanelCreate,
    FormPanelUpdate,
    FormPanelOut,
    FormPanelListResponse,
)
from app.domain.services import form_panel_service

from app.api.routes.form_panel import (
    list_form_panels,
    create_form_panel,
    get_form_panel,
    update_form_panel,
    delete_form_panel,
)


class DummySession(Session):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _fake_form_panel_out(
    *,
    tenant_id: uuid.UUID,
    form_panel_id: uuid.UUID,
    form_id: uuid.UUID,
    panel_key: str,
    panel_label: str = "",
    parent_panel_id: uuid.UUID | None = None,
) -> FormPanelOut:
    now = _now()
    return FormPanelOut(
        form_panel_id=form_panel_id,
        tenant_id=tenant_id,
        form_id=form_id,
        parent_panel_id=parent_panel_id,
        panel_key=panel_key,
        panel_label=panel_label,
        ui_config=None,
        panel_order=0,
        created_by="tester",
        created_at=now,
        updated_at=now,
    )


def test_list_form_panels_calls_service_and_wraps_response(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    form_id = uuid.uuid4()
    fake_db = DummySession()

    fp = _fake_form_panel_out(
        tenant_id=tenant_id,
        form_panel_id=uuid.uuid4(),
        form_id=form_id,
        panel_key="p1",
        panel_label="Panel 1",
    )
    fake_items = [fp]
    fake_total = 1

    captured: dict = {}

    def fake_list(**kwargs):
        captured.update(kwargs)
        return fake_items, fake_total

    monkeypatch.setattr(form_panel_service, "list_form_panels", fake_list)

    resp: FormPanelListResponse = list_form_panels(
        tenant_id=tenant_id,
        form_id=form_id,
        parent_panel_id=None,
        limit=50,
        offset=0,
        db=fake_db,
        current_user={"sub": "user", "tenant_id": str(tenant_id)},
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["form_id"] == form_id
    assert captured["parent_panel_id"] is None
    assert captured["limit"] == 50
    assert captured["offset"] == 0

    assert resp.total == fake_total
    assert resp.items == fake_items
    assert resp.limit == 50
    assert resp.offset == 0


def test_create_form_panel_uses_current_user_sub_as_created_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    form_id = uuid.uuid4()
    fake_db = DummySession()

    payload = FormPanelCreate(
        form_id=form_id,
        parent_panel_id=None,
        panel_key="key",
        panel_label="Panel",
        ui_config=None,
        panel_order=0,
        created_by=None,
    )

    fake_fp = _fake_form_panel_out(
        tenant_id=tenant_id,
        form_panel_id=uuid.uuid4(),
        form_id=form_id,
        panel_key=payload.panel_key,
        panel_label=payload.panel_label,
    )

    captured: dict = {}

    def fake_create(**kwargs):
        captured.update(kwargs)
        return fake_fp

    monkeypatch.setattr(form_panel_service, "create_form_panel", fake_create)

    result = create_form_panel(
        tenant_id=tenant_id,
        panel_in=payload,
        db=fake_db,
        current_user={"sub": "creator", "tenant_id": str(tenant_id)},
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["data"] == payload
    assert captured["created_by"] == "creator"
    assert result is fake_fp


def test_get_form_panel_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fp_id = uuid.uuid4()
    form_id = uuid.uuid4()
    fake_db = DummySession()

    fake_fp = _fake_form_panel_out(
        tenant_id=tenant_id,
        form_panel_id=fp_id,
        form_id=form_id,
        panel_key="key",
        panel_label="Panel",
    )

    captured: dict = {}

    def fake_get(**kwargs):
        captured.update(kwargs)
        return fake_fp

    monkeypatch.setattr(form_panel_service, "get_form_panel", fake_get)

    result = get_form_panel(
        tenant_id=tenant_id,
        form_panel_id=fp_id,
        db=fake_db,
        current_user={"sub": "u", "tenant_id": str(tenant_id)},
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["form_panel_id"] == fp_id
    assert result is fake_fp


def test_update_form_panel_put_uses_current_user_sub_as_modified_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fp_id = uuid.uuid4()
    form_id = uuid.uuid4()
    fake_db = DummySession()

    payload = FormPanelUpdate(
        panel_label="Updated",
        updated_by=None,
    )

    fake_fp = _fake_form_panel_out(
        tenant_id=tenant_id,
        form_panel_id=fp_id,
        form_id=form_id,
        panel_key="key",
        panel_label="Updated",
    )

    captured: dict = {}

    def fake_update(**kwargs):
        captured.update(kwargs)
        return fake_fp

    monkeypatch.setattr(form_panel_service, "update_form_panel", fake_update)

    result = update_form_panel(
        tenant_id=tenant_id,
        form_panel_id=fp_id,
        panel_in=payload,
        db=fake_db,
        current_user={"sub": "modifier", "tenant_id": str(tenant_id)},
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["form_panel_id"] == fp_id
    assert captured["data"] == payload
    assert captured["modified_by"] == "modifier"
    assert result is fake_fp


def test_delete_form_panel_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fp_id = uuid.uuid4()
    fake_db = DummySession()

    called: dict = {}

    def fake_delete(**kwargs):
        called.update(kwargs)
        return None

    monkeypatch.setattr(form_panel_service, "delete_form_panel", fake_delete)

    result = delete_form_panel(
        tenant_id=tenant_id,
        form_panel_id=fp_id,
        db=fake_db,
        current_user={"sub": "del", "tenant_id": str(tenant_id)},
    )

    assert called["db"] is fake_db
    assert called["tenant_id"] == tenant_id
    assert called["form_panel_id"] == fp_id
    assert result is None