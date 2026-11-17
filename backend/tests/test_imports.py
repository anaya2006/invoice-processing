# tests/test_imports.py
"""Basic import sanity checks for the core packages.
Ensures that all scaffolded modules can be imported and that the DB engine
and audit‑event triggers initialise without error.
"""
import os
import sys
import importlib
from sqlalchemy import text


# Add the project root (backend/.. ) to sys.path so "core", "db", and "models"
# can be imported as top‑level packages.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

MODULES = [
    "backend.core.config",
    "backend.core.roles",
    "backend.core.money",
    "backend.core.errors",
    "backend.db.base",
    "backend.db.session",
    "backend.models.user",
    "backend.models.vendor",
    "backend.models.purchase_order",
    "backend.models.invoice",
    "backend.models.extracted_field",
    "backend.models.exception",
    "backend.models.audit_event",
]

def test_imports():
    """Import each module to verify that there are no syntax or import errors."""
    for mod in MODULES:
        importlib.import_module(mod)

def test_db_engine_and_triggers():
    """Check that the SQLite engine can execute a simple query and that the audit triggers are created."""
    from backend.db.session import engine
    from backend.db.triggers import create_audit_triggers

    # Simple query to ensure the connection works using a text clause
    with engine.begin() as conn:
        conn.execute(text("SELECT 1"))

    # Create (or recreate) the audit triggers – should be idempotent
    create_audit_triggers()
