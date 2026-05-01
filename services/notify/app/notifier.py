"""Outbound notification support for Notify Hub."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

logger = logging.getLogger("notify.notifier")

_OUTBOUND_ENABLED_ENV = "NOTIFY_OUTBOUND_ENABLED"
_LEGACY_OUTBOUND_ENABLED_ENV = "NOTIFY_ENABLE_EXTERNAL_SEND"


@dataclass(frozen=True)
class NotificationDecision:
    """Result of an outbound notification attempt."""

    channel: str
    status: str
    response: str
    notified: bool = False


def _truthy(value: str | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _severity_set(value: str | None) -> set[str]:
    raw = value or "critical,error"
    return {item.strip().lower() for item in raw.split(",") if item.strip()}


def notification_enabled() -> bool:
    """Return whether outbound notifications should be attempted."""
    value = os.getenv(_OUTBOUND_ENABLED_ENV)
    legacy_value = os.getenv(_LEGACY_OUTBOUND_ENABLED_ENV)
    if value is not None and value.strip() != "":
        if legacy_value is not None:
            logger.warning(
                "%s is deprecated and ignored because %s is set.",
                _LEGACY_OUTBOUND_ENABLED_ENV,
                _OUTBOUND_ENABLED_ENV,
            )
        return _truthy(value, default=True)

    if legacy_value is not None and legacy_value.strip() != "":
        logger.warning(
            "%s is deprecated; use %s instead.",
            _LEGACY_OUTBOUND_ENABLED_ENV,
            _OUTBOUND_ENABLED_ENV,
        )
        return _truthy(legacy_value, default=True)

    return True


def configured_channel() -> str:
    """Return the configured notification channel name."""
    if os.getenv("NOTIFY_NTFY_URL"):
        return "ntfy"
    return "none"


def dedup_window_seconds() -> int:
    """Return notification deduplication window in seconds."""
    raw = os.getenv("NOTIFY_DEDUP_WINDOW_SECONDS", "900")
    try:
        value = int(raw)
    except ValueError:
        logger.warning("Invalid NOTIFY_DEDUP_WINDOW_SECONDS=%r; using 900", raw)
        return 900
    return max(0, value)


def parse_http_timeout_seconds() -> float:
    """Return a safe outbound HTTP timeout in seconds."""
    raw = os.getenv("NOTIFY_HTTP_TIMEOUT_SECONDS", "5")
    try:
        value = float(raw)
    except ValueError:
        logger.warning("Invalid NOTIFY_HTTP_TIMEOUT_SECONDS=%r; using 5.0", raw)
        return 5.0
    if value <= 0:
        logger.warning("Invalid NOTIFY_HTTP_TIMEOUT_SECONDS=%r; using 5.0", raw)
        return 5.0
    return value


def dedup_since_iso(now: datetime | None = None) -> str | None:
    """Return ISO timestamp used as the start of the dedup window."""
    seconds = dedup_window_seconds()
    if seconds <= 0:
        return None
    base = now or datetime.now(timezone.utc)
    return (base - timedelta(seconds=seconds)).isoformat()


def should_notify(severity: str) -> bool:
    """Return whether a severity is configured for outbound notification."""
    return severity.lower() in _severity_set(os.getenv("NOTIFY_SEVERITIES"))


def _priority_for_severity(severity: str) -> str:
    priorities = {
        "critical": "urgent",
        "error": "high",
        "warning": "default",
        "info": "low",
    }
    return priorities.get(severity.lower(), "default")


def _tags_for_event(event: dict[str, Any]) -> str:
    severity = str(event.get("severity") or "info").lower()
    source = str(event.get("source") or "unknown").lower()
    return f"homelab,{source},{severity}"


async def send_notification(event: dict[str, Any]) -> NotificationDecision:
    """Send one outbound notification if configured.

    The caller is responsible for severity filtering and deduplication.
    Failures are converted into a decision so event ingestion stays reliable.
    """
    if not notification_enabled():
        return NotificationDecision(
            channel="none",
            status="disabled",
            response="Outbound notifications are disabled",
        )

    url = os.getenv("NOTIFY_NTFY_URL", "").strip()
    if not url:
        return NotificationDecision(
            channel="none",
            status="unconfigured",
            response="NOTIFY_NTFY_URL is not configured",
        )

    title = str(event.get("title") or "HomeLab notification")
    message = str(event.get("message") or title)
    severity = str(event.get("severity") or "info")
    event_type = str(event.get("event_type") or "event")

    headers = {
        "Title": "HomeLab Alert",
        "Priority": _priority_for_severity(severity),
        "Tags": _tags_for_event(event),
        "X-Notify-Source": str(event.get("source") or "unknown"),
        "X-Notify-Event-Type": event_type,
    }

    token = os.getenv("NOTIFY_NTFY_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    body = (
        f"{title}\n\n"
        f"{message}\n\n"
        f"Severity: {severity}\n"
        f"Source: {event.get('source')}\n"
        f"Type: {event_type}\n"
        f"Dedup: {event.get('dedup_key') or '-'}"
    )

    timeout = parse_http_timeout_seconds()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, content=body.encode("utf-8"), headers=headers)
        if 200 <= response.status_code < 300:
            return NotificationDecision(
                channel="ntfy",
                status="sent",
                response=f"HTTP {response.status_code}",
                notified=True,
            )
        return NotificationDecision(
            channel="ntfy",
            status="failed",
            response=f"HTTP {response.status_code}: {response.text[:500]}",
        )
    except Exception as exc:  # noqa: BLE001 - notification failures must not break ingestion.
        logger.exception("Outbound notification failed")
        return NotificationDecision(
            channel="ntfy",
            status="failed",
            response=f"{type(exc).__name__}: {exc}",
        )
