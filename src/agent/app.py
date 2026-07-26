# app.py — AgentApplication 本体（現行 A365 SDK 準拠）
#
# ★ スターター（Preview 前提）。会話ロジック（頭脳）はここに書く。
#   ホスティング層（start_server.py）と観測の詳細計装（InvokeAgentScope 等）は Skills が生成する。

# 観測は「他モジュールの import より前」に初期化する（openai を自動計装させるため）。
from observability_setup import configure_observability

configure_observability()

from microsoft_agents.hosting.core import (
    AgentApplication,
    MemoryStorage,
    TurnContext,
    TurnState,
)

from llm import chat_complete

# Skills 生成の start_server.py が提供（ホスティング層＝受付・起動。baggage 配線もここ）。
from start_server import build_adapter  # type: ignore

AGENT_APP = AgentApplication[TurnState](
    storage=MemoryStorage(), adapter=build_adapter()
)


@AGENT_APP.message("/help")
async def _help(ctx: TurnContext, _: TurnState):
    await ctx.send_activity("Send any message to chat.")


@AGENT_APP.activity("message")
async def _on_message(ctx: TurnContext, _: TurnState):
    # LLM 呼び出しは distro により自動計装され、gen_ai span が出る。
    # MAC 表示に必要な InvokeAgentScope 等の意味スコープは
    # instrument-observability Skill が生成する（本体はシンプルに保つ）。
    reply = chat_complete(ctx.activity.text or "")
    await ctx.send_activity(reply)
