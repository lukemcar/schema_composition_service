"""
Service tests for the MyEntity domain.

These tests exercise the CRUD and JSON Patch operations defined in
``app.domain.services.my_entity_service``.  They verify that
entities can be created, retrieved, listed, updated, patched and
deleted for a given tenant, and that appropriate events are
published.  Error paths such as missing records and database
failures are also covered.  External side effects (message
publishing) are patched out to keep the tests isolated.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.domain.models import MyEntity
from app.domain.schemas.my_entity import MyEntityCreate, MyEntityUpdate
from app.domain.schemas.json_patch import JsonPatchRequest, JsonPatchOperation
from app.domain.services import my_entity_service
from app.messaging.producers.my_entity_producer import MyEntityProducer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ensure_table(db_session: Session) -> None:
    """Create the my_entity table if it doesn't exist."""
    MyEntity.__table__.create(bind=db_session.get_bind(), checkfirst=True)


def _insert_entity(
    db_session: Session,
    tenant_id: uuid.UUID,
    name: str,
    data: Dict[str, Any] | None = None,
    created_by: str = "tester",
    updated_by: str = "tester",
    created_at: datetime | None = None,
) -> MyEntity:
    """Insert a MyEntity record directly via the ORM and return it."""
    entity = MyEntity(
        tenant_id=tenant_id,
        name=name,
        data=data,
        created_by=created_by,
        updated_by=updated_by,
        created_at=created_at or datetime.utcnow(),
        updated_at=created_at or datetime.utcnow(),
    )
    db_session.add(entity)
    db_session.commit()
    db_session.refresh(entity)
    return entity


# ---------------------------------------------------------------------------
# Tests for create_my_entity
# ---------------------------------------------------------------------------


@pytest.mark.postgres
@pytest.mark.liquibase
def test_create_my_entity_creates_record_and_publishes_event(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """create_my_entity should persist a record and call the producer."""
    _ensure_table(db_session)
    tenant_id = uuid.uuid4()
    # Capture calls to the producer
    calls: List[Dict[str, Any]] = []

    def fake_send_my_entity_created(*, tenant_id: uuid.UUID, my_entity_id: uuid.UUID, payload: Dict[str, Any]) -> None:
        calls.append({"tenant_id": tenant_id, "my_entity_id": my_entity_id, "payload": payload})

    monkeypatch.setattr(MyEntityProducer, "send_my_entity_created", fake_send_my_entity_created)
    create_data = MyEntityCreate(name="Alpha", data={"k": "v"})
    entity = my_entity_service.create_my_entity(db=db_session, tenant_id=tenant_id, data=create_data, created_by="tester")
    # Assert one row in DB
    rows = db_session.query(MyEntity).filter(MyEntity.tenant_id == tenant_id).all()
    assert len(rows) == 1
    db_entity = rows[0]
    assert db_entity.my_entity_id == entity.my_entity_id
    assert db_entity.name == "Alpha"
    assert db_entity.data == {"k": "v"}
    assert db_entity.created_by == "tester"
    assert db_entity.updated_by == "tester"
    # Producer called exactly once with correct payload
    assert len(calls) == 1
    call = calls[0]
    assert call["tenant_id"] == tenant_id
    assert call["my_entity_id"] == entity.my_entity_id
    assert call["payload"]["my_entity_id"] == str(entity.my_entity_id)


@pytest.mark.postgres
@pytest.mark.liquibase
def test_create_my_entity_db_error_returns_500(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If commit fails, create_my_entity should rollback and raise 500."""
    _ensure_table(db_session)
    tenant_id = uuid.uuid4()
    # Patch commit to throw
    def fail_commit() -> None:
        raise SQLAlchemyError("boom")
    monkeypatch.setattr(db_session, "commit", lambda: fail_commit())
    # Patch producer to no-op
    monkeypatch.setattr(MyEntityProducer, "send_my_entity_created", lambda **kwargs: None)
    from fastapi import HTTPException as FastAPIHTTPException
    with pytest.raises(FastAPIHTTPException) as exc:
        my_entity_service.create_my_entity(
            db=db_session,
            tenant_id=tenant_id,
            data=MyEntityCreate(name="Fail", data=None),
            created_by="tester",
        )
    assert exc.value.status_code == 500


# ---------------------------------------------------------------------------
# Tests for get_my_entity
# ---------------------------------------------------------------------------

@pytest.mark.postgres
@pytest.mark.liquibase
def test_get_my_entity_returns_record(
    db_session: Session,
) -> None:
    """get_my_entity should return an existing record for the tenant."""
    _ensure_table(db_session)
    tenant_id = uuid.uuid4()
    other_tenant = uuid.uuid4()
    # Insert one entity for tenant_id and one for other tenant
    e = _insert_entity(db_session, tenant_id, "Item", {"a": 1})
    _insert_entity(db_session, other_tenant, "Other", None)
    # Should return the correct entity
    result = my_entity_service.get_my_entity(db=db_session, tenant_id=tenant_id, my_entity_id=e.my_entity_id)
    assert result.my_entity_id == e.my_entity_id
    assert result.name == "Item"


@pytest.mark.postgres
@pytest.mark.liquibase
def test_get_my_entity_not_found(
    db_session: Session,
) -> None:
    """get_my_entity should raise 404 for missing ID or mismatched tenant."""
    _ensure_table(db_session)
    tenant_id = uuid.uuid4()
    # Insert entity for tenant_id
    e = _insert_entity(db_session, tenant_id, "X", None)
    # Wrong tenant
    from fastapi import HTTPException as FastAPIHTTPException
    with pytest.raises(FastAPIHTTPException) as exc1:
        my_entity_service.get_my_entity(db=db_session, tenant_id=uuid.uuid4(), my_entity_id=e.my_entity_id)
    assert exc1.value.status_code == 404
    # Missing ID
    with pytest.raises(FastAPIHTTPException) as exc2:
        my_entity_service.get_my_entity(db=db_session, tenant_id=tenant_id, my_entity_id=uuid.uuid4())
    assert exc2.value.status_code == 404


# ---------------------------------------------------------------------------
# Tests for list_my_entities
# ---------------------------------------------------------------------------

@pytest.mark.postgres
@pytest.mark.liquibase
def test_list_my_entities_pagination(
    db_session: Session,
) -> None:
    """list_my_entities should return only tenant records, ordered descending, with total."""
    _ensure_table(db_session)
    tenant_id = uuid.uuid4()
    other_tenant = uuid.uuid4()
    # Insert three entities for tenant and one for other tenant
    now = datetime.utcnow()
    ids: List[MyEntity] = []
    for i in range(3):
        entity = _insert_entity(
            db_session,
            tenant_id,
            name=f"Item {i}",
            data={"i": i},
            created_at=now + timedelta(seconds=i),
        )
        ids.append(entity)
    _insert_entity(db_session, other_tenant, "Other", None)
    # Get limit=2 offset=1; should return 2nd and 3rd newest
    items, total = my_entity_service.list_my_entities(db=db_session, tenant_id=tenant_id, limit=2, offset=1)
    assert total == 3
    # Entities are ordered by created_at desc
    sorted_entities = sorted(ids, key=lambda e: e.created_at, reverse=True)
    assert [item.my_entity_id for item in items] == [sorted_entities[1].my_entity_id, sorted_entities[2].my_entity_id]


# ---------------------------------------------------------------------------
# Tests for update_my_entity
# ---------------------------------------------------------------------------

@pytest.mark.postgres
@pytest.mark.liquibase
def test_update_my_entity_modifies_fields_and_emits_event(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """update_my_entity should update name/data and produce an event with changes."""
    _ensure_table(db_session)
    tenant_id = uuid.uuid4()
    entity = _insert_entity(db_session, tenant_id, "Old", {"x": 1})
    calls: List[Dict[str, Any]] = []

    def fake_send_updated(*, tenant_id: uuid.UUID, my_entity_id: uuid.UUID, changes: Dict[str, Any], payload: Dict[str, Any]) -> None:
        calls.append({"tenant_id": tenant_id, "my_entity_id": my_entity_id, "changes": changes, "payload": payload})
    monkeypatch.setattr(MyEntityProducer, "send_my_entity_updated", fake_send_updated)
    # Perform update
    update_data = MyEntityUpdate(name="New", data={"x": 2})
    updated = my_entity_service.update_my_entity(
        db=db_session,
        tenant_id=tenant_id,
        my_entity_id=entity.my_entity_id,
        data=update_data,
        modified_by="tester",
    )
    assert updated.name == "New"
    assert updated.data == {"x": 2}
    # Ensure only changed fields appear in changes
    assert len(calls) == 1
    event_call = calls[0]
    assert event_call["changes"] == {"name": "New", "data": {"x": 2}}
    assert event_call["tenant_id"] == tenant_id
    assert event_call["my_entity_id"] == entity.my_entity_id


@pytest.mark.postgres
@pytest.mark.liquibase
def test_update_my_entity_no_changes_does_not_emit_event(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """update_my_entity should not produce an event when no fields change."""
    _ensure_table(db_session)
    tenant_id = uuid.uuid4()
    entity = _insert_entity(db_session, tenant_id, "Same", {"z": 0})
    monkeypatch.setattr(MyEntityProducer, "send_my_entity_updated", lambda **kwargs: (_ for _ in ()).throw(Exception("should not be called")))
    update_data = MyEntityUpdate(name="Same", data=None)
    # Should not raise even though event would throw if called
    updated = my_entity_service.update_my_entity(
        db=db_session,
        tenant_id=tenant_id,
        my_entity_id=entity.my_entity_id,
        data=update_data,
        modified_by="tester",
    )
    assert updated.name == "Same"
    assert updated.data == {"z": 0}


# ---------------------------------------------------------------------------
# Tests for delete_my_entity
# ---------------------------------------------------------------------------

@pytest.mark.postgres
@pytest.mark.liquibase
def test_delete_my_entity_removes_record_and_publishes_event(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """delete_my_entity should delete the record and emit deletion event."""
    _ensure_table(db_session)
    tenant_id = uuid.uuid4()
    entity = _insert_entity(db_session, tenant_id, "Del", None)
    calls: List[Dict[str, Any]] = []
    def fake_send_deleted(*, tenant_id: uuid.UUID, my_entity_id: uuid.UUID, deleted_dt: str) -> None:
        calls.append({"tenant_id": tenant_id, "my_entity_id": my_entity_id, "deleted_dt": deleted_dt})
    monkeypatch.setattr(MyEntityProducer, "send_my_entity_deleted", fake_send_deleted)
    my_entity_service.delete_my_entity(db=db_session, tenant_id=tenant_id, my_entity_id=entity.my_entity_id)
    # Record should be gone
    assert db_session.query(MyEntity).filter(MyEntity.my_entity_id == entity.my_entity_id).count() == 0
    assert len(calls) == 1
    assert calls[0]["tenant_id"] == tenant_id
    assert calls[0]["my_entity_id"] == entity.my_entity_id


@pytest.mark.postgres
@pytest.mark.liquibase
def test_delete_my_entity_not_found_raises_404(
    db_session: Session,
) -> None:
    """delete_my_entity should raise when the record doesn't exist."""
    _ensure_table(db_session)
    from fastapi import HTTPException as FastAPIHTTPException
    with pytest.raises(FastAPIHTTPException) as exc:
        my_entity_service.delete_my_entity(db=db_session, tenant_id=uuid.uuid4(), my_entity_id=uuid.uuid4())
    assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# Tests for patch_my_entity
# ---------------------------------------------------------------------------

@pytest.mark.postgres
@pytest.mark.liquibase
def test_patch_my_entity_replace_name(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """patch_my_entity should replace the name field and emit an event."""
    _ensure_table(db_session)
    tenant_id = uuid.uuid4()
    entity = _insert_entity(db_session, tenant_id, "OldName", {"v": 1})
    calls: List[Dict[str, Any]] = []
    def fake_send_updated(*, tenant_id: uuid.UUID, my_entity_id: uuid.UUID, changes: Dict[str, Any], payload: Dict[str, Any]) -> None:
        calls.append(changes)
    monkeypatch.setattr(MyEntityProducer, "send_my_entity_updated", fake_send_updated)
    patch = JsonPatchRequest(operations=[JsonPatchOperation(op="replace", path="/name", value="NewName")])
    updated = my_entity_service.patch_my_entity(db=db_session, tenant_id=tenant_id, my_entity_id=entity.my_entity_id, patch_request=patch, modified_by="tester")
    assert updated.name == "NewName"
    assert updated.data == {"v": 1}
    # Should have recorded name change only
    assert calls == [{"name": "NewName"}]


@pytest.mark.postgres
@pytest.mark.liquibase
def test_patch_my_entity_add_nested_data(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """patch_my_entity should add nested keys within data and emit event."""
    _ensure_table(db_session)
    tenant_id = uuid.uuid4()
    entity = _insert_entity(db_session, tenant_id, "Entity", {"outer": {"inner": 1}})
    calls: List[Dict[str, Any]] = []
    monkeypatch.setattr(MyEntityProducer, "send_my_entity_updated", lambda **kwargs: calls.append(kwargs["changes"]))
    patch = JsonPatchRequest(
        operations=[
            JsonPatchOperation(op="add", path="/data/outer/new", value=2),
            JsonPatchOperation(op="replace", path="/data/outer/inner", value=3),
        ]
    )
    updated = my_entity_service.patch_my_entity(db=db_session, tenant_id=tenant_id, my_entity_id=entity.my_entity_id, patch_request=patch, modified_by="tester")
    assert updated.data == {"outer": {"inner": 3, "new": 2}}
    # Changes dict should contain entire data, since nested modifications count as data change
    assert calls == [{"data": {"outer": {"inner": 3, "new": 2}}}]

