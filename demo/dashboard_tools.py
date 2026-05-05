"""HTTP helper for calling DentalOS agent-tools API.

Posts to /api/dalia/agent-tools/{name} with shared-secret auth.
Retries once on 5xx. Never retries 4xx.
Returns error dict (never raises) so the LLM can handle failures gracefully.

Part of openspec change `dalia-call-backend` Phase 10.
"""

import logging
import os

import httpx

logger = logging.getLogger("dalia.tools")

DASHBOARD_URL = os.getenv("DASHBOARD_WEBHOOK_URL", "").rstrip("/")
DASHBOARD_SECRET = os.getenv("DASHBOARD_WEBHOOK_SECRET", "")


async def call_dalia_tool(name: str, payload: dict) -> dict:
    """POST to /api/dalia/agent-tools/{name} with auth + 3s timeout.

    Retries once on 5xx (transient). Never retries 4xx.
    Never raises — returns an error dict so the LLM can act on it.
    """
    if not DASHBOARD_URL or not DASHBOARD_SECRET:
        logger.error(f"[{name}] DASHBOARD_WEBHOOK_URL/SECRET not configured")
        return {"error": "backend_not_configured", "message": "Dashboard URL or secret missing"}

    url = f"{DASHBOARD_URL}/api/dalia/agent-tools/{name.replace('_', '-')}"
    headers = {
        "X-Dalia-Secret": DASHBOARD_SECRET,
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=5.0) as client:
        for attempt in (1, 2):
            try:
                r = await client.post(url, headers=headers, json=payload)
            except httpx.HTTPError as e:
                logger.warning(f"[{name}] http error attempt {attempt}: {e}")
                if attempt == 2:
                    return {"error": "connection_failed", "message": str(e)}
                continue

            if r.status_code < 500:
                # 2xx, 4xx → try to parse JSON, fallback to error dict
                try:
                    return r.json()
                except Exception:
                    logger.warning(f"[{name}] non-JSON response ({r.status_code}): {r.text[:200]}")
                    return {
                        "error": "invalid_response",
                        "status_code": r.status_code,
                        "message": f"Backend returned non-JSON ({r.status_code})",
                    }

            logger.warning(f"[{name}] {r.status_code} attempt {attempt}")
            if attempt == 2:
                return {
                    "error": "server_error",
                    "status_code": r.status_code,
                    "message": f"Backend returned {r.status_code} after 2 attempts",
                }
    return {"error": "unknown", "message": "No response received"}
