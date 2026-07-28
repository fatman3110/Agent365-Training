# app.py — AgentApplication 本体（S2S・非 AI Teammate）
#
# 観測トークンの取得は start_server.py がバックグラウンドで行う（observability/token_service.py）。
# このファイルは per-turn のトークン交換に一切関与しない。

# 観測は「他モジュールの import より前」に初期化する（openai を自動計装させるため）。
from observability_setup import configure_observability

configure_observability()

import os

from microsoft_agents.hosting.core import (
    AgentApplication,
    MemoryStorage,
    TurnContext,
    TurnState,
)
from microsoft.opentelemetry.a365.core import (
    AgentDetails,
    CallerDetails,
    Channel,
    InvokeAgentScope,
    InvokeAgentScopeDetails,
    Request,
    ServiceEndpoint,
    UserDetails,
)

from llm import chat_complete

# start_server.py が提供（ホスティング層＝受付・起動。baggage 配線もここ）。
from start_server import build_adapter, load_agent_configuration  # type: ignore

_TENANT_ID = os.environ.get("AGENT365OBSERVABILITY__TENANTID", "")
_AGENT_ID = os.environ.get("AGENT365OBSERVABILITY__AGENTID", "")
_AGENT_BLUEPRINT_ID = os.environ.get("AGENT365OBSERVABILITY__AGENTBLUEPRINTID", "")
_AGENT_NAME = os.environ.get("AGENT365OBSERVABILITY__AGENTNAME", "A365 Handson Agent")
_AGENT_DESCRIPTION = os.environ.get("AGENT365OBSERVABILITY__AGENTDESCRIPTION", "")

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
    has_observability_identity = bool(_AGENT_ID) and bool(_TENANT_ID)

    if not has_observability_identity:
        reply = chat_complete(user_text)
        await ctx.send_activity(reply)
        return

    agent_details = AgentDetails(
        agent_id=_AGENT_ID,
        agent_name=_AGENT_NAME,
        agent_description=_AGENT_DESCRIPTION,
        agent_blueprint_id=_AGENT_BLUEPRINT_ID,
        tenant_id=_TENANT_ID,
    )
    scope_details = InvokeAgentScopeDetails(
        endpoint=ServiceEndpoint(hostname=os.environ.get("WEBSITE_HOSTNAME", "localhost"), port=443),
    )
    conversation = ctx.activity.conversation
    request = Request(
        content=user_text,
        session_id=getattr(conversation, "id", "") or "",
        conversation_id=getattr(conversation, "id", "") or "",
        channel=Channel(name=ctx.activity.channel_id or "custom"),
    )
    # S2S にはユーザー OBO コンテキストが無いため blueprint の sponsor identity を使う
    caller_details = CallerDetails(
        user_details=UserDetails(
            user_id=os.environ.get("AGENT365OBSERVABILITY__SPONSORUSERID", "")
            or os.environ.get("AGENT365OBSERVABILITY__CLIENTID", ""),
            user_email=os.environ.get("AGENT365OBSERVABILITY__SPONSORUSEREMAIL", ""),
            user_name=os.environ.get("AGENT365OBSERVABILITY__SPONSORUSERNAME", _AGENT_NAME),
        ),
    )

    with InvokeAgentScope.start(request, scope_details, agent_details, caller_details) as scope:
        scope.record_input_messages([user_text])
        reply = chat_complete(user_text)
        scope.record_output_messages([reply])

    await ctx.send_activity(reply)
