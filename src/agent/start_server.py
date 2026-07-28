# start_server.py — ホスティング層（受付・起動、S2S 観測トークンのバックグラウンド取得）
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

from aiohttp import web
from microsoft_agents.activity.config import load_configuration_from_env
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft.opentelemetry.a365.hosting import (
    ObservabilityHostingManager,
    ObservabilityHostingOptions,
)

from observability.token_service import acquire_initial_token, run_token_service

logger = logging.getLogger(__name__)

_A365_TENANT_ID = os.environ.get("AGENT365OBSERVABILITY__TENANTID", "")
_A365_AGENT_ID = os.environ.get("AGENT365OBSERVABILITY__AGENTID", "")
_A365_CLIENT_ID = os.environ.get("AGENT365OBSERVABILITY__CLIENTID", "")
_A365_CLIENT_SECRET = os.environ.get("AGENT365OBSERVABILITY__CLIENTSECRET", "")
_A365_ENABLED = bool(_A365_TENANT_ID and _A365_AGENT_ID and _A365_CLIENT_ID and _A365_CLIENT_SECRET)


def load_agent_configuration() -> dict:
    """.env の CONNECTIONS__* / AGENTAPPLICATION__* / CONNECTIONSMAP__* をパースする。"""
    return load_configuration_from_env(dict(os.environ))


def build_adapter(config: dict) -> tuple[CloudAdapter, MsalConnectionManager]:
    """CloudAdapter と ConnectionManager を構築する（Teams チャネル認証用。Observability の
    S2S トークン取得とは独立している）。"""
    connection_manager = MsalConnectionManager(**config)
    adapter = CloudAdapter(connection_manager=connection_manager)

    ObservabilityHostingManager.configure(
        adapter.middleware_set,
        ObservabilityHostingOptions(enable_baggage=True, enable_output_logging=True),
    )
    return adapter, connection_manager


async def _handle_messages(request: web.Request, agent_app) -> web.Response:
    try:
        body = await request.json()
    except Exception:
        body = {}
    text = (body.get("text") or "")[:60]
    logger.info(
        "[/api/messages] type=%s from=%s text=%s",
        body.get("type"), (body.get("from") or {}).get("name"), text,
    )
    try:
        return await agent_app.adapter.process(request, agent_app)
    except Exception:
        logger.exception("[/api/messages] adapter.process failed")
        return web.Response(
            status=500, text='{"error":"Internal server error"}',
            content_type="application/json",
        )


async def _handle_health(_request: web.Request) -> web.Response:
    import json
    body = json.dumps({"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()})
    return web.Response(text=body, content_type="application/json")


async def _handle_privacy(_request: web.Request) -> web.Response:
    return web.Response(
        text="<html><body><h1>Privacy Statement</h1><p>This is a training/demo agent. "
        "No personal data is retained beyond the current conversation turn.</p></body></html>",
        content_type="text/html",
    )


async def _handle_terms(_request: web.Request) -> web.Response:
    return web.Response(
        text="<html><body><h1>Terms of Use</h1><p>This is a training/demo agent provided "
        "as-is for Agent 365 hands-on purposes only.</p></body></html>",
        content_type="text/html",
    )


async def _start_observability_token_service(app: web.Application) -> None:
    if not _A365_ENABLED:
        logger.warning("Agent365 observability credentials not configured — skipping token service.")
        return
    try:
        await acquire_initial_token(
            tenant_id=_A365_TENANT_ID,
            agent_id=_A365_AGENT_ID,
            blueprint_client_id=_A365_CLIENT_ID,
            blueprint_client_secret=_A365_CLIENT_SECRET,
        )
    except Exception:
        logger.warning("Initial observability token acquisition failed; will retry in background.", exc_info=True)

    app["observability_token_task"] = asyncio.create_task(
        run_token_service(
            tenant_id=_A365_TENANT_ID,
            agent_id=_A365_AGENT_ID,
            blueprint_client_id=_A365_CLIENT_ID,
            blueprint_client_secret=_A365_CLIENT_SECRET,
        )
    )


async def _stop_observability_token_service(app: web.Application) -> None:
    task = app.get("observability_token_task")
    if task:
        task.cancel()


async def run_server(agent_app) -> None:
    """aiohttp サーバーを起動する（/api/messages, /api/health, /privacy, /terms）。"""
    app = web.Application()
    app.router.add_post("/api/messages", lambda req: _handle_messages(req, agent_app))
    app.router.add_get("/api/health", _handle_health)
    app.router.add_get("/privacy", _handle_privacy)
    app.router.add_get("/terms", _handle_terms)
    app.on_startup.append(_start_observability_token_service)
    app.on_cleanup.append(_stop_observability_token_service)

    port = int(os.getenv("PORT", "3978"))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info("Agent server running on port %d", port)
    await asyncio.Event().wait()  # 起動し続ける


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from app import AGENT_APP

    asyncio.run(run_server(AGENT_APP))
