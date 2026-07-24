# app.py — AgentApplication 本体（on_message で LLM 呼び出し）
#
# ★ スターター（Preview 前提）。
# build_adapter は Skills が生成する start_server.py に含まれる想定。
# `a365 setup all` / make-a365-agent 実行後、生成された骨格に本ロジックを差し込む。
from microsoft_agents.hosting.core import (
    AgentApplication,
    MemoryStorage,
    TurnContext,
    TurnState,
)

from llm import chat_complete

# Skills 生成の start_server.py が提供する想定（未生成なら import エラーになる）。
from start_server import build_adapter  # type: ignore

AGENT_APP = AgentApplication[TurnState](
    storage=MemoryStorage(), adapter=build_adapter()
)


@AGENT_APP.message("/help")
async def _help(ctx: TurnContext, _: TurnState):
    await ctx.send_activity("Send any message to chat.")


@AGENT_APP.activity("message")
async def _on_message(ctx: TurnContext, _: TurnState):
    reply = chat_complete(ctx.activity.text or "")
    await ctx.send_activity(reply)
