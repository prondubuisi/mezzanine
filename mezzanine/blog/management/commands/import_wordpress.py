"""Deprecated location — command lives in mezzanine.migrate."""

from mezzanine.migrate.management.commands.import_wordpress import (  # noqa: F401
    Command,
)

__all__ = ["Command"]
