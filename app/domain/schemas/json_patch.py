from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class JsonPatchOperation(BaseModel):
    """
    Represents a single JSON Patch operation (RFC 6902 - JSON Patch).

    JSON Patch allows a client to describe changes to a JSON document using a
    sequence of operations. Each operation targets a `path` expressed as a JSON
    Pointer (RFC 6901).

    Supported operations in the RFC:
      - add
      - remove
      - replace
      - move
      - copy
      - test

    High-level semantics (practical view):
      - add:     create/insert a value at `path` (or append to array via `/-`)
      - remove:  delete the value at `path`
      - replace: overwrite the value at `path`
      - move:    relocate a value from `from` -> `path` (like copy + remove)
      - copy:    duplicate a value from `from` -> `path`
      - test:    assert the value at `path` equals `value` (no mutation)

    IMPORTANT (for service layer implementers):
    ------------------------------------------
    This schema module only validates the *shape* and basic rules of patch
    operations. It does NOT apply operations to any domain object.
    Enforcement of:
      - allowed paths (e.g. only "/name" and "/data/*"),
      - domain-specific constraints,
      - "test" comparison semantics,
      - array bounds behavior,
    must happen in the service layer that applies the patch.

    Notes on JSON Pointer paths:
      - Must start with "/"
      - Segments are separated by "/"
      - "~1" represents "/" and "~0" represents "~" within segments
      - Trailing "/" is disallowed here because it introduces an empty segment
        that tends to be ambiguous and almost always accidental (e.g. "/data/").
    """

    op: str = Field(
        ...,
        description='JSON Patch op. One of: "add", "remove", "replace", "move", "copy", "test".',
    )

    path: str = Field(
        ...,
        description='JSON Pointer path (RFC 6901), e.g. "/name", "/data/foo", "/data/items/0".',
    )

    # `from` is only meaningful for move/copy. We keep it optional because it is
    # invalid for other operations, and validated conditionally below.
    #
    # NOTE: "from" is a reserved keyword in Python, but as a Pydantic field name
    # it is allowed. If you later need to access this attribute in code,
    # you will use `operation.from_` if you define an alias. Here we keep it as
    # "from" to match the RFC and typical JSON Patch payloads.
    from_path: Optional[str] = Field(
        default=None,
        alias="from",
        description='Source JSON Pointer path used by "move" and "copy". RFC field name is "from".',
    )

    # `value` is used by add/replace/test. It must be omitted/null for remove.
    # For move/copy, value is not used and should be omitted/null.
    value: Optional[Any] = Field(
        default=None,
        description='Value for "add", "replace", and "test". Must be omitted/null for "remove", "move", "copy".',
    )

    @field_validator("op")
    @classmethod
    def validate_op(cls, v: str) -> str:
        """
        Normalize and validate the operation.

        We normalize to lower-case and trim whitespace so callers can send
        "Add", " ADD ", etc. and still be accepted.

        The returned value is always one of the canonical lower-case RFC ops.
        """
        v2 = (v or "").strip().lower()
        allowed = {"add", "remove", "replace", "move", "copy", "test"}
        if v2 not in allowed:
            raise ValueError(
                'op must be one of: "add", "remove", "replace", "move", "copy", "test"'
            )
        return v2

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        """
        Validate the target path as a JSON Pointer-like string.

        This does not attempt to fully validate RFC 6901 (e.g. "~" escape rules),
        because many implementations allow unescaped segment values and handle
        escaping during pointer traversal. We enforce the basics that prevent
        common bugs and ambiguity:
          - must be a non-empty string
          - must start with "/"
          - must not end with "/" (unless it is exactly "/")
        """
        if not v or not isinstance(v, str):
            raise ValueError("path must be a non-empty string")
        if not v.startswith("/"):
            raise ValueError('path must start with "/" (JSON Pointer)')
        # Disallow trailing slash to avoid ambiguous empty segments like "/data/"
        if len(v) > 1 and v.endswith("/"):
            raise ValueError("path must not end with '/'")
        return v

    @field_validator("from_path")
    @classmethod
    def validate_from_path(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate the `from` path (used by move/copy) if provided.

        The same basic JSON Pointer validations apply as for `path`.
        """
        if v is None:
            return None
        if not isinstance(v, str) or not v:
            raise ValueError('"from" must be a non-empty string when provided')
        if not v.startswith("/"):
            raise ValueError('"from" must start with "/" (JSON Pointer)')
        if len(v) > 1 and v.endswith("/"):
            raise ValueError('"from" must not end with "/"')
        return v

    @model_validator(mode="after")
    def validate_operation_rules(self) -> "JsonPatchOperation":
        """
        Enforce RFC-style field requirements based on the operation.

        This validator focuses on "field presence" rules, which are the main
        cause of runtime surprises if left unchecked.

        - add / replace:
            - require `value`
            - must not specify `from`
        - remove:
            - must not specify `value` (null tolerated, non-null rejected)
            - must not specify `from`
        - move / copy:
            - require `from`
            - must not specify `value` (null tolerated, non-null rejected)
        - test:
            - require `value`
            - must not specify `from`

        NOTE ABOUT "test":
        ------------------
        "test" is an assertion operation. It does not mutate the document.
        When applying JSON Patch, if the value at `path` does not match `value`,
        the patch application fails (typically aborting the whole patch sequence)
        and no subsequent operations should be applied.

        In other words:
          - "test" is a guard / precondition
          - it is used for optimistic concurrency-like semantics at the document level
          - it prevents applying changes if the document is not in the expected state
        """
        op = self.op

        # Helper booleans to keep the logic readable.
        has_value = self.value is not None
        has_from = self.from_path is not None

        if op in {"add", "replace"}:
            if not has_value:
                raise ValueError(f'value is required for op="{op}"')
            if has_from:
                raise ValueError(f'"from" is not allowed for op="{op}"')
            return self

        if op == "remove":
            # We tolerate null but reject any non-null value.
            if has_value:
                raise ValueError('value must be omitted/null for op="remove"')
            if has_from:
                raise ValueError('"from" is not allowed for op="remove"')
            return self

        if op in {"move", "copy"}:
            if not has_from:
                raise ValueError(f'"from" is required for op="{op}"')
            # As above: tolerate null, reject any explicit non-null value.
            if has_value:
                raise ValueError(f'value must be omitted/null for op="{op}"')
            return self

        if op == "test":
            if not has_value:
                raise ValueError('value is required for op="test"')
            if has_from:
                raise ValueError('"from" is not allowed for op="test"')
            return self

        # Defensive: validate_op already restricts values, but keep this to avoid
        # silent acceptance if code is modified in the future.
        raise ValueError(f"Unsupported op: {op}")


class JsonPatchRequest(BaseModel):
    """
    Schema for a JSON Patch request containing multiple operations.

    Important behavior note:
    - RFC 6902 treats a JSON Patch document (the list of operations) as an
      ordered sequence. Operations must be applied in order.
    - If any operation fails (including a "test" failure), the patch application
      should fail as a whole (commonly meaning: no partial updates).

    This class enforces that at least one operation is present. Any deeper rules
    (like limiting patch size or restricting allowed paths) should be handled at
    the API/service layer.
    """

    operations: List[JsonPatchOperation] = Field(
        ...,
        min_length=1,
        description="Ordered list of JSON Patch operations (RFC 6902).",
    )
