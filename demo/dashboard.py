"""Dalia agent -> DentalOS dashboard integration.

Posts conversation turns and end-of-session reports to the DentalOS
backend via POST /api/livekit/agent-event.

Agent-side implementation of openspec change `dalia-call-backend` (Phase 6).
"""

import asyncio
import logging
import os
from datetime import datetime, timezone

import httpx
from livekit.agents.llm import ChatMessage

logger = logging.getLogger("dalia.dashboard")

DASHBOARD_URL = os.getenv("DASHBOARD_WEBHOOK_URL", "").rstrip("/")
DASHBOARD_SECRET = os.getenv("DASHBOARD_WEBHOOK_SECRET", "")
DASHBOARD_ENABLED = (
    os.getenv("DASHBOARD_INTEGRATION_ENABLED", "false").lower() == "true"
)

# Reuse a single httpx client across the session.
_http_client: httpx.AsyncClient | None = None


def _client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=httpx.Timeout(2.0, connect=1.0))
    return _http_client


async def _post(payload: dict, *, timeout: float) -> None:
    """POST best-effort to the dashboard. Never raises into the agent loop."""
    if not DASHBOARD_ENABLED:
        return
    if not DASHBOARD_URL or not DASHBOARD_SECRET:
        logger.warning("dashboard integration enabled but URL/secret missing")
        return
    try:
        await _client().post(
            f"{DASHBOARD_URL}/api/livekit/agent-event",
            json=payload,
            headers={"X-Dalia-Secret": DASHBOARD_SECRET},
            timeout=timeout,
        )
    except Exception as exc:
        # Best-effort: never block the conversation on dashboard failures.
        logger.warning("dashboard post failed: %s", exc)


def attach_dashboard_handlers(session, ctx) -> None:
    """Wire dashboard ingestion onto a LiveKit AgentSession.

    Call once after creating the session, right after
    ``session = AgentSession(...)``.
    """

    async def _handle_item(ev):
        item = getattr(ev, "item", None)
        if not isinstance(item, ChatMessage):
            return

        await _post(
            {
                "type": "message",
                "room_name": ctx.room.name,
                "role": item.role,
                "content": item.text_content or "",
                "interrupted": bool(getattr(item, "interrupted", False)),
                "metrics": getattr(item, "metrics", None),
                "started_at": datetime.now(timezone.utc).isoformat(),
            },
            timeout=2.0,
        )

    @session.on("conversation_item_added")
    def _on_item(ev):
        asyncio.create_task(_handle_item(ev))

    async def _shutdown():
        report_obj = (
            ctx.makeSessionReport() if hasattr(ctx, "makeSessionReport") else None
        )
        report_dict = report_obj.to_dict() if report_obj else {}

        await _post(
            {
                "type": "session_report",
                "room_name": ctx.room.name,
                "report": report_dict,
            },
            timeout=5.0,
        )
        # Drain the httpx client so we don't lose in-flight requests.
        if _http_client is not None:
            await _http_client.aclose()

    ctx.add_shutdown_callback(_shutdown)
