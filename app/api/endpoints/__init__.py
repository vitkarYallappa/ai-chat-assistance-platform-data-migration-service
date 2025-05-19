"""
__init__.py for API endpoints package.

Imports all endpoint modules to make them available when the package is imported.
"""

from app.api.endpoints import admin, migrations, status

__all__ = ["admin", "migrations", "status"]