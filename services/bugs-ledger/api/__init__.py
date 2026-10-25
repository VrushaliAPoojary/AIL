"""
api/__init__.py

Exposes application factory.
"""

from api.app import create_app

__all__ = ["create_app"]
