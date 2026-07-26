# start_server.py — ホスティング層（受付・起動）
#
# 非 AI Teammate エージェント用の最小 aiohttp ホスティング。
# app.py（頭脳）が `from start_server import build_adapter, load_agent_configuration` で使う。
#
# 実装済みパッケージ（microsoft-agents-hosting-core/aiohttp/authentication-msal 1.2.0）の
# ソースで実際に検証済み：
#   - CloudAdapter は `microsoft_agents.hosting.aiohttp`（トップレベル `microsoft_agents_hosting_aiohttp` ではない）
#   - MsalConnectionManager は `microsoft_agents.authentication.msal`（別 pip パッケージ
#     `microsoft-agents-authentication-msal`。requirements.txt に追記済み）
#   - MsalConnectionManager に `from_environment()` は無い。
#     `microsoft_agents.activity.config.load_configuration_from_env(os.environ)` で
#     CONNECTIONS__* 等をパースし、`MsalConnectionManager(**config)` に渡す
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

logger = logging.getLogger(__name__)


def load_agent_configuration() -> dict:
    """.env の CONNECTIONS__* / AGENTAPPLICATION__* / CONNECTIONSMAP__* を
    dict にパースする（`microsoft_agents.activity.config.load_configuration_from_env`）。
    戻り値は {"AGENTAPPLICATION": ..., "CONNECTIONS": ..., "CONNECTIONSMAP": ...}。
    """
    return load_configuration_from_env(dict(os.environ))


def build_adapter(config: dict) -> tuple[CloudAdapter, MsalConnectionManager]:
    """CloudAdapter と ConnectionManager を構築する。

    `config` は `load_agent_configuration()` の戻り値をそのまま渡す
    （`MsalConnectionManager(**config)` が config["CONNECTIONS"] / config["CONNECTIONSMAP"]
    を読み込む。client_id / client_secret / tenant_id を直接渡さない）。
    呼び出し側（app.py）は返る connection_manager を
    `AgentApplication(connection_manager=..., **config)` にも渡し、
    AGENTAPPLICATION.USERAUTHORIZATION（AGENTIC ハンドラ設定）を Authorization に伝播させること。
    """
    connection_manager = MsalConnectionManager(**config)
    adapter = CloudAdapter(connection_manager=connection_manager)

    # A365 Observability — best-effort instrumentation (verify against official sample)
    # TurnContext から baggage（tenant/agent 識別子）を自動的に配線する。
    # enable_baggage / enable_output_logging は既定 False のため明示的に True にする。
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


async def run_server(agent_app) -> None:
    """aiohttp サーバーを起動する（/api/messages, /api/health）。"""
    app = web.Application()
    app.router.add_post("/api/messages", lambda req: _handle_messages(req, agent_app))
    app.router.add_get("/api/health", _handle_health)

    port = int(os.getenv("PORT", "3978"))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info("Agent server running on port %d", port)
    await asyncio.Event().wait()  # 起動し続ける


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # app.py が `from start_server import build_adapter` するため、
    # 循環 import を避けて実行時にのみ import する。
    from app import AGENT_APP

    asyncio.run(run_server(AGENT_APP))
