"""
Template loader for ``ACTIVE_THEME`` (WordPress-style active theme).

Searched *before* project filesystem templates so runtime theme switch
overrides copy-on-create kit files without re-running nova-project.
"""

from django.template.loaders import filesystem

from mezzanine.kits.theme import active_theme_template_dir


class Loader(filesystem.Loader):
    def get_dirs(self):
        theme_dir = active_theme_template_dir()
        if theme_dir:
            return [theme_dir]
        return []
