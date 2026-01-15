"""
Event schema package.

This package defines the message payloads for domain events along with
the common ``EventEnvelope`` wrapper.  When adding new domain events
create a new module (e.g. ``schema_composition_events.py``) and import the
message classes here so that producers and consumers can reference
them.
"""

from .common import EventEnvelope  # noqa: F401

from .form_catalog_category_events import (
    FormCatalogCategoryCreatedMessage,
    FormCatalogCategoryUpdatedMessage,
    FormCatalogCategoryDeletedMessage,
)  # noqa: F401
from .field_def_events import (
    FieldDefCreatedMessage,
    FieldDefUpdatedMessage,
    FieldDefDeletedMessage,
)  # noqa: F401
from .field_def_option_events import (
    FieldDefOptionCreatedMessage,
    FieldDefOptionUpdatedMessage,
    FieldDefOptionDeletedMessage,
)  # noqa: F401
from .component_events import (
    ComponentCreatedMessage,
    ComponentUpdatedMessage,
    ComponentDeletedMessage,
)  # noqa: F401
from .component_panel_events import (
    ComponentPanelCreatedMessage,
    ComponentPanelUpdatedMessage,
    ComponentPanelDeletedMessage,
)  # noqa: F401
from .component_panel_field_events import (
    ComponentPanelFieldCreatedMessage,
    ComponentPanelFieldUpdatedMessage,
    ComponentPanelFieldDeletedMessage,
)  # noqa: F401
from .form_events import (
    FormCreatedMessage,
    FormUpdatedMessage,
    FormDeletedMessage,
)  # noqa: F401
from .form_panel_events import (
    FormPanelCreatedMessage,
    FormPanelUpdatedMessage,
    FormPanelDeletedMessage,
)  # noqa: F401
from .form_panel_component_events import (
    FormPanelComponentCreatedMessage,
    FormPanelComponentUpdatedMessage,
    FormPanelComponentDeletedMessage,
)  # noqa: F401
from .form_panel_field_events import (
    FormPanelFieldCreatedMessage,
    FormPanelFieldUpdatedMessage,
    FormPanelFieldDeletedMessage,
)  # noqa: F401
from .form_submission_events import (
    FormSubmissionCreatedMessage,
    FormSubmissionUpdatedMessage,
    FormSubmissionDeletedMessage,
)  # noqa: F401
from .form_submission_value_events import (
    FormSubmissionValueCreatedMessage,
    FormSubmissionValueUpdatedMessage,
    FormSubmissionValueDeletedMessage,
)  # noqa: F401

__all__ = [
    "EventEnvelope",
    "FormCatalogCategoryCreatedMessage",
    "FormCatalogCategoryUpdatedMessage",
    "FormCatalogCategoryDeletedMessage",
    "FieldDefCreatedMessage",
    "FieldDefUpdatedMessage",
    "FieldDefDeletedMessage",
    "FieldDefOptionCreatedMessage",
    "FieldDefOptionUpdatedMessage",
    "FieldDefOptionDeletedMessage",
    "ComponentCreatedMessage",
    "ComponentUpdatedMessage",
    "ComponentDeletedMessage",
    "ComponentPanelCreatedMessage",
    "ComponentPanelUpdatedMessage",
    "ComponentPanelDeletedMessage",
    "ComponentPanelFieldCreatedMessage",
    "ComponentPanelFieldUpdatedMessage",
    "ComponentPanelFieldDeletedMessage",
    "FormCreatedMessage",
    "FormUpdatedMessage",
    "FormDeletedMessage",
    "FormPanelCreatedMessage",
    "FormPanelUpdatedMessage",
    "FormPanelDeletedMessage",
    "FormPanelComponentCreatedMessage",
    "FormPanelComponentUpdatedMessage",
    "FormPanelComponentDeletedMessage",
    "FormPanelFieldCreatedMessage",
    "FormPanelFieldUpdatedMessage",
    "FormPanelFieldDeletedMessage",
    "FormSubmissionCreatedMessage",
    "FormSubmissionUpdatedMessage",
    "FormSubmissionDeletedMessage",
    "FormSubmissionValueCreatedMessage",
    "FormSubmissionValueUpdatedMessage",
    "FormSubmissionValueDeletedMessage",
]