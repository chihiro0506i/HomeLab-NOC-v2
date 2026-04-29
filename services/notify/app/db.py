"""SQLite database management for Notify Hub."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

import aiosqlite

logger = logging.getLogger("notify.db")

DB_PATH: str = os.getenv("NOTIFY_DB_PATH", "/app/data/notify.db")

# ---------------------------------------------------------------------------
# Schema – all CREATE statements are idempotent (IF NOT EXISTS)
# ---------------------------------------------------------------------------

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS events (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    source              TEXT    NOT NULL,
    event_type          TEXT    NOT NULL,
    severity            TEXT    NOT NULL,
    title               TEXT    NOT NULL,
    message             TEXT,
    dedup_key           TEXT,
    metadata_json       TEXT,
    created_at          TEXT    NOT NULL,
    notified_at         TEXT,
    notification_status TEXT
);

CREATE TABLE IF NOT EXISTS notifications (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id    INTEGER NOT NULL,
    channel     TEXT    NOT NULL,
    status      TEXT    NOT NULL,
    response    TEXT,
    sent_at     TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS slurm_jobs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id          TEXT    NOT NULL UNIQUE,
    job_name        TEXT,
    state           TEXT,
    previous_state  TEXT,
    partition       TEXT,
    node            TEXT,
    submit_time     TEXT,
    start_time      TEXT,
    end_time        TEXT,
    elapsed         TEXT,
    exit_code       TEXT,
    reason          TEXT,
    stdout_path     TEXT,
    stderr_path     TEXT,
    last_log_tail   TEXT,
    last_seen       TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""


async def init_db() -> None:
    """Create tables if they don't exist yet."""
    logger.info("Initialising database at %s", DB_PATH)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(_SCHEMA_SQL)
        await db.commit()
    logger.info("Database ready")


@asynccontextmanager
async def get_db() -> AsyncIterator[aiosqlite.Connection]:
    """Yield an *aiosqlite* connection with ``row_factory`` set to
    ``aiosqlite.Row`` so that columns are accessible by name."""
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()


async def insert_event(
    db: aiosqlite.Connection,
    *,
    source: str,
    event_type: str,
    severity: str,
    title: str,
    message: str | None,
    dedup_key: str | None,
    metadata_json: str | None,
    created_at: str,
) -> int:
    """Insert a new event row and return the generated ``id``."""
    cursor = await db.execute(
        """
        INSERT INTO events
            (source, event_type, severity, title, message,
             dedup_key, metadata_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (source, event_type, severity, title, message,
         dedup_key, metadata_json, created_at),
    )
    await db.commit()
    assert cursor.lastrowid is not None
    return cursor.lastrowid


async def fetch_events(
    db: aiosqlite.Connection,
    *,
    limit: int = 100,
    source: str | None = None,
    severity: str | None = None,
) -> list[dict[str, Any]]:
    """Return events ordered by newest first, with optional filters."""
    clauses: list[str] = []
    params: list[Any] = []
    if source:
        clauses.append("source = ?")
        params.append(source)
    if severity:
        clauses.append("severity = ?")
        params.append(severity)

    where = ""
    if clauses:
        where = "WHERE " + " AND ".join(clauses)

    query = f"SELECT * FROM events {where} ORDER BY id DESC LIMIT ?"
    params.append(limit)

    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def fetch_slurm_jobs(
    db: aiosqlite.Connection,
    *,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Return Slurm jobs ordered by newest ``last_seen`` first."""
    cursor = await db.execute(
        "SELECT * FROM slurm_jobs ORDER BY last_seen DESC LIMIT ?",
        (limit,),
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def count_events(
    db: aiosqlite.Connection,
    *,
    severity: str | None = None,
    since: str | None = None,
) -> int:
    """Count events, optionally filtered by severity and/or time."""
    clauses: list[str] = []
    params: list[Any] = []
    if severity:
        clauses.append("severity = ?")
        params.append(severity)
    if since:
        clauses.append("created_at >= ?")
        params.append(since)

    where = ""
    if clauses:
        where = "WHERE " + " AND ".join(clauses)

    cursor = await db.execute(
        f"SELECT COUNT(*) FROM events {where}", params,
    )
    row = await cursor.fetchone()
    return row[0] if row else 0
