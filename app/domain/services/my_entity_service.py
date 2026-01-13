"""
Service layer functions for the MyEntity domain.

This module implements the core business logic for creating,
retrieving, listing, updating and deleting MyEntity records.  All
database access is tenant-scoped: callers must provide the tenant
identifier explicitly.  When adding new domain services follow the
patterns used here: parameterise the tenant ID, perform a simple
query/update using SQLAlchemy and raise appropriate HTTP exceptions
when records are not found or operations fail.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID
from copy import deepcopy

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.domain.models import MyEntity
from app.domain.schemas.json_patch import JsonPatchRequest, JsonPatchOperation
from app.domain.schemas.my_entity import MyEntityCreate, MyEntityUpdate, MyEntityOut
from app.messaging.producers.my_entity_producer import MyEntityProducer




logger = logging.getLogger(__name__)


def create_my_entity(
    db: Session,
    tenant_id: UUID,
    data: MyEntityCreate,
    created_by: str = "system",
) -> MyEntity:
    """Create a new MyEntity for the given tenant.

    On success the new record is committed and refreshed, then a
    ``my_entity.created`` event is published via RabbitMQ.  If a
    database error occurs a 500 response is raised.
    """
    logger.info(
        "Creating my_entity for tenant_id=%s name=%r user=%s",
        tenant_id,
        data.name,
        created_by,
    )
    entity = MyEntity(
        tenant_id=tenant_id,
        name=data.name,
        data=data.data,
        created_by=data.created_by or created_by,
        updated_by=data.created_by or created_by,
    )
    db.add(entity)
    try:
        db.commit()
        db.refresh(entity)
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error while creating MyEntity")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the entity.",
        )

    # Publish event after commit to avoid sending events for rolled back transactions
    payload = MyEntityOut.model_validate(entity).model_dump(mode="json")
    MyEntityProducer.send_my_entity_created(
        tenant_id=tenant_id,
        my_entity_id=entity.my_entity_id,
        payload=payload,
    )
    return entity


def get_my_entity(
    db: Session,
    tenant_id: UUID,
    my_entity_id: UUID,
) -> MyEntity:
    """Retrieve a single MyEntity by id and tenant.

    Raises a 404 if the entity does not exist or does not belong to
    the tenant.
    """
    entity = db.get(MyEntity, my_entity_id)
    if entity is None or entity.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MyEntity not found",
        )
    return entity


def list_my_entities(
    db: Session,
    tenant_id: UUID,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[MyEntity], int]:
    """List MyEntity records for a tenant with simple pagination.

    Returns a tuple of (items, total) where total is the total number
    of entities for the tenant independent of limit/offset.
    """
    base_stmt = select(MyEntity).where(MyEntity.tenant_id == tenant_id)
    try:
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total: int = db.execute(count_stmt).scalar_one()
        stmt = base_stmt.order_by(MyEntity.created_at.desc()).limit(limit).offset(offset)
        items = db.execute(stmt).scalars().all()
        return items, total
    except SQLAlchemyError:
        logger.exception(
            "Database error while listing MyEntity records for tenant_id=%s",
            tenant_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving entities.",
        )


def update_my_entity(
    db: Session,
    tenant_id: UUID,
    my_entity_id: UUID,
    data: MyEntityUpdate,
    modified_by: str = "system",
) -> MyEntity:
    """Update a MyEntity record.

    Only the provided fields in ``data`` are modified.  After update
    the changes are recorded in a dictionary and published in a
    ``my_entity.updated`` event.  A 404 is raised if the record does
    not exist or does not belong to the tenant.
    """
    entity = get_my_entity(db, tenant_id, my_entity_id)
    changes: Dict[str, Any] = {}
    if data.name is not None and data.name != entity.name:
        changes["name"] = data.name
        entity.name = data.name
    if data.data is not None and data.data != entity.data:
        changes["data"] = data.data
        entity.data = data.data
    if data.updated_by:
        entity.updated_by = data.updated_by
    else:
        entity.updated_by = modified_by
    entity.updated_at = datetime.utcnow()
    try:
        db.commit()
        db.refresh(entity)
    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Database error while updating MyEntity id=%s tenant_id=%s",
            my_entity_id,
            tenant_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the entity.",
        )
    if changes:
        payload = MyEntityOut.model_validate(entity).model_dump(mode="json")
        MyEntityProducer.send_my_entity_updated(
            tenant_id=tenant_id,
            my_entity_id=my_entity_id,
            changes=changes,
            payload=payload,
        )
    else:
        logger.info("MyEntity has no changes")
        
    return entity


def delete_my_entity(
    db: Session,
    tenant_id: UUID,
    my_entity_id: UUID,
) -> None:
    """Delete a MyEntity record and publish a deletion event."""
    entity = get_my_entity(db, tenant_id, my_entity_id)
    try:
        db.delete(entity)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Database error while deleting MyEntity id=%s tenant_id=%s",
            my_entity_id,
            tenant_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the entity.",
        )
    # Publish deletion event.  We include a deleted timestamp as a string
    deleted_dt = datetime.utcnow().isoformat()
    MyEntityProducer.send_my_entity_deleted(
        tenant_id=tenant_id,
        my_entity_id=my_entity_id,
        deleted_dt=deleted_dt,
    )
    

def patch_my_entity(
    db: Session,
    tenant_id: UUID,
    my_entity_id: UUID,
    patch_request: JsonPatchRequest,
    modified_by: str = "system",
) -> MyEntity:
    """
    Apply an ordered list of JSON Patch operations (RFC 6902) to a ``MyEntity``.

    **Supported paths** (destination pointers):

    - ``/name`` - The entity's ``name`` attribute.  Adding or replacing requires a
      non-empty string.  Removing or moving from this path is disallowed.
    - ``/data`` - The entity's ``data`` attribute.  Setting this path replaces
      the entire payload.  Removing it sets the value to ``None``.
    - ``/data/<nested…>`` - Arbitrary nested JSON Pointer into the ``data``
      structure.  Intermediate containers are created for ``add``/``replace``.

    **Supported operations**:

    - ``add`` and ``replace``: Already supported; mutate the target pointer.
    - ``remove``: Already supported except for ``/name`` (disallowed).
    - ``copy``: Duplicate a value from a ``from`` pointer to the destination.
      Does not mutate the source.  Disallowed if the source is ``/name`` or if
      copying into ``/name`` would violate the string constraint.
    - ``move``: Relocate a value from a ``from`` pointer to the destination.
      Equivalent to ``copy`` followed by removal of the source.  Moving from
      ``/name`` is disallowed because the service never allows removal of the
      required ``name`` attribute.
    - ``test``: Assert that the current value at the destination pointer equals
      the provided ``value``.  On mismatch, the entire patch fails and a
      ``409 Conflict`` is returned.  Does not mutate the entity.

    The patch is applied atomically: if any operation fails, none of the
    subsequent operations are executed and the transaction is rolled back.
    ``patch_request`` is assumed to have been validated by Pydantic, so
    missing ``from`` pointers or invalid ``op`` values will never reach this
    function.
    """
    # Retrieve the entity up front; if not found, a 404 is raised.
    entity = get_my_entity(db, tenant_id, my_entity_id)

    # Capture the initial state for change detection.  ``deepcopy`` is used to
    # ensure nested structures are compared by value rather than by identity.
    before_name: str = entity.name
    before_data: Any = deepcopy(entity.data)

    logger.info(
        "Processing JSON Patch for my_entity_id=%s tenant_id=%s ops=%d",
        my_entity_id,
        tenant_id,
        len(patch_request.operations),
    )

    # Apply each operation in order.  If any operation raises an HTTPException,
    # the loop aborts and the transaction is rolled back in the caller.
    for op in patch_request.operations:
        _apply_my_entity_patch_operation(entity=entity, operation=op)

    # Update audit fields regardless of whether changes are detected.
    entity.updated_by = modified_by
    entity.updated_at = datetime.utcnow()

    # Determine which top-level fields actually changed to include in the
    # event payload.  The ``changes`` dict only contains keys for modified
    # attributes to avoid noisy event payloads.
    changes: Dict[str, Any] = {}
    if entity.name != before_name:
        changes["name"] = entity.name
    if entity.data != before_data:
        changes["data"] = entity.data

    try:
        db.commit()
        db.refresh(entity)
    except SQLAlchemyError:
        db.rollback()
        logger.exception(
            "Database error while JSON patching MyEntity id=%s tenant_id=%s",
            my_entity_id,
            tenant_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while applying the patch.",
        )

    # Emit an updated event only if something actually changed.  ``payload`` is
    # generated from the refreshed entity to ensure it reflects the committed
    # state.  ``changes`` contains only the modified keys.
    if changes:
        payload = MyEntityOut.model_validate(entity).model_dump(mode="json")
        MyEntityProducer.send_my_entity_updated(
            tenant_id=tenant_id,
            my_entity_id=my_entity_id,
            changes=changes,
            payload=payload,
        )
    else:
        logger.info("MyEntity has no changes")
    return entity


def _apply_my_entity_patch_operation(
    *,
    entity: MyEntity,
    operation: JsonPatchOperation,
) -> None:
    """
    Apply a single JSON Patch operation to ``entity``.

    The function dispatches based on the destination path and operation type.  It
    supports all RFC 6902 operations for the three allowed paths: ``/name``,
    ``/data``, and nested ``/data/…``.  Unsupported paths still result in a
    ``400 Bad Request``.  Removing or moving from ``/name`` continues to be
    disallowed.

    ``operation`` has already been validated by the schema layer, so ``op`` is
    guaranteed to be one of ``add``, ``replace``, ``remove``, ``move``, ``copy``,
    or ``test``, and the presence or absence of ``value`` and ``from`` follows
    RFC requirements.
    """
    path: str = operation.path
    op: str = operation.op

    # ---------------------------------------------------------------------
    # Helper inner functions
    #
    # These lambdas close over ``entity`` and ``operation`` to avoid passing
    # them explicitly through each branch.  They implement retrieval, setting,
    # and removal for different pointer categories.
    # ---------------------------------------------------------------------
    def get_value(pointer: str) -> Any:
        """
        Retrieve the value at the given JSON Pointer within ``entity``.

        Supports ``/name``, ``/data``, and nested ``/data/…``.  Raises
        ``HTTPException`` for invalid pointers.  Note that a missing key or
        index results in a ``400`` for copy/move contexts and a ``409`` for
        test contexts (handled by the caller).
        """
        if pointer == "/name":
            return entity.name
        if pointer == "/data":
            return entity.data
        if pointer.startswith("/data/"):
            # Data might be None; treat missing container as None
            container = entity.data
            segments = _json_pointer_segments(pointer[len("/data/"):])
            current = container
            for seg in segments:
                if isinstance(current, dict):
                    if seg not in current:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Path not found for get: key '{seg}' does not exist.",
                        )
                    current = current[seg]
                elif isinstance(current, list):
                    idx = _list_index(seg, allow_append=False)
                    if idx < 0 or idx >= len(current):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Path not found for get: index {idx} out of range.",
                        )
                    current = current[idx]
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid JSON Pointer traversal: encountered non-container.",
                    )
            return current
        # Any other pointer is invalid
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid patch path: {pointer}",
        )

    def set_value(dest_path: str, value: Any, op_for_list: str = "add") -> None:
        """
        Set the value at ``dest_path`` within ``entity``.

        ``op_for_list`` indicates the operation context for nested lists; it
        should be ``"add"`` to allow list append (``-``) semantics or
        ``"replace"`` to force replacement at a numeric index.  For copy/move
        we pass ``"add"`` to honour the RFC behaviour.
        """
        if dest_path == "/name":
            # Enforce name constraints: value must be non-empty string
            if not isinstance(value, str) or not value.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="name must be a non-empty string.",
                )
            entity.name = value
            return
        if dest_path == "/data":
            entity.data = value
            flag_modified(entity, "data")
            return
        if dest_path.startswith("/data/"):
            # Initialise data if necessary
            if entity.data is None:
                entity.data = {}
            if not isinstance(entity.data, (dict, list)):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot apply nested /data/* patch because data is not an object/array.",
                )
            segments = _json_pointer_segments(dest_path[len("/data/"):])
            _json_pointer_set(entity.data, segments, value, op=op_for_list)
            flag_modified(entity, "data")
            return
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid patch path: {dest_path}",
        )

    def remove_value(source_path: str) -> None:
        """
        Remove the value at ``source_path`` within ``entity``.

        Removal from ``/name`` is disallowed and will raise HTTPException.
        """
        if source_path == "/name":
            # Consistent with remove semantics: /name cannot be removed
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove required attribute 'name'.",
            )
        if source_path == "/data":
            entity.data = None
            flag_modified(entity, "data")
            return
        if source_path.startswith("/data/"):
            if entity.data is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Path not found for remove: source {source_path} does not exist.",
                )
            segments = _json_pointer_segments(source_path[len("/data/"):])
            _json_pointer_remove(entity.data, segments)
            flag_modified(entity, "data")
            return
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid patch path: {source_path}",
        )

    # ---------------------------------------------------------------------
    # Dispatch based on the operation type and destination path
    # ---------------------------------------------------------------------
    # Test operations run first to ensure precondition before any mutation
    if op == "test":
        try:
            current_value = get_value(path)
        except HTTPException as exc:
            # If the path cannot be resolved for test, treat as mismatch
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Test operation failed: path not found",
            ) from exc
        # Use equality for deep comparison; Python compares lists/dicts by
        # structure.  If mismatched, raise a 409 to indicate the test failed.
        if current_value != operation.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Test operation failed: value mismatch",
            )
        # On success, do nothing and return
        return

    # Copy and move require a source pointer
    if op in {"copy", "move"}:
        from_pointer = operation.from_path  # alias defined in schema
        # Pydantic ensures ``from`` is provided, but double check for safety
        if not from_pointer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'"from" pointer is required for op="{op}"',
            )
        # Disallow moving or copying from /name.  Removing name is not allowed,
        # and copying from name into data could violate type constraints.
        if from_pointer == "/name":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot move or copy from '/name'.",
            )
        # Retrieve the value at the source before any mutation.  deep copy
        # ensures subsequent removals do not affect the stored value.
        source_value = deepcopy(get_value(from_pointer))
        if op == "move":
            # For move operations, perform removal first to mirror RFC 6902
            # semantics (equivalent to remove, then add).  This avoids cases
            # where setting the destination replaces the container in which
            # the source resides (e.g. moving /data/a to /data).
            remove_value(from_pointer)
            set_value(path, source_value, op_for_list="add")
        else:  # copy
            set_value(path, source_value, op_for_list="add")
        return

    # Remove operation simply removes the path and returns
    if op == "remove":
        # Remove from /name is disallowed; remove_value handles enforcement
        remove_value(path)
        return

    # Add/replace operations set the value at the destination
    if op in {"add", "replace"}:
        # For /name, enforce non-empty string; set_value will check
        set_value(path, operation.value, op_for_list=op)
        return

    # If we reach here, op is unsupported for this path.  This fallback
    # preserves the original behaviour where unknown operations yield 400.
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unsupported operation for {path}: {op}",
    )


def _json_pointer_segments(pointer: str) -> List[str]:
    """Decode a JSON Pointer string into unescaped segments."""
    raw_parts = pointer.split("/")
    return [part.replace("~1", "/").replace("~0", "~") for part in raw_parts]


def _json_pointer_set(
    target: Any,
    segments: List[str],
    value: Any,
    op: str,
) -> None:
    """
    Set or add a value inside target (dict or list) following JSON Pointer segments.

    Numeric list indices are honoured, and '-' appends to the list.
    Intermediate structures are created as needed.
    """
    if not segments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON Pointer: empty path.",
        )

    current = target
    for i, seg in enumerate(segments[:-1]):
        nxt = segments[i + 1]
        if isinstance(current, dict):
            if seg not in current or current[seg] is None:
                current[seg] = [] if _looks_like_list_index(nxt) else {}
            current = current[seg]
        elif isinstance(current, list):
            idx = _list_index(seg, allow_append=False)
            _ensure_list_length(current, idx + 1)
            if current[idx] is None:
                current[idx] = [] if _looks_like_list_index(nxt) else {}
            current = current[idx]
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON Pointer traversal: encountered non-container.",
            )

    last = segments[-1]
    if isinstance(current, dict):
        current[last] = value
        return

    if isinstance(current, list):
        if last == "-":
            if op != "add":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail='List append using "-" is only valid for op="add".',
                )
            current.append(value)
        else:
            idx = _list_index(last, allow_append=False)
            _ensure_list_length(current, idx + 1)
            current[idx] = value
        return

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid JSON Pointer set: encountered non-container.",
    )
    
def _json_pointer_remove(target: Any, segments: List[str]) -> None:
    """Remove a value from target (dict or list) following JSON Pointer segments."""
    if not segments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON Pointer: empty path.",
        )

    current = target
    for seg in segments[:-1]:
        if isinstance(current, dict):
            if seg not in current:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Path not found for remove: key '{seg}' does not exist.",
                )
            current = current[seg]
        elif isinstance(current, list):
            idx = _list_index(seg, allow_append=False)
            if idx < 0 or idx >= len(current):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Path not found for remove: index {idx} out of range.",
                )
            current = current[idx]
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON Pointer traversal: encountered non-container.",
            )

    last = segments[-1]
    if isinstance(current, dict):
        if last not in current:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Path not found for remove: key '{last}' does not exist.",
            )
        del current[last]
        return

    if isinstance(current, list):
        if last == "-":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='"-" is not valid for remove.',
            )
        idx = _list_index(last, allow_append=False)
        if idx < 0 or idx >= len(current):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Path not found for remove: index {idx} out of range.",
            )
        current.pop(idx)
        return

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid JSON Pointer remove: encountered non-container.",
    )
    

def _looks_like_list_index(seg: str) -> bool:
    """Return True if the segment looks like a list index or '-' (append)."""
    return seg == "-" or seg.isdigit()

def _list_index(seg: str, allow_append: bool) -> int:
    """
    Convert a pointer segment to a list index.

    If allow_append is True, '-' returns -1; otherwise '-' is invalid.
    """
    if seg == "-":
        if allow_append:
            return -1
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='"-" is not allowed in this context.',
        )
    if not seg.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid list index in JSON Pointer: '{seg}'",
        )
    return int(seg)


def _ensure_list_length(lst: list, size: int) -> None:
    """Extend a list with None values until it reaches the given size."""
    while len(lst) < size:
        lst.append(None)