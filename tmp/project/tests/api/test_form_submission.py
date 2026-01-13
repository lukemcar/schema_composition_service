"""
API tests for the FormSubmission domain.

These tests ensure that form submission routes delegate correctly to
service layer functions and wrap paginated responses.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.form_submission import (
    FormSubmissionCreate,
    FormSubmissionUpdate,
    FormSubmissionOut,
    FormSubmissionListResponse,
)
from app.domain.services import form_submission_service

from app.api.routes.form_submission import (
    list_form_submissions,
    create_form_submission,
    get_form_submission,
    update_form_submission,
    delete_form_submission,
)


class DummySession(Session):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _fake_fs_out(
    *,
    tenant_id: uuid.UUID,
    form_submission_id: uuid.UUID,
    form_id: uuid.UUID,
    submission_status: str = "draft",
    is_deleted: bool = False,
) -> FormSubmissionOut:
    now = _now()
    return FormSubmissionOut(
        form_submission_id=form_submission_id,
        tenant_id=tenant_id,
        form_id=form_id,
        submission_status=submission_status,
        submitted_at=None,
        submitted_by=None,
        created_by="tester",
        created_at=now,
        updated_at=now,
        is_deleted=is_deleted,
    )


def test_list_form_submissions_calls_service_and_wraps_response(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    form_id = uuid.uuid4()
    fake_db = DummySession()

    fs = _fake_fs_out(
        tenant_id=tenant_id,
        form_submission_id=uuid.uuid4(),
        form_id=form_id,
        submission_status="draft",
        is_deleted=False,
    )
    fake_items = [fs]
    fake_total = 1

    captured: dict = {}

    def fake_list(**kwargs):
        captured.update(kwargs)
        return fake_items, fake_total

    monkeypatch.setattr(form_submission_service, "list_form_submissions", fake_list)

    resp: FormSubmissionListResponse = list_form_submissions(
        tenant_id=tenant_id,
        form_id=form_id,
        limit=100,
        offset=0,
        db=fake_db,
        current_user={"sub": "u", "tenant_id": str(tenant_id)},
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["form_id"] == form_id
    assert captured["limit"] == 100
    assert captured["offset"] == 0

    assert resp.total == fake_total
    assert resp.items == fake_items
    assert resp.limit == 100
    assert resp.offset == 0


def test_create_form_submission_uses_current_user_sub_as_created_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    form_id = uuid.uuid4()
    fake_db = DummySession()

    payload = FormSubmissionCreate(
        form_id=form_id,
        submission_status="draft",
        submitted_at=None,
        submitted_by=None,
        created_by=None,
    )

    fake_fs = _fake_fs_out(
        tenant_id=tenant_id,
        form_submission_id=uuid.uuid4(),
        form_id=form_id,
        submission_status="draft",
        is_deleted=False,
    )

    captured: dict = {}

    def fake_create(**kwargs):
        captured.update(kwargs)
        return fake_fs

    monkeypatch.setattr(form_submission_service, "create_form_submission", fake_create)

    result = create_form_submission(
        tenant_id=tenant_id,
        submission_in=payload,
        db=fake_db,
        current_user={"sub": "creator", "tenant_id": str(tenant_id)},
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["data"] == payload
    assert captured["created_by"] == "creator"
    assert result is fake_fs


def test_get_form_submission_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fs_id = uuid.uuid4()
    form_id = uuid.uuid4()
    fake_db = DummySession()

    fake_fs = _fake_fs_out(
        tenant_id=tenant_id,
        form_submission_id=fs_id,
        form_id=form_id,
        submission_status="draft",
        is_deleted=False,
    )

    captured: dict = {}

    def fake_get(**kwargs):
        captured.update(kwargs)
        return fake_fs

    monkeypatch.setattr(form_submission_service, "get_form_submission", fake_get)

    result = get_form_submission(
        tenant_id=tenant_id,
        form_submission_id=fs_id,
        db=fake_db,
        current_user={"sub": "user", "tenant_id": str(tenant_id)},
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["form_submission_id"] == fs_id
    assert result is fake_fs


def test_update_form_submission_put_uses_current_user_sub_as_modified_by(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fs_id = uuid.uuid4()
    form_id = uuid.uuid4()
    fake_db = DummySession()

    payload = FormSubmissionUpdate(
        submission_status="submitted",
        submitted_at=_now(),
        submitted_by="user",
        updated_by=None,
    )

    fake_fs = _fake_fs_out(
        tenant_id=tenant_id,
        form_submission_id=fs_id,
        form_id=form_id,
        submission_status="submitted",
        is_deleted=False,
    )

    captured: dict = {}

    def fake_update(**kwargs):
        captured.update(kwargs)
        return fake_fs

    monkeypatch.setattr(form_submission_service, "update_form_submission", fake_update)

    result = update_form_submission(
        tenant_id=tenant_id,
        form_submission_id=fs_id,
        submission_in=payload,
        db=fake_db,
        current_user={"sub": "modifier", "tenant_id": str(tenant_id)},
    )

    assert captured["db"] is fake_db
    assert captured["tenant_id"] == tenant_id
    assert captured["form_submission_id"] == fs_id
    assert captured["data"] == payload
    assert captured["modified_by"] == "modifier"
    assert result is fake_fs


def test_delete_form_submission_calls_service(monkeypatch: pytest.MonkeyPatch) -> None:
    tenant_id = uuid.uuid4()
    fs_id = uuid.uuid4()
    fake_db = DummySession()

    called: dict = {}

    def fake_delete(**kwargs):
        called.update(kwargs)
        return None

    monkeypatch.setattr(form_submission_service, "delete_form_submission", fake_delete)

    result = delete_form_submission(
        tenant_id=tenant_id,
        form_submission_id=fs_id,
        db=fake_db,
        current_user={"sub": "deleter", "tenant_id": str(tenant_id)},
    )

    assert called["db"] is fake_db
    assert called["tenant_id"] == tenant_id
    assert called["form_submission_id"] == fs_id
    assert result is None