"""HTTP helper for calling DentalOS agent-tools API.

Posts to /api/dalia/agent-tools/{name} with shared-secret auth.
Retries once on 5xx. Never retries 4xx.

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

    Retries once on 5xx (transient). Never retries 4xx — those mean our
    request is malformed (validation error, wrong cabinet, etc.).
    """
    if not DASHBOARD_URL or not DASHBOARD_SECRET:
        raise RuntimeError("DASHBOARD_WEBHOOK_URL/SECRET not configured")

    url = f"{DASHBOARD_URL}/api/dalia/agent-tools/{name.replace('_', '-')}"
    headers = {
        "X-Dalia-Secret": DASHBOARD_SECRET,
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=3.0) as client:
        for attempt in (1, 2):
            try:
                r = await client.post(url, headers=headers, json=payload)
            except httpx.HTTPError as e:
                logger.warning(f"[{name}] http error attempt {attempt}: {e}")
                if attempt == 2:
                    raise
                continue
            if r.status_code < 500:
                # 2xx, 4xx → return body for the LLM to act on
                return r.json()
            logger.warning(f"[{name}] {r.status_code} attempt {attempt}")
            if attempt == 2:
                r.raise_for_status()
        return {}
