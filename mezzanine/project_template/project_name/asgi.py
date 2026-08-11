"""
ASGI config for {{ project_name }} project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/{{ docs_version }}/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

from mezzanine.utils.conf import real_project_name

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "%s.settings" % real_project_name("{{ project_name }}")
)

application = get_asgi_application()
