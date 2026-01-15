"""
Service package initialiser.

Import service functions here for convenient access in other parts of
the codebase.  When adding a new domain service expose its public
functions in ``__all__`` so they are discoverable via
``app.domain.services``.
"""

from .health_service import get_liveness, get_readiness  # noqa: F401

# Import FormCatalogCategory service functions
from .form_catalog_category_service import (
    create_form_catalog_category,
    get_form_catalog_category,
    list_form_catalog_categories,
    update_form_catalog_category,
    delete_form_catalog_category,
)  # noqa: F401

# Import FieldDef service functions
from .field_def_service import (
    create_field_def,
    get_field_def,
    list_field_defs,
    update_field_def,
    delete_field_def,
)  # noqa: F401

# Import FieldDefOption service functions
from .field_def_option_service import (
    create_field_def_option,
    get_field_def_option,
    list_field_def_options,
    update_field_def_option,
    delete_field_def_option,
)  # noqa: F401

# Import Component service functions
from .component_service import (
    create_component,
    get_component,
    list_components,
    update_component,
    delete_component,
)  # noqa: F401

# Import ComponentPanel service functions
from .component_panel_service import (
    create_component_panel,
    get_component_panel,
    list_component_panels,
    update_component_panel,
    delete_component_panel,
)  # noqa: F401

# Import ComponentPanelField service functions
from .component_panel_field_service import (
    create_component_panel_field,
    get_component_panel_field,
    list_component_panel_fields,
    update_component_panel_field,
    delete_component_panel_field,
)  # noqa: F401

# Import Form service functions
from .form_service import (
    create_form,
    get_form,
    list_forms,
    update_form,
    delete_form,
)  # noqa: F401

# Import FormPanel service functions
from .form_panel_service import (
    create_form_panel,
    get_form_panel,
    list_form_panels,
    update_form_panel,
    delete_form_panel,
)  # noqa: F401

# Import FormPanelComponent service functions
from .form_panel_component_service import (
    create_form_panel_component,
    get_form_panel_component,
    list_form_panel_components,
    update_form_panel_component,
    delete_form_panel_component,
)  # noqa: F401

# Import FormPanelField service functions
from .form_panel_field_service import (
    create_form_panel_field,
    get_form_panel_field,
    list_form_panel_fields,
    update_form_panel_field,
    delete_form_panel_field,
)  # noqa: F401

# Import FormSubmission service functions
from .form_submission_service import (
    create_form_submission,
    get_form_submission,
    list_form_submissions,
    update_form_submission,
    delete_form_submission,
)  # noqa: F401

# Import FormSubmissionValue service functions
from .form_submission_value_service import (
    create_form_submission_value,
    get_form_submission_value,
    list_form_submission_values,
    update_form_submission_value,
    delete_form_submission_value,
)  # noqa: F401

__all__ = [
    "get_liveness",
    "get_readiness",

    # FormCatalogCategory
    "create_form_catalog_category",
    "get_form_catalog_category",
    "list_form_catalog_categories",
    "update_form_catalog_category",
    "delete_form_catalog_category",

    # FieldDef
    "create_field_def",
    "get_field_def",
    "list_field_defs",
    "update_field_def",
    "delete_field_def",

    # FieldDefOption
    "create_field_def_option",
    "get_field_def_option",
    "list_field_def_options",
    "update_field_def_option",
    "delete_field_def_option",

    # Component
    "create_component",
    "get_component",
    "list_components",
    "update_component",
    "delete_component",

    # ComponentPanel
    "create_component_panel",
    "get_component_panel",
    "list_component_panels",
    "update_component_panel",
    "delete_component_panel",

    # ComponentPanelField
    "create_component_panel_field",
    "get_component_panel_field",
    "list_component_panel_fields",
    "update_component_panel_field",
    "delete_component_panel_field",

    # Form
    "create_form",
    "get_form",
    "list_forms",
    "update_form",
    "delete_form",

    # FormPanel
    "create_form_panel",
    "get_form_panel",
    "list_form_panels",
    "update_form_panel",
    "delete_form_panel",

    # FormPanelComponent
    "create_form_panel_component",
    "get_form_panel_component",
    "list_form_panel_components",
    "update_form_panel_component",
    "delete_form_panel_component",

    # FormPanelField
    "create_form_panel_field",
    "get_form_panel_field",
    "list_form_panel_fields",
    "update_form_panel_field",
    "delete_form_panel_field",

    # FormSubmission
    "create_form_submission",
    "get_form_submission",
    "list_form_submissions",
    "update_form_submission",
    "delete_form_submission",

    # FormSubmissionValue
    "create_form_submission_value",
    "get_form_submission_value",
    "list_form_submission_values",
    "update_form_submission_value",
    "delete_form_submission_value",
]