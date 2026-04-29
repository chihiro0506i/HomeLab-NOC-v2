"""Pydantic schemas for request / response validation."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

# Allowed severity levels – used as CSS class names (badge-<severity>),
# so they must be a fixed set of safe identifiers.
Severity = Literal["info", "warning", "error", "critical"]


# ---------------------------------------------------------------------------
# Event
# ---------------------------------------------------------------------------

class EventCreate(BaseModel):
    """Body accepted by ``POST /api/events``."""

    source: str = Field(
        ...,
        min_length=1,
        max_length=64,
        examples=["uptime-kuma", "backup", "manual", "system"],
    )
    event_type: str = Field(
        ...,
        min_length=1,
        max_length=64,
        examples=["monitor_down", "monitor_up", "test"],
    )
    severity: Severity = Field(
        ...,
        examples=["info", "warning", "error", "critical"],
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=256,
        examples=["Pi-hole DNS is down"],
    )
    message: str | None = Field(
        None,
        max_length=4096,
        examples=["Uptime Kuma detected Pi-hole DNS failure."],
    )
    dedup_key: str | None = Field(
        None,
        max_length=256,
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
