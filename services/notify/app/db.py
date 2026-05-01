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

-- Outbound notification attempt history.
CREATE TABLE IF NOT EXISTS notifications (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id    INTEGER NOT NULL,
    channel     TEXT    NOT NULL,
    status      TEXT    NOT NULL,
    response    TEXT,
    sent_at     TEXT    NOT NULL,
    FOREIGN KEY(event_id) REFERENCES events(id)
);

-- Reserved: key-value store for runtime settings (e.g. last poll time).
-- Currently not read or written by the application.
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT
);

CREATE INDEX IF NOT EXISTS idx_events_dedup_key
    ON events(dedup_key);

CREATE INDEX IF NOT EXISTS idx_notifications_event_status
    ON notifications(event_id, status, sent_at);
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


async def fetch_event_by_id(
    db: aiosqlite.Connection,
    event_id: int,
) -> dict[str, Any] | None:
    """Return a single event by id."""
    cursor = await db.execute("SELECT * FROM events WHERE id = ?", (event_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def update_event_notification_status(
    db: aiosqlite.Connection,
    *,
    event_id: int,
    notified_at: str | None,
    notification_status: str,
) -> None:
    """Store the latest notification state on an event row."""
    await db.execute(
        """
        UPDATE events
           SET notified_at = ?,
               notification_status = ?
         WHERE id = ?
        """,
        (notified_at, notification_status, event_id),
    )
    await db.commit()


async def insert_notification(
    db: aiosqlite.Connection,
    *,
    event_id: int,
    channel: str,
    status: str,
    response: str | None,
    sent_at: str,
) -> int:
    """Insert one notification attempt row and return its id."""
    cursor = await db.execute(
        """
        INSERT INTO notifications
            (event_id, channel, status, response, sent_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (event_id, channel, status, response, sent_at),
    )
    await db.commit()
    assert cursor.lastrowid is not None
    return cursor.lastrowid


async def has_recent_sent_notification(
    db: aiosqlite.Connection,
    *,
    dedup_key: str,
    channel: str,
    since: str,
) -> bool:
    """Return whether a matching notification was sent since a timestamp."""
    cursor = await db.execute(
        """
        SELECT 1
          FROM notifications AS n
          JOIN events AS e ON e.id = n.event_id
         WHERE e.dedup_key = ?
           AND n.channel = ?
           AND n.status = 'sent'
           AND n.sent_at >= ?
         LIMIT 1
        """,
        (dedup_key, channel, since),
    )
    row = await cursor.fetchone()
    return row is not None


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


async def fetch_notifications(
    db: aiosqlite.Connection,
    *,
    limit: int = 100,
    status: str | None = None,
    channel: str | None = None,
) -> list[dict[str, Any]]:
    """Return notification attempts with their source event context."""
    clauses: list[str] = []
    params: list[Any] = []
    if status:
        clauses.append("n.status = ?")
        params.append(status)
    if channel:
        clauses.append("n.channel = ?")
        params.append(channel)

    where = ""
    if clauses:
        where = "WHERE " + " AND ".join(clauses)

    query = f"""
        SELECT
            n.id,
            n.event_id,
            n.channel,
            n.status,
            n.response,
            n.sent_at,
            e.source,
            e.event_type,
            e.severity,
            e.title,
            e.dedup_key
          FROM notifications AS n
          JOIN events AS e ON e.id = n.event_id
          {where}
         ORDER BY n.id DESC
         LIMIT ?
    """
    params.append(limit)

    cursor = await db.execute(query, params)
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


async def count_notifications(
    db: aiosqlite.Connection,
    *,
    status: str | None = None,
) -> int:
    """Count notification attempts, optionally filtered by status."""
    if status:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM notifications WHERE status = ?",
            (status,),
        )
    else:
        cursor = await db.execute("SELECT COUNT(*) FROM notifications")
    row = await cursor.fetchone()
    return row[0] if row else 0
