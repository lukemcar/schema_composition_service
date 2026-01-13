"""
API tests for the FormSubmissionValue domain.

These tests ensure that the form submission value endpoints correctly
delegate to the service layer and wrap paginated responses.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, Any

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.form_submission_value import (
    FormSubmissionValueCreate,
    FormSubmissionValueUpdate,
    FormSubmissionValueOut,
    FormSubmissionValueListResponse,
)
from app.domain.services import form_submission_value_service

from app.api.routes.form_submission_value import (
    list_form_submission_values,
    create_form_submission_value,
    get_form_submission_value,
    update_form_submission_value,
    delete_form_submission_value,
)


class DummySession(Session):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _fake_fsv_out(
    *,
    tenant_id: uuid.UUID,
    form_submission_value_id: uuid.UUID,
    form_submission_id: uuid.UUID,
    field_instance_path: str,
    value: Dict[str, Any] | None = None,
) -> FormSubmissionValueOut:
    now = _now()
    return FormSubmissionValueOut(
        form_submission_value_id=form_submission_value_id,
        tenant_id=tenant_id,
        form_submission_id=form_submission_id,
        field_instance_path=field_instance_path,
        value=value,
        created_by="tester",
        created_at=now,
        updated_at=now,
    )


def test_list_form_submission_values_calls_service_and_wraps_response(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fs_id = uuid.uuid4()
    fake_db = DummySession()

    fsv = _fake_fsv_out(
        tenant_id=tenant_id,
        form_submission_value_id=uuid.uuid4(),
        form_submission_id=fs_id,
        field_instance_path="/field",  # sample path
        value={"v": 1},
    )
    fake_items = [fsv]
    fake_total = 1

    captured: dict = {}

    def fake_list(**kwargs):
        captured.update(kwargs)
        return fake_items, fake_total

    monkeypatch.setattr(form_submission_value_service, "list_form_submission_values", fake_list)

    resp: FormSubmissionValueListResponse = list_form_submission_values(
        tenant_id=tenant_id,
        form_submission_id=fs_id,
        field_instance_path="/field",
        limit=10,
        offset=0,
        db=fake_db,
        current_user={"sub": "u", "tenant_id": str(tenant_id)},
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["form_submission_id"] == fs_id
    assert captured["field_instance_path"] == "/field"
    assert captured["limit"] == 10
    assert captured["offset"] == 0

    assert resp.total == fake_total
    assert resp.items == fake_items
    assert resp.limit == 10
    assert resp.offset == 0


def test_create_form_submission_value_uses_current_user_sub_as_created_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fs_id = uuid.uuid4()
    fake_db = DummySession()

    payload = FormSubmissionValueCreate(
        form_submission_id=fs_id,
        field_instance_path="/field",
        value={"x": 1},
        created_by=None,
    )

    fake_fsv = _fake_fsv_out(
        tenant_id=tenant_id,
        form_submission_value_id=uuid.uuid4(),
        form_submission_id=fs_id,
        field_instance_path=payload.field_instance_path,
        value=payload.value,
    )

    captured: dict = {}

    def fake_create(**kwargs):
        captured.update(kwargs)
        return fake_fsv

    monkeypatch.setattr(form_submission_value_service, "create_form_submission_value", fake_create)

    result = create_form_submission_value(
        tenant_id=tenant_id,
        submission_value_in=payload,
        db=fake_db,
        current_user={"sub": "creator", "tenant_id": str(tenant_id)},
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["data"] == payload
    assert captured["created_by"] == "creator"
    assert result is fake_fsv


def test_get_form_submission_value_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fsv_id = uuid.uuid4()
    fs_id = uuid.uuid4()
    fake_db = DummySession()

    fake_fsv = _fake_fsv_out(
        tenant_id=tenant_id,
        form_submission_value_id=fsv_id,
        form_submission_id=fs_id,
        field_instance_path="/path",
        value=None,
    )

    captured: dict = {}

    def fake_get(**kwargs):
        captured.update(kwargs)
        return fake_fsv

    monkeypatch.setattr(form_submission_value_service, "get_form_submission_value", fake_get)

    result = get_form_submission_value(
        tenant_id=tenant_id,
        form_submission_value_id=fsv_id,
        db=fake_db,
        current_user={"sub": "user", "tenant_id": str(tenant_id)},
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["form_submission_value_id"] == fsv_id
    assert result is fake_fsv


def test_update_form_submission_value_put_uses_current_user_sub_as_modified_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fsv_id = uuid.uuid4()
    fs_id = uuid.uuid4()
    fake_db = DummySession()

    payload = FormSubmissionValueUpdate(
        field_instance_path="/new",
        value={"y": 2},
        updated_by=None,
    )

    fake_fsv = _fake_fsv_out(
        tenant_id=tenant_id,
        form_submission_value_id=fsv_id,
        form_submission_id=fs_id,
        field_instance_path="/new",
        value={"y": 2},
    )

    captured: dict = {}

    def fake_update(**kwargs):
        captured.update(kwargs)
        return fake_fsv

    monkeypatch.setattr(form_submission_value_service, "update_form_submission_value", fake_update)

    result = update_form_submission_value(
        tenant_id=tenant_id,
        form_submission_value_id=fsv_id,
        submission_value_in=payload,
        db=fake_db,
        current_user={"sub": "mod", "tenant_id": str(tenant_id)},
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["form_submission_value_id"] == fsv_id
    assert captured["data"] == payload
    assert captured["modified_by"] == "mod"
    assert result is fake_fsv


def test_delete_form_submission_value_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fsv_id = uuid.uuid4()
    fake_db = DummySession()

    called: dict = {}

    def fake_delete(**kwargs):
        called.update(kwargs)
        return None

    monkeypatch.setattr(form_submission_value_service, "delete_form_submission_value", fake_delete)

    result = delete_form_submission_value(
        tenant_id=tenant_id,
        form_submission_value_id=fsv_id,
        db=fake_db,
        current_user={"sub": "del", "tenant_id": str(tenant_id)},
    )

    assert called["db"] is fake_db
    assert called["tenant_id"] == tenant_id
    assert called["form_submission_value_id"] == fsv_id
    assert result is None