# app.py — AgentApplication 本体（S2S・非 AI Teammate）
#
# 観測トークンの取得は start_server.py がバックグラウンドで行う（observability/token_service.py）。
# このファイルは per-turn のトークン交換に一切関与しない。

# 観測は「他モジュールの import より前」に初期化する（openai を自動計装させるため）。
from observability_setup import configure_observability

configure_observability()

import asyncio

from microsoft_agents.hosting.core import (
    AgentApplication,
    MemoryStorage,
    TurnContext,
    TurnState,
)

from agent_service import run_agent_turn

# start_server.py が提供（ホスティング層＝受付・起動。baggage 配線もここ）。
from start_server import build_adapter, load_agent_configuration  # type: ignore

_config = load_agent_configuration()
_adapter, _connection_manager = build_adapter(_config)

AGENT_APP = AgentApplication[TurnState](
    storage=MemoryStorage(),
    adapter=_adapter,
    connection_manager=_connection_manager,
    **_config,
)


@AGENT_APP.message("/help")
async def _help(ctx: TurnContext, _: TurnState):
    await ctx.send_activity("Send any message to chat.")


@AGENT_APP.activity("message")
async def _on_message(ctx: TurnContext, _: TurnState):
    user_text = ctx.activity.text or ""
    conversation = ctx.activity.conversation
    reply = await asyncio.to_thread(
        run_agent_turn,
        user_text,
        getattr(conversation, "id", "") or "",
        ctx.activity.channel_id or "custom",
    )
    await ctx.send_activity(reply)
