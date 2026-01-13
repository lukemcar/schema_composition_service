"""
API tests for the FieldDef domain.

These tests ensure that the FastAPI routes defined in
``app/api/routes/field_def.py`` correctly call the service functions
and handle request/response wrapping.  Only routing logic is tested
here; database and messaging side effects are out of scope.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.field_def import (
    FieldDefCreate,
    FieldDefUpdate,
    FieldDefOut,
    FieldDefListResponse,
)
from app.domain.models.enums import FieldElementType
from app.domain.services import field_def_service

from app.api.routes.field_def import (
    list_field_defs,
    create_field_def,
    get_field_def,
    update_field_def,
    delete_field_def,
)


class DummySession(Session):
    """Placeholder for DB session type hints."""

    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _fake_field_def_out(
    *,
    tenant_id: uuid.UUID,
    field_def_id: uuid.UUID,
    field_def_business_key: str,
    name: str,
    field_key: str,
    label: str,
    element_type: FieldElementType,
    version: int = 1,
) -> FieldDefOut:
    """Create a minimal FieldDefOut object for testing."""
    now = _now()
    return FieldDefOut(
        field_def_id=field_def_id,
        tenant_id=tenant_id,
        field_def_business_key=field_def_business_key,
        field_def_version=version,
        name=name,
        description=None,
        field_key=field_key,
        label=label,
        category_id=None,
        data_type=None,
        element_type=element_type,
        validation=None,
        ui_config=None,
        is_published=False,
        published_at=None,
        is_archived=False,
        archived_at=None,
        source_type=None,
        source_package_key=None,
        source_artifact_key=None,
        source_artifact_version=None,
        source_checksum=None,
        installed_at=None,
        installed_by=None,
        created_by="tester",
        updated_by="tester",
        created_at=now,
        updated_at=now,
    )


def test_list_field_defs_calls_service_and_wraps_response(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fake_db = DummySession()

    f1 = _fake_field_def_out(
        tenant_id=tenant_id,
        field_def_id=uuid.uuid4(),
        field_def_business_key="f1",
        name="Field One",
        field_key="field_one",
        label="Field One",
        element_type=FieldElementType.TEXT,
    )
    fake_items = [f1]
    fake_total = 1

    captured_kwargs: dict = {}

    def fake_list(**kwargs):
        captured_kwargs.update(kwargs)
        return fake_items, fake_total

    monkeypatch.setattr(field_def_service, "list_field_defs", fake_list)

    resp: FieldDefListResponse = list_field_defs(
        tenant_id=tenant_id,
        category_id=None,
        element_type=None,
        data_type=None,
        is_active=None,
        limit=25,
        offset=0,
        db=fake_db,
        current_user={"sub": "user", "tenant_id": str(tenant_id)},
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["category_id"] is None
    assert captured_kwargs["element_type"] is None
    assert captured_kwargs["data_type"] is None
    assert captured_kwargs["is_active"] is None
    assert captured_kwargs["limit"] == 25
    assert captured_kwargs["offset"] == 0

    assert resp.total == fake_total
    assert resp.items == fake_items
    assert resp.limit == 25
    assert resp.offset == 0


def test_create_field_def_uses_current_user_sub_as_created_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fake_db = DummySession()

    payload = FieldDefCreate(
        field_def_business_key="key",
        field_def_version=1,
        name="Name",
        description=None,
        field_key="field_key",
        label="Label",
        category_id=None,
        data_type=None,
        element_type=FieldElementType.TEXT,
        validation=None,
        ui_config=None,
        is_published=False,
        published_at=None,
        is_archived=False,
        archived_at=None,
        source_type=None,
        source_package_key=None,
        source_artifact_key=None,
        source_artifact_version=None,
        source_checksum=None,
        installed_at=None,
        installed_by=None,
        created_by=None,
        updated_by=None,
    )

    fake_def = _fake_field_def_out(
        tenant_id=tenant_id,
        field_def_id=uuid.uuid4(),
        field_def_business_key=payload.field_def_business_key,
        name=payload.name,
        field_key=payload.field_key,
        label=payload.label,
        element_type=payload.element_type,
    )

    captured_kwargs: dict = {}

    def fake_create(**kwargs):
        captured_kwargs.update(kwargs)
        return fake_def

    monkeypatch.setattr(field_def_service, "create_field_def", fake_create)

    current_user = {"sub": "creator", "tenant_id": str(tenant_id)}

    result = create_field_def(
        tenant_id=tenant_id,
        field_in=payload,
        db=fake_db,
        current_user=current_user,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["data"] == payload
    assert captured_kwargs["created_by"] == "creator"
    assert result is fake_def


def test_get_field_def_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    def_id = uuid.uuid4()
    fake_db = DummySession()

    fake_def = _fake_field_def_out(
        tenant_id=tenant_id,
        field_def_id=def_id,
        field_def_business_key="b",
        name="Name",
        field_key="field",
        label="Label",
        element_type=FieldElementType.TEXT,
    )

    captured: dict = {}

    def fake_get(**kwargs):
        captured.update(kwargs)
        return fake_def

    monkeypatch.setattr(field_def_service, "get_field_def", fake_get)

    result = get_field_def(
        tenant_id=tenant_id,
        field_def_id=def_id,
        db=fake_db,
        current_user={"sub": "user", "tenant_id": str(tenant_id)},
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["field_def_id"] == def_id
    assert result is fake_def


def test_update_field_def_put_uses_current_user_sub_as_modified_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    def_id = uuid.uuid4()
    fake_db = DummySession()

    payload = FieldDefUpdate(
        name="Updated",
        updated_by=None,
    )

    fake_def = _fake_field_def_out(
        tenant_id=tenant_id,
        field_def_id=def_id,
        field_def_business_key="b",
        name="Updated",
        field_key="field",
        label="Label",
        element_type=FieldElementType.TEXT,
    )

    captured: dict = {}

    def fake_update(**kwargs):
        captured.update(kwargs)
        return fake_def

    monkeypatch.setattr(field_def_service, "update_field_def", fake_update)

    result = update_field_def(
        tenant_id=tenant_id,
        field_def_id=def_id,
        field_in=payload,
        db=fake_db,
        current_user={"sub": "modifier", "tenant_id": str(tenant_id)},
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["field_def_id"] == def_id
    assert captured["data"] == payload
    assert captured["modified_by"] == "modifier"
    assert result is fake_def


def test_delete_field_def_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    def_id = uuid.uuid4()
    fake_db = DummySession()

    called = {}

    def fake_delete(**kwargs):
        called.update(kwargs)
        return None

    monkeypatch.setattr(field_def_service, "delete_field_def", fake_delete)

    result = delete_field_def(
        tenant_id=tenant_id,
        field_def_id=def_id,
        db=fake_db,
        current_user={"sub": "deleter", "tenant_id": str(tenant_id)},
    )

    assert called["db"] is fake_db
    assert called["tenant_id"] == tenant_id
    assert called["field_def_id"] == def_id
    assert result is None