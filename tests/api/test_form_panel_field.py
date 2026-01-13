"""
API tests for the FormPanelField domain.

These tests verify that form panel field routes properly delegate to
the service functions and wrap responses with pagination data.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, Any

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.form_panel_field import (
    FormPanelFieldCreate,
    FormPanelFieldUpdate,
    FormPanelFieldOut,
    FormPanelFieldListResponse,
)
from app.domain.services import form_panel_field_service

from app.api.routes.form_panel_field import (
    list_form_panel_fields,
    create_form_panel_field,
    get_form_panel_field,
    update_form_panel_field,
    delete_form_panel_field,
)


class DummySession(Session):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _fake_fpf_out(
    *,
    tenant_id: uuid.UUID,
    form_panel_field_id: uuid.UUID,
    form_panel_id: uuid.UUID,
    field_def_id: uuid.UUID,
    overrides: Dict[str, Any] | None = None,
    field_order: int = 0,
    is_required: bool = False,
) -> FormPanelFieldOut:
    now = _now()
    return FormPanelFieldOut(
        form_panel_field_id=form_panel_field_id,
        tenant_id=tenant_id,
        form_panel_id=form_panel_id,
        field_def_id=field_def_id,
        overrides=overrides,
        field_order=field_order,
        is_required=is_required,
        created_by="tester",
        created_at=now,
        updated_at=now,
    )


def test_list_form_panel_fields_calls_service_and_wraps_response(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fp_id = uuid.uuid4()
    field_id = uuid.uuid4()
    fake_db = DummySession()

    fpf = _fake_fpf_out(
        tenant_id=tenant_id,
        form_panel_field_id=uuid.uuid4(),
        form_panel_id=fp_id,
        field_def_id=field_id,
        overrides=None,
        field_order=1,
        is_required=True,
    )
    fake_items = [fpf]
    fake_total = 1

    captured: dict = {}

    def fake_list(**kwargs):
        captured.update(kwargs)
        return fake_items, fake_total

    monkeypatch.setattr(form_panel_field_service, "list_form_panel_fields", fake_list)

    resp: FormPanelFieldListResponse = list_form_panel_fields(
        tenant_id=tenant_id,
        form_panel_id=fp_id,
        field_def_id=field_id,
        limit=50,
        offset=0,
        db=fake_db,
        current_user={"sub": "u", "tenant_id": str(tenant_id)},
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["form_panel_id"] == fp_id
    assert captured["field_def_id"] == field_id
    assert captured["limit"] == 50
    assert captured["offset"] == 0

    assert resp.total == fake_total
    assert resp.items == fake_items
    assert resp.limit == 50
    assert resp.offset == 0


def test_create_form_panel_field_uses_current_user_sub_as_created_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fp_id = uuid.uuid4()
    field_id = uuid.uuid4()
    fake_db = DummySession()

    payload = FormPanelFieldCreate(
        form_panel_id=fp_id,
        field_def_id=field_id,
        overrides={"o": 1},
        field_order=0,
        is_required=False,
        created_by=None,
    )

    fake_fpf = _fake_fpf_out(
        tenant_id=tenant_id,
        form_panel_field_id=uuid.uuid4(),
        form_panel_id=fp_id,
        field_def_id=field_id,
        overrides={"o": 1},
        field_order=0,
        is_required=False,
    )

    captured: dict = {}

    def fake_create(**kwargs):
        captured.update(kwargs)
        return fake_fpf

    monkeypatch.setattr(form_panel_field_service, "create_form_panel_field", fake_create)

    result = create_form_panel_field(
        tenant_id=tenant_id,
        panel_field_in=payload,
        db=fake_db,
        current_user={"sub": "creator", "tenant_id": str(tenant_id)},
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["data"] == payload
    assert captured["created_by"] == "creator"
    assert result is fake_fpf


def test_get_form_panel_field_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fpf_id = uuid.uuid4()
    fp_id = uuid.uuid4()
    field_id = uuid.uuid4()
    fake_db = DummySession()

    fake_fpf = _fake_fpf_out(
        tenant_id=tenant_id,
        form_panel_field_id=fpf_id,
        form_panel_id=fp_id,
        field_def_id=field_id,
    )

    captured: dict = {}

    def fake_get(**kwargs):
        captured.update(kwargs)
        return fake_fpf

    monkeypatch.setattr(form_panel_field_service, "get_form_panel_field", fake_get)

    result = get_form_panel_field(
        tenant_id=tenant_id,
        form_panel_field_id=fpf_id,
        db=fake_db,
        current_user={"sub": "u", "tenant_id": str(tenant_id)},
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["form_panel_field_id"] == fpf_id
    assert result is fake_fpf


def test_update_form_panel_field_put_uses_current_user_sub_as_modified_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fpf_id = uuid.uuid4()
    fp_id = uuid.uuid4()
    field_id = uuid.uuid4()
    fake_db = DummySession()

    payload = FormPanelFieldUpdate(
        overrides={"x": 2},
        updated_by=None,
    )

    fake_fpf = _fake_fpf_out(
        tenant_id=tenant_id,
        form_panel_field_id=fpf_id,
        form_panel_id=fp_id,
        field_def_id=field_id,
        overrides={"x": 2},
        field_order=0,
        is_required=False,
    )

    captured: dict = {}

    def fake_update(**kwargs):
        captured.update(kwargs)
        return fake_fpf

    monkeypatch.setattr(form_panel_field_service, "update_form_panel_field", fake_update)

    result = update_form_panel_field(
        tenant_id=tenant_id,
        form_panel_field_id=fpf_id,
        panel_field_in=payload,
        db=fake_db,
        current_user={"sub": "mod", "tenant_id": str(tenant_id)},
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["form_panel_field_id"] == fpf_id
    assert captured["data"] == payload
    assert captured["modified_by"] == "mod"
    assert result is fake_fpf


def test_delete_form_panel_field_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fpf_id = uuid.uuid4()
    fake_db = DummySession()

    called: dict = {}

    def fake_delete(**kwargs):
        called.update(kwargs)
        return None

    monkeypatch.setattr(form_panel_field_service, "delete_form_panel_field", fake_delete)

    result = delete_form_panel_field(
        tenant_id=tenant_id,
        form_panel_field_id=fpf_id,
        db=fake_db,
        current_user={"sub": "del", "tenant_id": str(tenant_id)},
    )

    assert called["db"] is fake_db
    assert called["tenant_id"] == tenant_id
    assert called["form_panel_field_id"] == fpf_id
    assert result is None