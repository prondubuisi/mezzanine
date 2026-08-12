"""
Shared bootstrap / seed defaults.

Single source for createdb, site-clone seed commands, and the project
template password floor (DESIGN.md Amendment 2 H2 / H4). No Django
imports so project settings can read these during load.
"""

DEFAULT_SUPERUSER_USERNAME = "admin"
DEFAULT_SUPERUSER_EMAIL = "example@example.com"
DEFAULT_SUPERUSER_PASSWORD = "default"

# Keep in lockstep with accounts form validation and AUTH_PASSWORD_VALIDATORS.
ACCOUNTS_MIN_PASSWORD_LENGTH = 12
