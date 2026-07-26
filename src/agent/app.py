# app.py — AgentApplication 本体（現行 A365 SDK 準拠）
#
# ★ スターター（Preview 前提）。会話ロジック（頭脳）はここに書く。
#   ホスティング層は start_server.py（本リポジトリ同梱）。

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
from microsoft.opentelemetry.a365.runtime.environment_utils import (
    get_observability_authentication_scope,
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
from token_cache import cache_agentic_token

# start_server.py が提供（ホスティング層＝受付・起動。baggage 配線もここ）。
from start_server import build_adapter, load_agent_configuration  # type: ignore

# `AgentApplication:AgenticAuthHandlerName` に相当。ハードコードせず環境変数から読む
# （a365 setup all が .env に書く AGENTAPPLICATION__USERAUTHORIZATION__HANDLERS__<name>__... の <name>）。
AGENTIC_AUTH_HANDLER_NAME = os.environ.get("AGENTIC_AUTH_HANDLER_NAME", "AGENTIC")

_config = load_agent_configuration()
_adapter, _connection_manager = build_adapter(_config)

# connection_manager と **_config（AGENTAPPLICATION セクション）を渡すことで、
# Authorization が USERAUTHORIZATION.HANDLERS.AGENTIC の設定を認識する。
AGENT_APP = AgentApplication[TurnState](
    storage=MemoryStorage(),
    adapter=_adapter,
    connection_manager=_connection_manager,
    **_config,
)


@AGENT_APP.message("/help")
async def _help(ctx: TurnContext, _: TurnState):
    await ctx.send_activity("Send any message to chat.")


# A365 Observability — best-effort instrumentation (verify against official sample)
# A365 auth mode: obo（非 AI Teammate・委任） — 参考: https://learn.microsoft.com/en-us/entra/agent-id/agent-on-behalf-of-oauth-flow
async def _setup_observability_token(ctx: TurnContext, tenant_id: str, agent_id: str) -> None:
    """OBO: 観測トークンを交換して token_cache に書き込む（exporter が後で読み出す）。失敗しても会話は継続する。"""
    try:
        exaau_token = await AGENT_APP.auth.exchange_token(
            ctx,
            scopes=get_observability_authentication_scope(),
            auth_handler_id=AGENTIC_AUTH_HANDLER_NAME,
        )
        cache_agentic_token(tenant_id, agent_id, exaau_token.token)
    except Exception as exc:  # noqa: BLE001 — 観測失敗で会話を止めない
        print(f"[observability] token exchange failed: {exc}")


@AGENT_APP.activity("message", auth_handlers=[AGENTIC_AUTH_HANDLER_NAME])
async def _on_message(ctx: TurnContext, _: TurnState):
    recipient = ctx.activity.recipient
    tenant_id = getattr(recipient, "tenant_id", None) or os.environ.get(
        "AGENT365OBSERVABILITY__TENANTID", ""
    )
    agent_id = getattr(recipient, "agentic_app_id", None) or os.environ.get(
        "AGENT365OBSERVABILITY__AGENTID", ""
    )

    # OBO: ターン毎に観測トークンを更新（S2S では呼ばない）。
    await _setup_observability_token(ctx, tenant_id, agent_id)

    user_text = ctx.activity.text or ""
    has_observability_identity = bool(agent_id) and bool(tenant_id)

    if not has_observability_identity:
        # 身元が解決できないターンは観測をスキップして応答だけ返す。
        reply = chat_complete(user_text)
        await ctx.send_activity(reply)
        return

    agent_details = AgentDetails(
        agent_id=agent_id,
        agent_name=os.environ.get("AGENT365OBSERVABILITY__AGENTNAME", "A365 Training Agent"),
        agent_description=os.environ.get("AGENT365OBSERVABILITY__AGENTDESCRIPTION", ""),
        agent_blueprint_id=os.environ.get("AGENT365OBSERVABILITY__AGENTBLUEPRINTID", ""),
        tenant_id=tenant_id,
    )
    scope_details = InvokeAgentScopeDetails(
        endpoint=ServiceEndpoint(hostname=os.environ.get("WEBSITE_HOSTNAME", "localhost"), port=443),
    )
    from_property = ctx.activity.from_property
    conversation = ctx.activity.conversation
    request = Request(
        content=user_text,
        session_id=getattr(conversation, "id", "") or "",
        conversation_id=getattr(conversation, "id", "") or "",
        channel=Channel(name=ctx.activity.channel_id or "custom"),
    )
    caller_details = CallerDetails(
        user_details=UserDetails(
            user_id=getattr(from_property, "id", "") or "",
            user_email="",  # このチャネルは UPN を運ばないため空のまま（既知の制限）
            user_name=getattr(from_property, "name", "") or "unknown",
        ),
    )

    # LLM 呼び出し自体は distro が自動計装し gen_ai span を出す（Python + OpenAI SDK は自動計装対象）。
    with InvokeAgentScope.start(request, scope_details, agent_details, caller_details) as scope:
        scope.record_input_messages([user_text])
        reply = chat_complete(user_text)
        scope.record_output_messages([reply])

    await ctx.send_activity(reply)
