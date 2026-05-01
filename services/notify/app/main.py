"""Notify Hub – FastAPI application entry point.

A lightweight event-aggregation and notification service for HomeLab-NOC-v2.
"""

from __future__ import annotations

import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, AsyncIterator

from fastapi import Depends, FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .db import (
    count_notifications,
    count_events,
    fetch_event_by_id,
    fetch_events,
    fetch_notifications,
    get_db,
    has_recent_sent_notification,
    init_db,
    insert_event,
    insert_notification,
    update_event_notification_status,
)
from .notifier import (
    configured_channel,
    dedup_since_iso,
    notification_enabled,
    send_notification,
    should_notify,
)
from .schemas import EventCreate, EventResponse, HealthResponse
from .security import verify_token

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("notify")

# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Startup / shutdown tasks."""
    logger.info("Notify Hub starting …")
    await init_db()
    yield
    logger.info("Notify Hub shutting down …")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Notify Hub",
    description="Event aggregation and notification service for HomeLab-NOC-v2.",
    version="0.1.0",
    lifespan=lifespan,
)

# Static files & templates -------------------------------------------------

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(_BASE_DIR, "static")),
    name="static",
)

templates = Jinja2Templates(directory=os.path.join(_BASE_DIR, "templates"))


# ===================================================================== #
#  Utility helpers                                                       #
# ===================================================================== #

def _now_iso() -> str:
    """Return current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _generate_dedup_key(source: str, event_type: str, title: str) -> str:
    """Build a default dedup_key from event fields."""
    return f"{source}:{event_type}:{title}"


# ===================================================================== #
#  API routes                                                            #
# ===================================================================== #

# --- Health ---------------------------------------------------------------

@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    """Health-check endpoint for Uptime Kuma monitoring."""
    return HealthResponse()


# --- Events (JSON API) ---------------------------------------------------

@app.post(
    "/api/events",
    response_model=EventResponse,
    status_code=201,
    tags=["events"],
)
async def create_event(
    body: EventCreate,
    _token: str = Depends(verify_token),
) -> EventResponse:
    """Receive and store a new event."""

    dedup_key = body.dedup_key or _generate_dedup_key(
        body.source, body.event_type, body.title,
    )
    metadata_json: str | None = (
        json.dumps(body.metadata, ensure_ascii=False) if body.metadata else None
    )

    notified = False
    async with get_db() as db:
        event_id = await insert_event(
            db,
            source=body.source,
            event_type=body.event_type,
            severity=body.severity,
            title=body.title,
            message=body.message,
            dedup_key=dedup_key,
            metadata_json=metadata_json,
            created_at=_now_iso(),
        )
        event = await fetch_event_by_id(db, event_id)
        if event is None:
            logger.error("Event disappeared before notification processing id=%d", event_id)
            return EventResponse(event_id=event_id, notified=False)

        notification_status = "not_applicable"
        notified_at: str | None = None
        if should_notify(body.severity):
            channel = configured_channel()
            if not notification_enabled():
                sent_at = _now_iso()
                notification_status = "disabled"
                await insert_notification(
                    db,
                    event_id=event_id,
                    channel="none",
                    status=notification_status,
                    response="Outbound notifications are disabled",
                    sent_at=sent_at,
                )
            elif channel == "none":
                sent_at = _now_iso()
                notification_status = "unconfigured"
                await insert_notification(
                    db,
                    event_id=event_id,
                    channel="none",
                    status=notification_status,
                    response="NOTIFY_NTFY_URL is not configured",
                    sent_at=sent_at,
                )
            else:
                since = dedup_since_iso()
                if (
                    dedup_key
                    and since
                    and await has_recent_sent_notification(
                        db,
                        dedup_key=dedup_key,
                        channel=channel,
                        since=since,
                    )
                ):
                    sent_at = _now_iso()
                    notification_status = "deduplicated"
                    await insert_notification(
                        db,
                        event_id=event_id,
                        channel=channel,
                        status=notification_status,
                        response=f"Matching sent notification exists since {since}",
                        sent_at=sent_at,
                    )
                    logger.info(
                        "Notification deduplicated id=%d channel=%s dedup_key=%s",
                        event_id, channel, dedup_key,
                    )
                else:
                    decision = await send_notification(event)
                    sent_at = _now_iso()
                    notification_status = decision.status
                    notified = decision.notified
                    if notified:
                        notified_at = sent_at
                    await insert_notification(
                        db,
                        event_id=event_id,
                        channel=decision.channel,
                        status=decision.status,
                        response=decision.response,
                        sent_at=sent_at,
                    )
        await update_event_notification_status(
            db,
            event_id=event_id,
            notified_at=notified_at,
            notification_status=notification_status,
        )

    logger.info(
        "Event stored id=%d source=%s type=%s severity=%s notified=%s status=%s title=%s",
        event_id,
        body.source,
        body.event_type,
        body.severity,
        notified,
        notification_status,
        body.title,
    )
    return EventResponse(event_id=event_id, notified=notified)


@app.get("/api/events", tags=["events"])
async def list_events(
    limit: int = Query(100, ge=1, le=1000),
    source: str | None = Query(None),
    severity: str | None = Query(None),
) -> list[dict[str, Any]]:
    """Return stored events as JSON (newest first)."""
    async with get_db() as db:
        return await fetch_events(db, limit=limit, source=source, severity=severity)


@app.get("/api/notifications", tags=["notifications"])
async def list_notifications(
    limit: int = Query(100, ge=1, le=1000),
    status: str | None = Query(None),
    channel: str | None = Query(None),
) -> list[dict[str, Any]]:
    """Return outbound notification attempts as JSON (newest first)."""
    async with get_db() as db:
        return await fetch_notifications(
            db, limit=limit, status=status, channel=channel,
        )


@app.post(
    "/api/test-notification",
    response_model=EventResponse,
    status_code=201,
    tags=["events"],
)
async def test_notification(
    _token: str = Depends(verify_token),
) -> EventResponse:
    """Create a test event for verification purposes."""
    async with get_db() as db:
        event_id = await insert_event(
            db,
            source="system",
            event_type="test",
            severity="info",
            title="Test notification",
            message="This is a test event created via /api/test-notification.",
            dedup_key=f"system:test:{_now_iso()}",
            metadata_json=None,
            created_at=_now_iso(),
        )

    logger.info("Test event stored  id=%d", event_id)
    return EventResponse(event_id=event_id)


# ===================================================================== #
#  Web pages (HTML)                                                      #
# ===================================================================== #

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def page_index(request: Request) -> HTMLResponse:
    """Dashboard page."""
    async with get_db() as db:
        total_events = await count_events(db)
        critical_count = await count_events(db, severity="critical")
        error_count = await count_events(db, severity="error")
        sent_count = await count_notifications(db, status="sent")
        recent_events = await fetch_events(db, limit=5)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "total_events": total_events,
            "critical_count": critical_count,
            "error_count": error_count,
            "sent_count": sent_count,
            "recent_events": recent_events,
        },
    )


@app.get("/events", response_class=HTMLResponse, include_in_schema=False)
async def page_events(
    request: Request,
    limit: int = Query(100, ge=1, le=1000),
    source: str | None = Query(None),
    severity: str | None = Query(None),
) -> HTMLResponse:
    """Event history page."""
    async with get_db() as db:
        events = await fetch_events(
            db, limit=limit, source=source, severity=severity,
        )

    return templates.TemplateResponse(
        request=request,
        name="events.html",
        context={
            "events": events,
            "filter_source": source or "",
            "filter_severity": severity or "",
        },
    )


@app.get("/notifications", response_class=HTMLResponse, include_in_schema=False)
async def page_notifications(
    request: Request,
    limit: int = Query(100, ge=1, le=1000),
    status: str | None = Query(None),
    channel: str | None = Query(None),
) -> HTMLResponse:
    """Notification attempt history page."""
    async with get_db() as db:
        notifications = await fetch_notifications(
            db, limit=limit, status=status, channel=channel,
        )

    return templates.TemplateResponse(
        request=request,
        name="notifications.html",
        context={
            "notifications": notifications,
            "filter_status": status or "",
            "filter_channel": channel or "",
        },
    )
