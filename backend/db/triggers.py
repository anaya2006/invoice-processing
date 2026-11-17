# backend/db/triggers.py
"""SQLite triggers to enforce append‑only audit_events.
These triggers are idempotent: they are created at start‑up if not already present.
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from .session import engine

def create_audit_triggers():
    # BEFORE UPDATE on audit_events
    stmt_update = text('''
    CREATE TRIGGER IF NOT EXISTS audit_events_before_update
    BEFORE UPDATE ON audit_events
    BEGIN
        SELECT RAISE(ABORT, 'audit_events is append-only');
    END;
    ''')
    # BEFORE DELETE on audit_events
    stmt_delete = text('''
    CREATE TRIGGER IF NOT EXISTS audit_events_before_delete
    BEFORE DELETE ON audit_events
    BEGIN
        SELECT RAISE(ABORT, 'audit_events is append-only');
    END;
    ''')
    with engine.begin() as conn:
        try:
            conn.execute(stmt_update)
            conn.execute(stmt_delete)
        except OperationalError:
            # Table may not exist yet; ignore until migrations run.
            pass

# Run at import time so triggers are present when the app starts, but safely ignore missing tables.
create_audit_triggers()
