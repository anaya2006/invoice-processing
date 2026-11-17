"""Reset the SQLite database.
Deletes the existing `ana.db` file (or drops all tables) and recreates the schema.
Used during development and for the demo seeding script.
"""

import os
from pathlib import Path

from ..db.base import Base
from ..db.session import engine
from ..db.triggers import create_audit_triggers

def reset_db():
    """Drop all tables and recreate them.
    This works for SQLite by dropping the file if it exists, then calling
    ``Base.metadata.create_all``. For other DBs you could reflect and drop.
    """
    db_path = Path(engine.url.database)  # type: ignore[attr-defined]
    if db_path.exists():
        db_path.unlink()
        print(f"Deleted existing DB at {db_path}")
    # Recreate tables
    Base.metadata.create_all(bind=engine)
    # Ensure audit triggers exist
    create_audit_triggers()
    print("Database reset and tables created.")

if __name__ == "__main__":
    reset_db()
