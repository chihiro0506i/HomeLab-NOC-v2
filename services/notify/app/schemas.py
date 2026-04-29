"""Pydantic schemas for request / response validation."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Event
# ---------------------------------------------------------------------------

class EventCreate(BaseModel):
    """Body accepted by ``POST /api/events``."""

    source: str = Field(
        ...,
        examples=["uptime-kuma", "backup", "manual", "system"],
    )
    event_type: str = Field(
        ...,
        examples=["monitor_down", "monitor_up", "test"],
    )
    severity: str = Field(
        ...,
        examples=["info", "warning", "error", "critical"],
    )
    title: str = Field(..., examples=["Pi-hole DNS is down"])
    message: str | None = Field(
        None,
        examples=["Uptime Kuma detected Pi-hole DNS failure."],
    )
    dedup_key: str | None = Field(
        None,
        examples=["uptime:pihole_dns:down"],
    )
    metadata: dict[str, Any] | None = Field(
        None,
        examples=[{"monitor_name": "Pi-hole DNS"}],
    )


class EventResponse(BaseModel):
    """Returned after storing an event."""

    status: str = "stored"
    event_id: int
    notified: bool = False



# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    """``GET /health`` response."""

    status: str = "ok"
    service: str = "homelab-notify"
