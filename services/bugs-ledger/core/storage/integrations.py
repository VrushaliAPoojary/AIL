"""
core/storage/integrations.py

Persistence adapter for external engineering systems integrations (e.g. Azure DevOps).
Maintains idempotency and stores external system identifiers against investigations.
"""

import sqlite3
import json
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any


DDL_EXTERNAL_WORK_ITEMS = """
CREATE TABLE IF NOT EXISTS external_work_items (
    id TEXT PRIMARY KEY,
    investigation_key TEXT NOT NULL,
    system TEXT NOT NULL,
    external_id TEXT NOT NULL,
    external_url TEXT NULL,
    created_at TEXT NOT NULL,
    metadata_json TEXT NULL,
    
    FOREIGN KEY (investigation_key) REFERENCES investigations(record_key) ON DELETE RESTRICT,
    CONSTRAINT uq_external_inv_system UNIQUE (investigation_key, system)
);

CREATE INDEX IF NOT EXISTS idx_ext_wi_inv ON external_work_items(investigation_key);
CREATE INDEX IF NOT EXISTS idx_ext_wi_ext_id ON external_work_items(system, external_id);
"""


def ensure_external_work_items_table(conn: sqlite3.Connection) -> None:
    """Creates the external_work_items table if it does not exist."""
    cursor = conn.cursor()
    cursor.executescript(DDL_EXTERNAL_WORK_ITEMS)
    conn.commit()


def get_external_work_item(conn: sqlite3.Connection, investigation_key: str, system: str = "AZURE_DEVOPS") -> Optional[Dict[str, Any]]:
    """Retrieves an existing external work item reference for the investigation."""
    ensure_external_work_items_table(conn)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM external_work_items WHERE investigation_key = ? AND system = ?;",
        (investigation_key, system)
    )
    row = cursor.fetchone()
    return dict(row) if row else None


def record_external_work_item(
    conn: sqlite3.Connection,
    investigation_key: str,
    external_id: str,
    external_url: Optional[str] = None,
    system: str = "AZURE_DEVOPS",
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Atomically records an external work item ID.
    Enforces uniqueness on (investigation_key, system).
    """
    ensure_external_work_items_table(conn)
    now = datetime.now(timezone.utc).isoformat()
    record_id = f"EWI-{uuid.uuid4().hex[:12].upper()}"
    metadata_str = json.dumps(metadata) if metadata else None

    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO external_work_items (
            id, investigation_key, system, external_id, external_url, created_at, metadata_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(investigation_key, system) DO NOTHING;
        """,
        (record_id, investigation_key, system, external_id, external_url, now, metadata_str)
    )
    conn.commit()
    return get_external_work_item(conn, investigation_key, system)
