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
    count_events,
    fetch_events,
    fetch_slurm_jobs,
    get_db,
    init_db,
    insert_event,
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
# Configuration (read from environment)
# ---------------------------------------------------------------------------

SLURM_ENABLED: bool = os.getenv("SLURM_ENABLED", "false").lower() == "true"

# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Startup / shutdown tasks."""
    logger.info("Notify Hub starting …")
    await init_db()
    logger.info("SLURM_ENABLED=%s", SLURM_ENABLED)
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

    logger.info(
        "Event stored  id=%d source=%s type=%s severity=%s title=%s",
        event_id, body.source, body.event_type, body.severity, body.title,
    )
    return EventResponse(event_id=event_id)


@app.get("/api/events", tags=["events"])
async def list_events(
    limit: int = Query(100, ge=1, le=1000),
    source: str | None = Query(None),
    severity: str | None = Query(None),
) -> list[dict[str, Any]]:
    """Return stored events as JSON (newest first)."""
    async with get_db() as db:
        return await fetch_events(db, limit=limit, source=source, severity=severity)


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


# --- Slurm jobs (JSON API) -----------------------------------------------

@app.get("/api/slurm/jobs", tags=["slurm"])
async def list_slurm_jobs(
    limit: int = Query(100, ge=1, le=1000),
) -> list[dict[str, Any]]:
    """Return Slurm job records.  Returns ``[]`` when monitoring is disabled."""
    if not SLURM_ENABLED:
        return []
    async with get_db() as db:
        return await fetch_slurm_jobs(db, limit=limit)


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
        recent_events = await fetch_events(db, limit=5)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "total_events": total_events,
            "critical_count": critical_count,
            "error_count": error_count,
            "recent_events": recent_events,
            "slurm_enabled": SLURM_ENABLED,
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
        "events.html",
        {
            "request": request,
            "events": events,
            "filter_source": source or "",
            "filter_severity": severity or "",
        },
    )


@app.get("/jobs", response_class=HTMLResponse, include_in_schema=False)
async def page_jobs(request: Request) -> HTMLResponse:
    """Slurm jobs page."""
    jobs: list[dict[str, Any]] = []
    if SLURM_ENABLED:
        async with get_db() as db:
            jobs = await fetch_slurm_jobs(db, limit=200)

    return templates.TemplateResponse(
        "jobs.html",
        {
            "request": request,
            "jobs": jobs,
            "slurm_enabled": SLURM_ENABLED,
        },
    )
