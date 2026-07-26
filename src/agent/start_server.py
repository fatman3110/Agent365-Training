# start_server.py — ホスティング層（受付・起動）
#
# 非 AI Teammate エージェント用の最小 aiohttp ホスティング。
# app.py（頭脳）が `from start_server import build_adapter` で使う。
#
# ★ 参考実装の出典：agent365-skills の make-ai-teammate リファレンス
#   （plugins/agent365/skills/make-ai-teammate/references/python-ai-teammate.md の
#    host_agent_server.py、nodejs-ai-teammate.md の src/index.ts）から、AI Teammate
#    固有の要素（AgentNotification 通知配線・メール通知処理）を除いた最小形。
#   `AgentApplication` + `CloudAdapter.process(request, agent)` の正確なシグネチャは
#   `microsoft-agents-hosting-aiohttp` のバージョンにより変わり得るため、
#   着手時に Microsoft Learn / インストール済みパッケージのソースで確認すること。
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

from aiohttp import web
from microsoft_agents_hosting_aiohttp import CloudAdapter
from microsoft_agents.hosting.core.authorization import MsalConnectionManager

logger = logging.getLogger(__name__)


def build_adapter() -> CloudAdapter:
    """CloudAdapter を構築する。

    MsalConnectionManager が CONNECTIONS__* / AGENTAPPLICATION__* 環境変数
    （`a365 setup all` が .env に書き込む）から認証設定を読み込む。
    client_id / client_secret / tenant_id を直接渡さない。
    """
    connection_manager = MsalConnectionManager.from_environment()
    return CloudAdapter(connection_manager=connection_manager)


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
