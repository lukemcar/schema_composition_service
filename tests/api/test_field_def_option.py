"""
API tests for the FieldDefOption domain.

These tests verify that the route functions defined in
``app/api/routes/field_def_option.py`` correctly delegate work to the
service layer and wrap responses as expected.  They do not exercise
database or messaging behaviour, only the wiring between FastAPI
endpoints and the underlying service functions.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.field_def_option import (
    FieldDefOptionCreate,
    FieldDefOptionUpdate,
    FieldDefOptionOut,
    FieldDefOptionListResponse,
)
from app.domain.services import field_def_option_service as option_service

from app.api.routes.field_def_option import (
    list_field_def_options,
    create_field_def_option,
    get_field_def_option,
    update_field_def_option,
    delete_field_def_option,
)


class DummySession(Session):
    """Lightweight stand‑in so type hints are happy without a real DB."""

    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _fake_option_out(
    *,
    tenant_id: uuid.UUID,
    field_def_option_id: uuid.UUID,
    field_def_id: uuid.UUID,
    option_key: str,
    option_label: str,
    option_order: int = 0,
) -> FieldDefOptionOut:
    """Construct a minimal FieldDefOptionOut for testing."""
    return FieldDefOptionOut(
        field_def_option_id=field_def_option_id,
        tenant_id=tenant_id,
        field_def_id=field_def_id,
        option_key=option_key,
        option_label=option_label,
        option_order=option_order,
        created_at=_now(),
        created_by="tester",
    )


def test_list_field_def_options_calls_service_and_wraps_response(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fake_db = DummySession()
    field_def_id = uuid.uuid4()

    o1 = _fake_option_out(
        tenant_id=tenant_id,
        field_def_option_id=uuid.uuid4(),
        field_def_id=field_def_id,
        option_key="one",
        option_label="One",
        option_order=1,
    )
    fake_items = [o1]
    fake_total = 1

    captured_kwargs: dict = {}

    def fake_list(**kwargs):
        captured_kwargs.update(kwargs)
        return fake_items, fake_total

    monkeypatch.setattr(option_service, "list_field_def_options", fake_list)

    resp: FieldDefOptionListResponse = list_field_def_options(
        tenant_id=tenant_id,
        field_def_id=field_def_id,
        limit=10,
        offset=0,
        db=fake_db,
        current_user={"sub": "user", "tenant_id": str(tenant_id)},
    )

    # Verify service call arguments
    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["field_def_id"] == field_def_id
    assert captured_kwargs["limit"] == 10
    assert captured_kwargs["offset"] == 0

    # Verify response wrapping
    assert resp.total == fake_total
    assert resp.items == fake_items
    assert resp.limit == 10
    assert resp.offset == 0


def test_create_field_def_option_uses_current_user_sub_as_created_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    field_def_id = uuid.uuid4()
    fake_db = DummySession()

    payload = FieldDefOptionCreate(
        option_key="opt",
        option_label="Option",
        option_order=0,
        created_by=None,
    )

    fake_option = _fake_option_out(
        tenant_id=tenant_id,
        field_def_option_id=uuid.uuid4(),
        field_def_id=field_def_id,
        option_key=payload.option_key,
        option_label=payload.option_label,
        option_order=payload.option_order,
    )

    captured_kwargs: dict = {}

    def fake_create(**kwargs):
        captured_kwargs.update(kwargs)
        return fake_option

    monkeypatch.setattr(option_service, "create_field_def_option", fake_create)

    current_user = {"sub": "tester", "tenant_id": str(tenant_id)}

    result = create_field_def_option(
        tenant_id=tenant_id,
        option_in=payload,
        db=fake_db,
        current_user=current_user,
    )

    # Service called correctly
    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["data"] == payload
    assert captured_kwargs["created_by"] == "tester"

    # Route returns service result
    assert result is fake_option


def test_get_field_def_option_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    option_id = uuid.uuid4()
    field_def_id = uuid.uuid4()
    fake_db = DummySession()

    fake_option = _fake_option_out(
        tenant_id=tenant_id,
        field_def_option_id=option_id,
        field_def_id=field_def_id,
        option_key="k",
        option_label="L",
    )

    captured_kwargs: dict = {}

    def fake_get(**kwargs):
        captured_kwargs.update(kwargs)
        return fake_option

    monkeypatch.setattr(option_service, "get_field_def_option", fake_get)

    result = get_field_def_option(
        tenant_id=tenant_id,
        field_def_option_id=option_id,
        db=fake_db,
        current_user={"sub": "user", "tenant_id": str(tenant_id)},
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["field_def_option_id"] == option_id
    assert result is fake_option


def test_update_field_def_option_put_uses_current_user_sub_as_modified_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    option_id = uuid.uuid4()
    fake_db = DummySession()

    payload = FieldDefOptionUpdate(
        option_key="new", option_label="New", option_order=2, updated_by=None
    )

    fake_option = _fake_option_out(
        tenant_id=tenant_id,
        field_def_option_id=option_id,
        field_def_id=uuid.uuid4(),
        option_key="new",
        option_label="New",
        option_order=2,
    )

    captured_kwargs: dict = {}

    def fake_update(**kwargs):
        captured_kwargs.update(kwargs)
        return fake_option

    monkeypatch.setattr(option_service, "update_field_def_option", fake_update)

    result = update_field_def_option(
        tenant_id=tenant_id,
        field_def_option_id=option_id,
        option_in=payload,
        db=fake_db,
        current_user={"sub": "modifier", "tenant_id": str(tenant_id)},
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["field_def_option_id"] == option_id
    assert captured_kwargs["data"] == payload
    assert captured_kwargs["modified_by"] == "modifier"
    assert result is fake_option


def test_delete_field_def_option_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    option_id = uuid.uuid4()
    fake_db = DummySession()

    called = {}

    def fake_delete(**kwargs):
        called.update(kwargs)
        return None

    monkeypatch.setattr(option_service, "delete_field_def_option", fake_delete)

    result = delete_field_def_option(
        tenant_id=tenant_id,
        field_def_option_id=option_id,
        db=fake_db,
        current_user={"sub": "user", "tenant_id": str(tenant_id)},
    )

    assert called["db"] is fake_db
    assert called["tenant_id"] == tenant_id
    assert called["field_def_option_id"] == option_id
    assert result is None