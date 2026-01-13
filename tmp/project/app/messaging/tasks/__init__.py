"""Celery task package for message bus consumers.

This package exposes all Celery tasks defined in submodules so that
``celery_app.autodiscover_tasks(['app.messaging'])`` will find them.  It
explicitly imports tasks from form session, action, and engagement modules.
"""

# Import all task modules so Celery autodiscovery can find them
from .my_entity_tasks import *  # noqa: F401,F403
from .form_catalog_category_tasks import *  # noqa: F401,F403
from .field_def_tasks import *  # noqa: F401,F403
from .field_def_option_tasks import *  # noqa: F401,F403
from .component_tasks import *  # noqa: F401,F403
from .component_panel_tasks import *  # noqa: F401,F403
from .component_panel_field_tasks import *  # noqa: F401,F403
from .form_tasks import *  # noqa: F401,F403
from .form_panel_tasks import *  # noqa: F401,F403
from .form_panel_component_tasks import *  # noqa: F401,F403
from .form_panel_field_tasks import *  # noqa: F401,F403
from .form_submission_tasks import *  # noqa: F401,F403
from .form_submission_value_tasks import *  # noqa: F401,F403