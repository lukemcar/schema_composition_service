from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session

from app.domain.schemas.form_catalog_category import (
    FormCatalogCategoryCreate,
    FormCatalogCategoryUpdate,
    FormCatalogCategoryOut,
    FormCatalogCategoryListResponse,
)
from app.domain.services import form_catalog_category_service as category_service

# Adjust this import path if your router module is in a different location
from app.api.routes.form_catalog_category import (
    list_form_catalog_categories,
    create_form_catalog_category,
    get_form_catalog_category,
    update_form_catalog_category,
    delete_form_catalog_category,
)


class DummySession(Session):
    """Lightweight stand‑in so type hints are happy without a real DB."""
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _fake_category_out(
    *, tenant_id: uuid.UUID, form_catalog_category_id: uuid.UUID, category_key: str, category_name: str
) -> FormCatalogCategoryOut:
    now = _now()
    return FormCatalogCategoryOut(
        form_catalog_category_id=form_catalog_category_id,
        tenant_id=tenant_id,
        category_key=category_key,
        category_name=category_name,
        description=None,
        is_active=True,
        created_by="tester",
        updated_by="tester",
        created_at=now,
        updated_at=now,
    )


# ---------------------------------------------------------------------------
# list_form_catalog_categories
# ---------------------------------------------------------------------------


def test_list_form_catalog_categories_calls_service_and_wraps_response(monkeypatch: pytest.MonkeyPatch):
    tenant_id = uuid.uuid4()
    fake_db = DummySession()

    c1 = _fake_category_out(
        tenant_id=tenant_id,
        form_catalog_category_id=uuid.uuid4(),
        category_key="cat1",
        category_name="Category One",
    )
    fake_items = [c1]
    fake_total = 1

    captured_kwargs: dict = {}

    def fake_list(**kwargs):
        captured_kwargs.update(kwargs)
        return fake_items, fake_total

    monkeypatch.setattr(category_service, "list_form_catalog_categories", fake_list)

    resp: FormCatalogCategoryListResponse = list_form_catalog_categories(
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
# create_form_catalog_category
# ---------------------------------------------------------------------------


def test_create_form_catalog_category_uses_current_user_sub_as_created_by(monkeypatch: pytest.MonkeyPatch):
    tenant_id = uuid.uuid4()
    fake_db = DummySession()

    payload = FormCatalogCategoryCreate(
        category_key="cat1",
        category_name="Cat 1",
        description=None,
        is_active=True,
        created_by=None,
        updated_by=None,
    )

    fake_category = _fake_category_out(
        tenant_id=tenant_id,
        form_catalog_category_id=uuid.uuid4(),
        category_key=payload.category_key,
        category_name=payload.category_name,
    )

    captured_kwargs: dict = {}

    def fake_create(**kwargs):
        captured_kwargs.update(kwargs)
        return fake_category

    monkeypatch.setattr(category_service, "create_form_catalog_category", fake_create)

    current_user = {"sub": "test-user", "tenant_id": str(tenant_id)}

    result = create_form_catalog_category(
        tenant_id=tenant_id,
        category_in=payload,
        db=fake_db,
        current_user=current_user,
    )

    # Service called correctly
    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["data"] == payload
    assert captured_kwargs["created_by"] == "test-user"

    # Route returns service result
    assert result is fake_category


# ---------------------------------------------------------------------------
# get_form_catalog_category
# ---------------------------------------------------------------------------


def test_get_form_catalog_category_calls_service(monkeypatch: pytest.MonkeyPatch):
    tenant_id = uuid.uuid4()
    cat_id = uuid.uuid4()
    fake_db = DummySession()

    fake_category = _fake_category_out(
        tenant_id=tenant_id,
        form_catalog_category_id=cat_id,
        category_key="k",
        category_name="Cat",
    )

    captured_kwargs: dict = {}

    def fake_get(**kwargs):
        captured_kwargs.update(kwargs)
        return fake_category

    monkeypatch.setattr(category_service, "get_form_catalog_category", fake_get)

    result = get_form_catalog_category(
        tenant_id=tenant_id,
        form_catalog_category_id=cat_id,
        db=fake_db,
        current_user={"sub": "user", "tenant_id": str(tenant_id)},
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["form_catalog_category_id"] == cat_id
    assert result is fake_category


# ---------------------------------------------------------------------------
# update_form_catalog_category (PUT)
# ---------------------------------------------------------------------------


def test_update_form_catalog_category_put_uses_current_user_sub_as_modified_by(monkeypatch: pytest.MonkeyPatch):
    tenant_id = uuid.uuid4()
    cat_id = uuid.uuid4()
    fake_db = DummySession()

    update_payload = FormCatalogCategoryUpdate(
        category_key="new-key",
        category_name="New Name",
        description="New desc",
        is_active=True,
        updated_by=None,
    )

    fake_category = _fake_category_out(
        tenant_id=tenant_id,
        form_catalog_category_id=cat_id,
        category_key=update_payload.category_key or "old-key",
        category_name=update_payload.category_name or "Old Name",
    )

    captured_kwargs: dict = {}

    def fake_update(**kwargs):
        captured_kwargs.update(kwargs)
        return fake_category

    monkeypatch.setattr(category_service, "update_form_catalog_category", fake_update)

    current_user = {"sub": "mod-user", "tenant_id": str(tenant_id)}

    result = update_form_catalog_category(
        tenant_id=tenant_id,
        form_catalog_category_id=cat_id,
        category_in=update_payload,
        db=fake_db,
        current_user=current_user,
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["form_catalog_category_id"] == cat_id
    assert captured_kwargs["data"] == update_payload
    assert captured_kwargs["modified_by"] == "mod-user"
    assert result is fake_category


# ---------------------------------------------------------------------------
# delete_form_catalog_category
# ---------------------------------------------------------------------------


def test_delete_form_catalog_category_calls_service(monkeypatch: pytest.MonkeyPatch):
    tenant_id = uuid.uuid4()
    cat_id = uuid.uuid4()
    fake_db = DummySession()

    captured_kwargs: dict = {}

    def fake_delete(**kwargs):
        captured_kwargs.update(kwargs)
        return None

    monkeypatch.setattr(category_service, "delete_form_catalog_category", fake_delete)

    result = delete_form_catalog_category(
        tenant_id=tenant_id,
        form_catalog_category_id=cat_id,
        db=fake_db,
        current_user={"sub": "deleter", "tenant_id": str(tenant_id)},
    )

    assert captured_kwargs["db"] is fake_db
    assert captured_kwargs["tenant_id"] == tenant_id
    assert captured_kwargs["form_catalog_category_id"] == cat_id
    assert result is None
