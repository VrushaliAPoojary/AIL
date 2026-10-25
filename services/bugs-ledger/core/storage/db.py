"""
core/storage/db.py

Phase 01G — SQLite Connection & Atomic Allocator
Provides:
- Configurable SQLite connection helper with PRAGMA foreign_keys = ON, WAL mode, and busy timeout.
- Atomic database-backed business ID allocation for INV-<YYYYMMDD>-#### and ART-<MODULE>-###.
- Legacy sequence seeding primitive (ensure_minimum_sequence).
"""

import sqlite3
import re


def get_connection(db_path: str, timeout_seconds: float = 10.0) -> sqlite3.Connection:
    """
    Creates and configures an SQLite connection.
    Enforces foreign keys, WAL mode (for file databases), and busy timeout.
    """
    conn = sqlite3.connect(db_path, timeout=timeout_seconds, isolation_level=None)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # Enable WAL mode if not an in-memory database
    if db_path != ":memory:":
        cursor.execute("PRAGMA journal_mode = WAL;")
    
    timeout_ms = int(timeout_seconds * 1000)
    cursor.execute(f"PRAGMA busy_timeout = {timeout_ms};")
    return conn


class AtomicIdAllocator:
    """
    Allocates sequential business IDs using atomic UPSERT operations on the id_allocations table.
    
    Scopes:
    - INV:YYYYMMDD -> formats as INV-<YYYYMMDD>-<4-DIGIT-SEQUENCE>
    - BUG:<MODULE> -> formats as ART-<MODULE>-<3-DIGIT-SEQUENCE>
    
    Rollback Semantics:
    Because allocation operates inside SQLite write transactions, if the transaction enclosing
    the allocation fails and rolls back, the sequence update in id_allocations also rolls back.
    This guarantees zero collisions and consistency between business IDs and committed investigations.
    """

    @staticmethod
    def allocate_investigation_id(conn: sqlite3.Connection, date_str: str) -> str:
        """
        Atomically allocates the next sequential Investigation ID for date YYYYMMDD.
        Format: INV-YYYYMMDD-0001
        """
        if not re.match(r"^\d{8}$", date_str):
            raise ValueError(f"Invalid date_str format '{date_str}'. Expected YYYYMMDD.")
        
        scope = f"INV:{date_str}"
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO id_allocations (scope, last_seq) VALUES (?, 1)
            ON CONFLICT(scope) DO UPDATE SET last_seq = id_allocations.last_seq + 1
            RETURNING last_seq;
            """,
            (scope,)
        )
        row = cursor.fetchone()
        seq = row[0]
        if seq > 9999:
            raise OverflowError(f"Sequence overflow for date {date_str}. Exceeded 9999.")
        return f"INV-{date_str}-{seq:04d}"

    @staticmethod
    def allocate_bug_id(
        conn: sqlite3.Connection,
        module: str,
        prefix: str = "ART",
        is_test: bool = False
    ) -> str:
        """
        Atomically allocates the next sequential Canonical ART Bug ID for an approved module.
        Format: ART-<MODULE>-001 or TEST-ART-<MODULE>-001
        """
        if not module or not isinstance(module, str):
            raise ValueError("Module must be a non-empty string.")
        
        module_norm = module.strip().upper()
        if module_norm == "NOT PROVIDED":
            raise ValueError("Cannot allocate bug ID for 'Not provided' module.")
        
        effective_prefix = "TEST-ART" if is_test else (prefix or "ART").strip().upper()
        scope = f"BUG:{effective_prefix}:{module_norm}" if effective_prefix != "ART" else f"BUG:{module_norm}"
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO id_allocations (scope, last_seq) VALUES (?, 1)
            ON CONFLICT(scope) DO UPDATE SET last_seq = id_allocations.last_seq + 1
            RETURNING last_seq;
            """,
            (scope,)
        )
        row = cursor.fetchone()
        seq = row[0]
        if seq > 999:
            raise OverflowError(f"Sequence overflow for module '{module_norm}'. Exceeded 999.")
        return f"{effective_prefix}-{module_norm}-{seq:03d}"

    @staticmethod
    def allocate_feature_id(
        conn: sqlite3.Connection,
        module: str,
        prefix: str = "ART-FEAT",
        is_test: bool = False
    ) -> str:
        """
        Atomically allocates the next sequential Canonical ART Feature ID for an approved module.
        Format: ART-FEAT-<MODULE>-001 or TEST-ART-FEAT-<MODULE>-001
        """
        if not module or not isinstance(module, str):
            raise ValueError("Module must be a non-empty string.")
        
        from core.identity.generator import FEATURE_MODULE_CODES
        raw_mod = module.strip().upper()
        module_norm = FEATURE_MODULE_CODES.get(raw_mod, raw_mod)
        if module_norm == "NOT PROVIDED":
            raise ValueError("Cannot allocate feature ID for 'Not provided' module.")
        
        effective_prefix = "TEST-ART-FEAT" if is_test else (prefix or "ART-FEAT").strip().upper()
        scope = f"FEAT:{effective_prefix}:{module_norm}" if effective_prefix != "ART-FEAT" else f"FEAT:{module_norm}"
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO id_allocations (scope, last_seq) VALUES (?, 1)
            ON CONFLICT(scope) DO UPDATE SET last_seq = id_allocations.last_seq + 1
            RETURNING last_seq;
            """,
            (scope,)
        )
        row = cursor.fetchone()
        seq = row[0]
        if seq > 999:
            raise OverflowError(f"Sequence overflow for feature module '{module_norm}'. Exceeded 999.")
        return f"{effective_prefix}-{module_norm}-{seq:03d}"

    @staticmethod
    def ensure_minimum_sequence(conn: sqlite3.Connection, scope: str, min_seq: int) -> int:
        """
        Safely seeds or advances an allocation scope to at least min_seq.
        - If scope is absent -> initializes to min_seq.
        - If current < min_seq -> advances to min_seq.
        - If current >= min_seq -> remains unchanged.
        Returns the resulting last_seq.
        """
        if not scope or not isinstance(scope, str):
            raise ValueError("Scope must be a non-empty string.")
        if min_seq < 0:
            raise ValueError("min_seq cannot be negative.")

        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO id_allocations (scope, last_seq) VALUES (?, ?)
            ON CONFLICT(scope) DO UPDATE SET 
                last_seq = CASE 
                    WHEN id_allocations.last_seq < excluded.last_seq THEN excluded.last_seq 
                    ELSE id_allocations.last_seq 
                END
            RETURNING last_seq;
            """,
            (scope, min_seq)
        )
        row = cursor.fetchone()
        return row[0]
