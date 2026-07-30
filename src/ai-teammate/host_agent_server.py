# host_agent_server.py — aiohttp サーバー＋Agent 365 ルーティング（Agent365-Samples 準拠のリファレンス実装）
# ⚠️ プレビュー SDK。import 名/引数が変わり得るため、ビルドが通らない場合は
#    https://github.com/microsoft/Agent365-Samples/tree/main/python の該当ファイルに合わせる。
import asyncio
import logging
import os
from typing import Type

from dotenv import load_dotenv

load_dotenv()

from agent_interface import AgentInterface
from aiohttp import web
from microsoft_agents_hosting_aiohttp import CloudAdapter
from microsoft_agents_hosting_core import ActivityTypes
from microsoft_agents.hosting.core.authorization import MsalConnectionManager
from microsoft_agents.activity import ChannelId
from microsoft_agents_a365.notifications import AgentNotification

logger = logging.getLogger(__name__)
AUTH_HANDLER_NAME = os.getenv("AUTH_HANDLER_NAME", "")


class GenericAgentHost:
    def __init__(self, agent: AgentInterface):
        self._agent = agent
        self._adapter: CloudAdapter | None = None
        self._app: web.Application | None = None

    def _setup_handlers(self):
        @self._adapter.on_activity(ActivityTypes.message)
        async def on_message(context, state):
            await context.send_activity({"type": "typing"})
            reply = await self._agent.process_user_message(
                context.activity.text or "",
                self._adapter.authorization,
                AUTH_HANDLER_NAME or None,
                context,
            )
            await context.send_activity(reply)

        notifications = AgentNotification(self._adapter)

        @notifications.on_agent_notification(ChannelId(channel="agents", sub_channel="*"))
        async def on_notification(context, state, notification):
            reply = await self._agent.handle_agent_notification_activity(
                getattr(context.activity, "name", None),
                context.activity.value,
                context,
                None,
                AUTH_HANDLER_NAME or None,
            )
            if reply:
                await context.send_activity(reply)

    async def start_server(self):
        await self._agent.initialize()
        connection_manager = MsalConnectionManager.from_environment()
        self._adapter = CloudAdapter(connection_manager=connection_manager)
        self._setup_handlers()

        self._app = web.Application()
        self._app.router.add_post("/api/messages", self._handle_messages)
        self._app.router.add_get("/api/health", self._handle_health)

        port = int(os.getenv("PORT", "3978"))
        runner = web.AppRunner(self._app)
        await runner.setup()
        await web.TCPSite(runner, "0.0.0.0", port).start()
        logger.info("Agent server running on port %s", port)
        await asyncio.Event().wait()

    async def _handle_messages(self, request: web.Request) -> web.Response:
        try:
            return await self._adapter.process(request)
        except Exception as err:  # noqa: BLE001 — 500 を返してイベントループを守る
            logger.exception("adapter.process raised", exc_info=err)
            return web.Response(
                status=500,
                text='{"error":"Internal server error"}',
                content_type="application/json",
            )

    async def _handle_health(self, request: web.Request) -> web.Response:
        return web.Response(text='{"status":"healthy"}', content_type="application/json")


def create_and_run_host(agent_class: Type[AgentInterface]):
    asyncio.run(GenericAgentHost(agent_class()).start_server())
