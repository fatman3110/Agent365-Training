# Copyright (c) Microsoft Corporation. Licensed under the MIT License.
# TurnContext から A365 観測性用の details を抽出する共有ユーティリティ。
# 公式サンプル（python/claude/sample-agent/turn_context_utils.py）準拠。
import uuid
from dataclasses import dataclass
from typing import Optional

from microsoft_agents.hosting.core import TurnContext
from microsoft_agents_a365.observability.core import (
    AgentDetails,
    InvokeAgentScopeDetails,
    Request,
)
from microsoft_agents_a365.observability.core.middleware.baggage_builder import BaggageBuilder
from microsoft_agents_a365.observability.core.models.caller_details import CallerDetails
from microsoft_agents_a365.observability.core.models.user_details import UserDetails
from microsoft_agents_a365.observability.hosting.scope_helpers.populate_baggage import populate


@dataclass
class TurnContextDetails:
    """TurnContext から抽出した観測性用の詳細。"""

    tenant_id: Optional[str]
    agent_id: Optional[str]
    agent_name: Optional[str]
    agent_upn: Optional[str]
    agent_blueprint_id: Optional[str]
    agent_auid: Optional[str]
    conversation_id: Optional[str]
    correlation_id: str
    caller_id: Optional[str]
    caller_name: Optional[str]
    caller_aad_object_id: Optional[str]


def extract_turn_context_details(context: TurnContext) -> TurnContextDetails:
    """TurnContext から tenant / agent / caller / conversation を抽出する。"""
    activity = context.activity
    recipient = activity.recipient if activity.recipient else None

    tenant_id = recipient.tenant_id if recipient else None
    # 実行時 Agent Identity（AUID）を優先。取れなければ recipient.id にフォールバック
    agent_id = activity.get_agentic_instance_id()
    if not agent_id:
        agent_id = getattr(recipient, "id", None) if recipient else None
    agent_name = getattr(recipient, "name", None) if recipient else None
    agent_upn = getattr(recipient, "name", None) if recipient else None
    agent_blueprint_id = getattr(recipient, "agentic_app_id", None) if recipient else None
    agent_auid = getattr(recipient, "agentic_user_id", None) if recipient else None

    conversation_id = activity.conversation.id if activity.conversation else None
    correlation_id = str(uuid.uuid4())

    caller = activity.from_property if activity and activity.from_property else None
    caller_id = getattr(caller, "id", None)
    caller_name = getattr(caller, "name", None)
    caller_aad_object_id = getattr(caller, "aad_object_id", None)

    return TurnContextDetails(
        tenant_id=tenant_id or "default-tenant",
        agent_id=agent_id,
        agent_name=agent_name,
        agent_upn=agent_upn,
        agent_blueprint_id=agent_blueprint_id,
        agent_auid=agent_auid,
        conversation_id=conversation_id,
        correlation_id=correlation_id,
        caller_id=caller_id,
        caller_name=caller_name,
        caller_aad_object_id=caller_aad_object_id,
    )


def create_agent_details(
    details: TurnContextDetails,
    description: str = "Foundry のクラウドモデルで動く AI Teammate",
) -> AgentDetails:
    """観測性用の AgentDetails を組み立てる。"""
    return AgentDetails(
        agent_id=details.agent_id,
        agent_name=details.agent_name,
        agent_description=description,
        tenant_id=details.tenant_id,
        agentic_user_id=details.agent_auid,
        agent_blueprint_id=details.agent_blueprint_id,
    )


def create_caller_details(details: TurnContextDetails) -> CallerDetails:
    """観測性用の CallerDetails を組み立てる（人間の呼び出し元 OID を優先）。"""
    return CallerDetails(
        user_details=UserDetails(
            user_id=details.caller_aad_object_id or details.caller_id or "unknown-user-id",
            user_name=details.caller_name,
        ),
    )


def create_request(details: TurnContextDetails, message: str) -> Request:
    """観測性用の Request（入力・会話 ID）を組み立てる。"""
    return Request(
        content=message,
        session_id=details.conversation_id,
        conversation_id=details.conversation_id,
    )


def create_invoke_agent_details(details: TurnContextDetails) -> InvokeAgentScopeDetails:
    """InvokeAgentScope 用の scope details を組み立てる。"""
    return InvokeAgentScopeDetails()


def build_baggage_builder(context: TurnContext) -> BaggageBuilder:
    """TurnContext から baggage（span 間で伝播する文脈）を構築する。"""
    builder = BaggageBuilder()
    populate(builder, context)
    return builder
