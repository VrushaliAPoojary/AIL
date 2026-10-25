"""
core/storage/schema.py

Phase 01G — SQLite Schema Definition
Defines the frozen 10-table persistence model for the ART Product Resolution System.

Safety constraints:
- All child tables reference investigations.record_key (internal persistence primary key).
- Unique business identifiers: investigation_id (when non-null), canonical_bug_id (when non-null).
- source_kind strictly constrained to ('NATIVE', 'LEGACY_IMPORT').
- Enums match frozen contracts exactly, with 'Not provided' supported where appropriate.
- Evidence allows duplicate byte content (SHA-256 is non-unique).
- PRAGMA foreign_keys = ON enforced.
"""

DDL_STATEMENTS = """
-- 1. Atomic sequence counters
CREATE TABLE IF NOT EXISTS id_allocations (
    scope TEXT PRIMARY KEY,
    last_seq INTEGER NOT NULL
);

-- 2. Investigations (Aggregate Root)
CREATE TABLE IF NOT EXISTS investigations (
    record_key TEXT PRIMARY KEY,
    investigation_id TEXT NULL,
    canonical_bug_id TEXT NULL,
    source_kind TEXT NOT NULL,
    slug TEXT NOT NULL,
    lifecycle_phase TEXT NOT NULL,
    status TEXT NULL,
    classification TEXT NULL,
    module TEXT NOT NULL DEFAULT 'Not provided',
    severity TEXT NOT NULL DEFAULT 'Not provided',
    priority TEXT NOT NULL DEFAULT 'Not provided',
    assignee TEXT NULL,
    original_input_id TEXT NOT NULL,
    active_ticket_id TEXT NULL,
    resolution_json TEXT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    
    CONSTRAINT uq_inv_investigation_id UNIQUE (investigation_id),
    CONSTRAINT uq_inv_canonical_bug_id UNIQUE (canonical_bug_id),
    CONSTRAINT chk_inv_source_kind CHECK (source_kind IN ('NATIVE', 'LEGACY_IMPORT')),
    CONSTRAINT chk_inv_lifecycle_phase CHECK (lifecycle_phase IN ('CAPTURE', 'INVESTIGATING', 'CONFIRMED', 'RESOLVED')),
    CONSTRAINT chk_inv_status CHECK (status IS NULL OR status IN ('OPEN', 'FIXING', 'RETEST', 'VERIFIED', 'CLOSED', 'BLOCKED')),
    CONSTRAINT chk_inv_classification CHECK (classification IS NULL OR classification IN ('BUG', 'PRODUCT_IMPROVEMENT', 'COMPETITOR_INSIGHT', 'PRODUCT_CONCEPT')),
    CONSTRAINT chk_inv_severity CHECK (severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'Not provided')),
    CONSTRAINT chk_inv_priority CHECK (priority IN ('P0', 'P1', 'P2', 'P3', 'Not provided'))
);

CREATE INDEX IF NOT EXISTS idx_inv_phase_status ON investigations(lifecycle_phase, status);
CREATE INDEX IF NOT EXISTS idx_inv_assignee ON investigations(assignee) WHERE assignee IS NOT NULL;

-- 3. Original Input (Immutable capture)
CREATE TABLE IF NOT EXISTS original_inputs (
    id TEXT PRIMARY KEY,
    investigation_key TEXT NOT NULL,
    tester_description TEXT NOT NULL,
    reporter TEXT NOT NULL,
    captured_at TEXT NOT NULL,
    initial_evidence_ids_json TEXT NOT NULL,
    provenance TEXT NOT NULL DEFAULT 'HUMAN_SUPPLIED',
    
    FOREIGN KEY (investigation_key) REFERENCES investigations(record_key) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_original_inputs_inv ON original_inputs(investigation_key);

-- 4. Evidence (Metadata only; no binary bytes stored)
CREATE TABLE IF NOT EXISTS evidence (
    id TEXT PRIMARY KEY,
    investigation_key TEXT NOT NULL,
    stage TEXT NOT NULL,
    evidence_type TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    canonical_filename TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    byte_size INTEGER NOT NULL,
    uploaded_by TEXT NOT NULL,
    captured_at TEXT NOT NULL,
    notes TEXT NULL,
    provenance TEXT NOT NULL,
    
    FOREIGN KEY (investigation_key) REFERENCES investigations(record_key) ON DELETE RESTRICT,
    CONSTRAINT chk_evidence_stage CHECK (stage IN ('ORIGINAL', 'DEVELOPER_FIX', 'RETEST', 'SUPPLEMENTAL')),
    CONSTRAINT chk_evidence_type CHECK (evidence_type IN ('SCREENSHOT', 'IMAGE', 'LOG', 'RAW_TEXT', 'HAR', 'VIDEO', 'OTHER'))
);

CREATE INDEX IF NOT EXISTS idx_evidence_inv ON evidence(investigation_key);
CREATE INDEX IF NOT EXISTS idx_evidence_sha256 ON evidence(sha256);

-- 5. AI Artifacts (Append-only AI generation runs)
CREATE TABLE IF NOT EXISTS ai_artifacts (
    generation_id TEXT PRIMARY KEY,
    investigation_key TEXT NOT NULL,
    purpose TEXT NOT NULL,
    model_identifier TEXT NOT NULL,
    input_evidence_ids_json TEXT NOT NULL,
    structured_output_json TEXT NOT NULL,
    optional_usage_metadata_json TEXT NULL,
    generated_at TEXT NOT NULL,
    provenance TEXT NOT NULL DEFAULT 'AI_INFERENCE',
    
    FOREIGN KEY (investigation_key) REFERENCES investigations(record_key) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_ai_artifacts_inv ON ai_artifacts(investigation_key, generated_at DESC);

-- 6. Research Artifacts (Append-only research runs)
CREATE TABLE IF NOT EXISTS research_artifacts (
    id TEXT PRIMARY KEY,
    investigation_key TEXT NOT NULL,
    research_question TEXT NOT NULL,
    trigger_reason TEXT NOT NULL,
    sources_json TEXT NOT NULL,
    observations_json TEXT NOT NULL,
    relevance_to_art TEXT NOT NULL,
    possible_art_approach TEXT NOT NULL,
    generated_at TEXT NOT NULL,
    provenance TEXT NOT NULL DEFAULT 'AI_RECOMMENDATION',
    
    FOREIGN KEY (investigation_key) REFERENCES investigations(record_key) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_research_artifacts_inv ON research_artifacts(investigation_key, generated_at DESC);

-- 7. Ticket Revisions (Append-only ticket specifications)
CREATE TABLE IF NOT EXISTS ticket_revisions (
    ticket_id TEXT PRIMARY KEY,
    investigation_key TEXT NOT NULL,
    revision INTEGER NOT NULL,
    title TEXT NOT NULL,
    repro_steps TEXT NOT NULL,
    expected_result TEXT NOT NULL,
    actual_result TEXT NOT NULL,
    business_impact TEXT NOT NULL,
    recommended_solution TEXT NOT NULL,
    module TEXT NOT NULL,
    environment TEXT NOT NULL,
    severity TEXT NOT NULL,
    priority TEXT NOT NULL,
    tags_json TEXT NOT NULL,
    discussion_json TEXT NOT NULL,
    provenance TEXT NOT NULL DEFAULT 'HUMAN_APPROVED',
    updated_at TEXT NOT NULL,
    
    FOREIGN KEY (investigation_key) REFERENCES investigations(record_key) ON DELETE RESTRICT,
    CONSTRAINT uq_ticket_revisions_key_rev UNIQUE (investigation_key, revision),
    CONSTRAINT chk_ticket_severity CHECK (severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'Not provided')),
    CONSTRAINT chk_ticket_priority CHECK (priority IN ('P0', 'P1', 'P2', 'P3', 'Not provided'))
);

CREATE INDEX IF NOT EXISTS idx_ticket_revisions_inv ON ticket_revisions(investigation_key, revision DESC);

-- 8. Developer Updates (Append-only fix submissions)
CREATE TABLE IF NOT EXISTS developer_updates (
    id TEXT PRIMARY KEY,
    investigation_key TEXT NOT NULL,
    developer_username TEXT NOT NULL,
    summary_of_changes TEXT NOT NULL,
    commit_hash_or_pr TEXT NULL,
    resolved_in_version_or_branch TEXT NOT NULL,
    test_instructions_for_qa TEXT NOT NULL,
    submitted_at TEXT NOT NULL,
    provenance TEXT NOT NULL DEFAULT 'DEVELOPER_UPDATE',
    
    FOREIGN KEY (investigation_key) REFERENCES investigations(record_key) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_developer_updates_inv ON developer_updates(investigation_key, submitted_at DESC);

-- 9. Retest Artifacts (Append-only verification attempts)
CREATE TABLE IF NOT EXISTS retest_artifacts (
    id TEXT PRIMARY KEY,
    investigation_key TEXT NOT NULL,
    retest_evidence_ids_json TEXT NOT NULL,
    ai_recommendation_json TEXT NULL,
    human_confirmation_json TEXT NOT NULL,
    executed_at TEXT NOT NULL,
    provenance TEXT NOT NULL DEFAULT 'RETEST_VERIFICATION',
    
    FOREIGN KEY (investigation_key) REFERENCES investigations(record_key) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_retest_artifacts_inv ON retest_artifacts(investigation_key, executed_at DESC);

-- 10. Audit Events (Append-only lifecycle event log)
CREATE TABLE IF NOT EXISTS audit_events (
    id TEXT PRIMARY KEY,
    investigation_key TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    actor TEXT NOT NULL,
    event_type TEXT NOT NULL,
    summary TEXT NOT NULL,
    details_json TEXT NULL,
    
    FOREIGN KEY (investigation_key) REFERENCES investigations(record_key) ON DELETE RESTRICT,
    CONSTRAINT chk_audit_event_type CHECK (event_type IN (
        'INVESTIGATION_CAPTURED',
        'EVIDENCE_ADDED',
        'AI_ANALYSIS_COMPLETED',
        'RESEARCH_COMPLETED',
        'TICKET_REVISED',
        'TICKET_CONFIRMED',
        'ASSIGNED',
        'STATUS_TRANSITIONED',
        'FIX_SUBMITTED',
        'RETEST_EXECUTED',
        'VERIFIED',
        'LEGACY_SYNCED'
    ))
);

CREATE INDEX IF NOT EXISTS idx_audit_events_inv_ts ON audit_events(investigation_key, timestamp ASC);
"""


def init_db(connection):
    """
    Executes schema creation on the supplied SQLite connection.
    Enforces foreign keys.
    """
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.executescript(DDL_STATEMENTS)
    connection.commit()
