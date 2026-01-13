# Analysis – Tests

This document describes the new tests added to the `tests` package to
exercise the newly implemented domains.

## Overview

The starter project included tests for the `MyEntity` domain across both
the API and service layers.  Building on that pattern, API tests were
added for every new domain introduced from the simplified DDL.  These
tests focus on the routing layer and verify that each endpoint forwards
arguments correctly to the service layer and wraps responses in the
appropriate pagination envelope.

## API Tests

The following test modules reside in `tests/api` and cover all CRUD
endpoints for the new domains:

| Module | Domain | Purpose |
|-------|--------|---------|
| `test_form_catalog_category.py` | FormCatalogCategory | Verifies list, create, get, update and delete routes call the category service with correct arguments and wrap responses. |
| `test_field_def.py` | FieldDef | Ensures the field definition routes delegate to the service functions with tenant scope and wrap paginated lists. |
| `test_field_def_option.py` | FieldDefOption | Confirms option routes handle filtering by `field_def_id`, use the current user’s subject for `created_by`/`modified_by` fields, and return service results unchanged. |
| `test_component.py` | Component | Tests that component routes forward business keys and version information, capture the user performing the action and wrap list responses. |
| `test_component_panel.py` | ComponentPanel | Validates that panel routes accept optional filters by component and parent panel, propagate audit information and wrap paginated results. |
| `test_component_panel_field.py` | ComponentPanelField | Checks that panel field routes pass through parent IDs, field IDs, override data and ordering and that responses are returned as provided. |
| `test_form.py` | Form | Verifies that form routes pass along business keys, handle creation and updates with audit metadata and wrap list responses with pagination. |
| `test_form_panel.py` | FormPanel | Tests that panel routes accept optional parent panel filters, propagate audit information and wrap lists. |
| `test_form_panel_component.py` | FormPanelComponent | Confirms that embedded component routes handle panel and component IDs, configuration overrides, and audit fields correctly. |
| `test_form_panel_field.py` | FormPanelField | Ensures that ad hoc field routes pass through parent panel and field IDs, override data and ordering and wrap responses. |
| `test_form_submission.py` | FormSubmission | Verifies that submission routes handle form IDs, submission status transitions, audit fields and paginated lists. |
| `test_form_submission_value.py` | FormSubmissionValue | Checks that submission value routes propagate submission IDs, field instance paths, JSON values and audit metadata and wrap results. |

Each module uses `pytest.MonkeyPatch` to replace service functions with
test doubles that capture the arguments they receive and return
predefined values.  A simple `DummySession` type stands in for a real
database session so that tests can run without a database.  The tests
assert that the route functions:

* Pass the correct tenant ID, identifiers, filter parameters and payloads
  to the service layer.
* Use the authenticated user’s `sub` claim as the `created_by` or
  `modified_by` actor when these fields are omitted by the client.
* Wrap lists of domain objects in the corresponding `ListResponse`
  envelope with total counts, limits and offsets.

These API tests provide confidence that the routing layer correctly wires
to the service layer across all domains.  Integration tests that
exercise the service layer against a test database and verify event
publication could be added in the future to increase coverage.

## Pending Tests

At present there are no outstanding API test gaps for the domains
introduced in this iteration.  Future work could include service layer
tests and integration tests to validate database interactions and
messaging behaviours.