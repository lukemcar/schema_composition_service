from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.my_entity import (
    MyEntityCreate,
    MyEntityUpdate,
    MyEntityOut,
    MyEntityListResponse,
)
from app.domain.schemas.json_patch import JsonPatchRequest, JsonPatchOperation
from app.domain.services import my_entity_service

# Adjust this import path if your router module is in a different location
from app.api.routes.my_entity import (
    list_my_entities,
    create_my_entity,
    get_my_entity,
    update_my_entity,  # PUT
    patch_my_entity,   # PATCH JSON Patch
    delete_my_entity,
)


class DummySession(Session):
    """Lightweight stand-in so type hints are happy without a real DB."""
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _fake_entity_out(*, tenant_id: uuid.UUID, my_entity_id: uuid.UUID, name: str, data: dict) -> MyEntityOut:
    now = _now()
    return MyEntityOut(
        my_entity_id=my_entity_id,
        tenant_id=tenant_id,
        name=name,
        data=data,
        created_by="tester",
        updated_by="tester",
        created_at=now,
        updated_at=now,
    )


# ---------------------------------------------------------------------------
# list_my_entities
# ---------------------------------------------------------------------------


def test_list_my_entities_calls_service_and_wraps_response(monkeypatch: pytest.MonkeyPatch):
    tenant_id = uuid.uuid4()
    fake_db = DummySession()

    e1 = _fake_entity_out(
        tenant_id=tenant_id,
        my_entity_id=uuid.uuid4(),
        name="Record A",
        data={"priority": "high"},
    )
    fake_items = [e1]
    fake_total = 1

    captured_kwargs: dict = {}

    def fake_list_my_entities(**kwargs):
        captured_kwargs.update(kwargs)
        return fake_items, fake_total

    monkeypatch.setattr(my_entity_service, "list_my_entities", fake_list_my_entities)

    resp: MyEntityListResponse = list_my_entities(
        tenant_id=tenant_id,
        limit=25,
        offset=5,
        db=fake_db,
        current_user={"sub": "user-123", "tenant_id": str(tenant_id)},
    )

    # Service called with correct arguments
    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["limit"] == 25
    assert captured_kwargs["offset"] == 5

    # Response correctly wrapped
    assert resp.total == fake_total
    assert resp.items == fake_items
    assert resp.limit == 25
    assert resp.offset == 5


# ---------------------------------------------------------------------------
# create_my_entity
# ---------------------------------------------------------------------------


def test_create_my_entity_uses_current_user_sub_as_created_by(monkeypatch: pytest.MonkeyPatch):
    tenant_id = uuid.uuid4()
    fake_db = DummySession()

    payload = MyEntityCreate(
        name="Records 1",
        data={"tags": ["alpha"]},
        created_by=None,
    )

    fake_entity = _fake_entity_out(
        tenant_id=tenant_id,
        my_entity_id=uuid.uuid4(),
        name=payload.name,
        data=payload.data,
    )

    captured_kwargs: dict = {}

    def fake_create_my_entity(**kwargs):
        captured_kwargs.update(kwargs)
        return fake_entity

    monkeypatch.setattr(my_entity_service, "create_my_entity", fake_create_my_entity)

    current_user = {"sub": "test-user", "tenant_id": str(tenant_id)}

    result = create_my_entity(
        tenant_id=tenant_id,
        my_entity_in=payload,
        db=fake_db,
        current_user=current_user,
    )

    # Service called correctly
    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["data"] == payload
    assert captured_kwargs["created_by"] == "test-user"

    # Route returns service result
    assert result is fake_entity


# ---------------------------------------------------------------------------
# get_my_entity
# ---------------------------------------------------------------------------


def test_get_my_entity_calls_service(monkeypatch: pytest.MonkeyPatch):
    tenant_id = uuid.uuid4()
    my_entity_id = uuid.uuid4()
    fake_db = DummySession()

    fake_entity = _fake_entity_out(
        tenant_id=tenant_id,
        my_entity_id=my_entity_id,
        name="Records 1",
        data={"priority": "high"},
    )

    captured_kwargs: dict = {}

    def fake_get_my_entity(**kwargs):
        captured_kwargs.update(kwargs)
        return fake_entity

    monkeypatch.setattr(my_entity_service, "get_my_entity", fake_get_my_entity)

    result = get_my_entity(
        tenant_id=tenant_id,
        my_entity_id=my_entity_id,
        db=fake_db,
        current_user={"sub": "user", "tenant_id": str(tenant_id)},
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["my_entity_id"] == my_entity_id
    assert result is fake_entity


# ---------------------------------------------------------------------------
# update_my_entity (PUT)
# ---------------------------------------------------------------------------


def test_update_my_entity_put_uses_current_user_sub_as_modified_by(monkeypatch: pytest.MonkeyPatch):
    tenant_id = uuid.uuid4()
    my_entity_id = uuid.uuid4()
    fake_db = DummySession()

    update_payload = MyEntityUpdate(
        name="Records 1 updated",
        data={"priority": "low"},
        updated_by=None,
    )

    fake_entity = _fake_entity_out(
        tenant_id=tenant_id,
        my_entity_id=my_entity_id,
        name=update_payload.name or "Records 1",
        data=update_payload.data or {"priority": "high"},
    )

    captured_kwargs: dict = {}

    def fake_update_my_entity(**kwargs):
        captured_kwargs.update(kwargs)
        return fake_entity

    monkeypatch.setattr(my_entity_service, "update_my_entity", fake_update_my_entity)

    current_user = {"sub": "editor", "tenant_id": str(tenant_id)}

    result = update_my_entity(
        tenant_id=tenant_id,
        my_entity_id=my_entity_id,
        my_entity_in=update_payload,
        db=fake_db,
        current_user=current_user,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["my_entity_id"] == my_entity_id
    assert captured_kwargs["data"] == update_payload
    assert captured_kwargs["modified_by"] == "editor"
    assert result is fake_entity


# ---------------------------------------------------------------------------
# patch_my_entity (JSON Patch)
# ---------------------------------------------------------------------------


def test_patch_my_entity_uses_current_user_sub_as_modified_by(monkeypatch: pytest.MonkeyPatch):
    tenant_id = uuid.uuid4()
    my_entity_id = uuid.uuid4()
    fake_db = DummySession()

    patch_request = JsonPatchRequest(
        operations=[
            JsonPatchOperation(
                op="replace",
                path="/name",
                value="Records 1 (patched)",
            ),
            JsonPatchOperation(
                op="replace",
                path="/data/priority",
                value="low",
            ),
        ]
    )

    fake_entity = _fake_entity_out(
        tenant_id=tenant_id,
        my_entity_id=my_entity_id,
        name="Records 1 (patched)",
        data={"priority": "low"},
    )

    captured_kwargs: dict = {}

    def fake_patch_my_entity(**kwargs):
        captured_kwargs.update(kwargs)
        return fake_entity

    monkeypatch.setattr(my_entity_service, "patch_my_entity", fake_patch_my_entity)

    current_user = {"sub": "editor", "tenant_id": str(tenant_id)}

    result = patch_my_entity(
        tenant_id=tenant_id,
        my_entity_id=my_entity_id,
        patch_request=patch_request,
        db=fake_db,
        current_user=current_user,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["my_entity_id"] == my_entity_id
    assert captured_kwargs["patch_request"] == patch_request
    assert captured_kwargs["modified_by"] == "editor"
    assert result is fake_entity


# ---------------------------------------------------------------------------
# delete_my_entity
# ---------------------------------------------------------------------------


def test_delete_my_entity_calls_service_and_returns_none(monkeypatch: pytest.MonkeyPatch):
    tenant_id = uuid.uuid4()
    my_entity_id = uuid.uuid4()
    fake_db = DummySession()

    captured: dict = {"called": False}

    def fake_delete_my_entity(**kwargs):
        captured["called"] = True
        captured.update(kwargs)

    monkeypatch.setattr(my_entity_service, "delete_my_entity", fake_delete_my_entity)

    result = delete_my_entity(
        tenant_id=tenant_id,
        my_entity_id=my_entity_id,
        db=fake_db,
        current_user={"sub": "deleter", "tenant_id": str(tenant_id)},
    )

    assert captured["called"] is True
    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["my_entity_id"] == my_entity_id
    assert result is None
