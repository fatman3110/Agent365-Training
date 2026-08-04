"""Shared agent turn execution for Teams and A2A transports."""

from __future__ import annotations

import os

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

_TENANT_ID = os.environ.get("AGENT365OBSERVABILITY__TENANTID", "")
_AGENT_ID = os.environ.get("AGENT365OBSERVABILITY__AGENTID", "")
_AGENT_BLUEPRINT_ID = os.environ.get("AGENT365OBSERVABILITY__AGENTBLUEPRINTID", "")
_AGENT_NAME = os.environ.get("AGENT365OBSERVABILITY__AGENTNAME", "A365 Handson Agent")
_AGENT_DESCRIPTION = os.environ.get("AGENT365OBSERVABILITY__AGENTDESCRIPTION", "")


def run_agent_turn(user_text: str, session_id: str, channel_name: str) -> str:
    """Run one agent turn with Agent 365 semantic tracing when configured."""
    if not (_AGENT_ID and _TENANT_ID):
        return chat_complete(user_text)

    agent_details = AgentDetails(
        agent_id=_AGENT_ID,
        agent_name=_AGENT_NAME,
        agent_description=_AGENT_DESCRIPTION,
        agent_blueprint_id=_AGENT_BLUEPRINT_ID,
        tenant_id=_TENANT_ID,
    )
    scope_details = InvokeAgentScopeDetails(
        endpoint=ServiceEndpoint(
            hostname=os.environ.get("WEBSITE_HOSTNAME", "localhost"),
            port=443,
        ),
    )
    request = Request(
        content=user_text,
        session_id=session_id,
        conversation_id=session_id,
        channel=Channel(name=channel_name),
    )
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
        return reply