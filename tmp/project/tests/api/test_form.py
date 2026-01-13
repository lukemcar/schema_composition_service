"""
API tests for the Form domain.

The goal of these tests is to ensure that the Form endpoints forward
parameters correctly to the service layer and wrap list responses as
expected.  We don't hit the database or message bus here.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.form import (
    FormCreate,
    FormUpdate,
    FormOut,
    FormListResponse,
)
from app.domain.services import form_service

from app.api.routes.form import (
    list_forms,
    create_form,
    get_form,
    update_form,
    delete_form,
)


class DummySession(Session):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _fake_form_out(
    *,
    tenant_id: uuid.UUID,
    form_id: uuid.UUID,
    form_key: str,
    version: str,
    form_name: str,
) -> FormOut:
    now = _now()
    return FormOut(
        form_id=form_id,
        tenant_id=tenant_id,
        form_key=form_key,
        version=version,
        form_name=form_name,
        description=None,
        category_id=None,
        ui_config=None,
        is_active=True,
        is_published=False,
        created_by="tester",
        created_at=now,
        updated_at=now,
    )


def test_list_forms_calls_service_and_wraps_response(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fake_db = DummySession()

    f1 = _fake_form_out(
        tenant_id=tenant_id,
        form_id=uuid.uuid4(),
        form_key="form1",
        version="1.0",
        form_name="Form One",
    )
    fake_items = [f1]
    fake_total = 1

    captured: dict = {}

    def fake_list(**kwargs):
        captured.update(kwargs)
        return fake_items, fake_total

    monkeypatch.setattr(form_service, "list_forms", fake_list)

    resp: FormListResponse = list_forms(
        tenant_id=tenant_id,
        category_id=None,
        limit=20,
        offset=2,
        db=fake_db,
        current_user={"sub": "user", "tenant_id": str(tenant_id)},
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["category_id"] is None
    assert captured["limit"] == 20
    assert captured["offset"] == 2

    assert resp.total == fake_total
    assert resp.items == fake_items
    assert resp.limit == 20
    assert resp.offset == 2


def test_create_form_uses_current_user_sub_as_created_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fake_db = DummySession()

    payload = FormCreate(
        form_key="form",
        version="1.0",
        form_name="Form",
        description=None,
        category_id=None,
        ui_config=None,
        is_active=True,
        is_published=False,
        created_by=None,
    )

    fake_form = _fake_form_out(
        tenant_id=tenant_id,
        form_id=uuid.uuid4(),
        form_key=payload.form_key,
        version=payload.version,
        form_name=payload.form_name,
    )

    captured: dict = {}

    def fake_create(**kwargs):
        captured.update(kwargs)
        return fake_form

    monkeypatch.setattr(form_service, "create_form", fake_create)

    result = create_form(
        tenant_id=tenant_id,
        form_in=payload,
        db=fake_db,
        current_user={"sub": "creator", "tenant_id": str(tenant_id)},
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["data"] == payload
    assert captured["created_by"] == "creator"
    assert result is fake_form


def test_get_form_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    form_id = uuid.uuid4()
    fake_db = DummySession()

    fake_form = _fake_form_out(
        tenant_id=tenant_id,
        form_id=form_id,
        form_key="key",
        version="1.0",
        form_name="Name",
    )

    captured: dict = {}

    def fake_get(**kwargs):
        captured.update(kwargs)
        return fake_form

    monkeypatch.setattr(form_service, "get_form", fake_get)

    result = get_form(
        tenant_id=tenant_id,
        form_id=form_id,
        db=fake_db,
        current_user={"sub": "u", "tenant_id": str(tenant_id)},
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["form_id"] == form_id
    assert result is fake_form


def test_update_form_put_uses_current_user_sub_as_modified_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    form_id = uuid.uuid4()
    fake_db = DummySession()

    payload = FormUpdate(
        form_name="Updated",
        updated_by=None,
    )

    fake_form = _fake_form_out(
        tenant_id=tenant_id,
        form_id=form_id,
        form_key="key",
        version="1.0",
        form_name="Updated",
    )

    captured: dict = {}

    def fake_update(**kwargs):
        captured.update(kwargs)
        return fake_form

    monkeypatch.setattr(form_service, "update_form", fake_update)

    result = update_form(
        tenant_id=tenant_id,
        form_id=form_id,
        form_in=payload,
        db=fake_db,
        current_user={"sub": "mod", "tenant_id": str(tenant_id)},
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["form_id"] == form_id
    assert captured["data"] == payload
    assert captured["modified_by"] == "mod"
    assert result is fake_form


def test_delete_form_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    form_id = uuid.uuid4()
    fake_db = DummySession()

    called: dict = {}

    def fake_delete(**kwargs):
        called.update(kwargs)
        return None

    monkeypatch.setattr(form_service, "delete_form", fake_delete)

    result = delete_form(
        tenant_id=tenant_id,
        form_id=form_id,
        db=fake_db,
        current_user={"sub": "deleter", "tenant_id": str(tenant_id)},
    )

    assert called["db"] is fake_db
    assert called["tenant_id"] == tenant_id
    assert called["form_id"] == form_id
    assert result is None