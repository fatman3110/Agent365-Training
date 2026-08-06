"""A2A protocol routes for the existing Agent 365 training agent."""

from __future__ import annotations

import asyncio
import os
import uuid

from a2a.compat.v0_3 import types as a2a_v03
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    add_a2a_routes_to_fastapi,
    create_jsonrpc_routes,
    create_rest_routes,
)
from a2a.server.tasks import InMemoryTaskStore
from a2a.types.a2a_pb2 import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
    APIKeySecurityScheme,
    Message,
    Part,
    Role,
    SecurityRequirement,
    SecurityScheme,
    StringList,
)
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from agent_service import run_agent_turn

_API_KEY_HEADER = "X-A2A-API-Key"


class TrainingAgentExecutor(AgentExecutor):
    """Execute text A2A requests against the shared training agent logic."""

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        user_text = context.get_user_input().strip()
        if not user_text:
            reply = "A text message is required."
        else:
            session_id = context.context_id or str(uuid.uuid4())
            reply = await asyncio.to_thread(run_agent_turn, user_text, session_id, "a2a")

        await event_queue.enqueue_event(
            Message(
                message_id=str(uuid.uuid4()),
                context_id=context.context_id or "",
                role=Role.ROLE_AGENT,
                parts=[Part(text=reply, media_type="text/plain")],
            )
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        del context, event_queue


def add_a2a_routes(app: FastAPI) -> None:
    """Register Copilot Studio-compatible A2A v0.3 routes and Agent Card."""
    hostname = os.environ.get("WEBSITE_HOSTNAME", "localhost:3978")
    base_url = os.environ.get("A2A_PUBLIC_BASE_URL", f"https://{hostname}").rstrip("/")
    endpoint_url = f"{base_url}/a2a"
    name = os.environ.get("A2A_AGENT_NAME", "Agent 365 Training Assistant")
    description = os.environ.get(
        "A2A_AGENT_DESCRIPTION",
        "Agent 365 の学習と検証を支援し、Microsoft Teams と Agent2Agent (A2A) 経由の質問に日本語で回答する汎用アシスタントです。",
    )

    api_key_scheme = SecurityScheme(
        api_key_security_scheme=APIKeySecurityScheme(
            description="API key required for A2A requests.",
            location="header",
            name=_API_KEY_HEADER,
        )
    )
    agent_card = AgentCard(
        name=name,
        description=description,
        supported_interfaces=[
            AgentInterface(
                url=endpoint_url,
                protocol_binding="JSONRPC",
                protocol_version="1.0",
            ),
            AgentInterface(
                url=endpoint_url,
                protocol_binding="HTTP+JSON",
                protocol_version="1.0",
            ),
        ],
        version="1.0.0",
        capabilities=AgentCapabilities(streaming=False),
        security_schemes={"apiKey": api_key_scheme},
        security_requirements=[
            SecurityRequirement(schemes={"apiKey": StringList(list=[])})
        ],
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        skills=[
            AgentSkill(
                id="general-assistance",
                name="General assistance",
                description=description,
                tags=["training", "assistant", "a2a"],
                examples=["このエージェントについて説明してください。"],
                input_modes=["text/plain"],
                output_modes=["text/plain"],
            )
        ],
    )
    compatibility_card = a2a_v03.AgentCard(
        name=name,
        description=description,
        url=endpoint_url,
        version="1.0.0",
        protocolVersion="0.3.0",
        preferredTransport="JSONRPC",
        capabilities=a2a_v03.AgentCapabilities(streaming=False),
        securitySchemes={
            "apiKey": a2a_v03.SecurityScheme(
                root=a2a_v03.APIKeySecurityScheme(
                    name=_API_KEY_HEADER,
                    in_=a2a_v03.In.header,
                    description="API key required for A2A requests.",
                )
            )
        },
        security=[{"apiKey": []}],
        defaultInputModes=["text/plain"],
        defaultOutputModes=["text/plain"],
        skills=[
            a2a_v03.AgentSkill(
                id="general-assistance",
                name="General assistance",
                description=description,
                tags=["training", "assistant", "a2a"],
                examples=["このエージェントについて説明してください。"],
                inputModes=["text/plain"],
                outputModes=["text/plain"],
            )
        ],
    )

    async def compatibility_card_response() -> JSONResponse:
        return JSONResponse(
            compatibility_card.model_dump(by_alias=True, exclude_none=True)
        )

    for compatibility_path in (
        "/.well-known/agent-card.json",
        "/.well-known/agent.json",
        "/.well-known/agentcard.json",
        "/.well-known/agentCard.json",
        "/.well-known/agent_card.json",
        "/a2a/.well-known/agent-card.json",
        "/a2a/.well-known/agent.json",
        "/a2a/.well-known/agentcard.json",
        "/a2a/.well-known/agentCard.json",
        "/a2a/.well-known/agent_card.json",
        "/a2a",
    ):
        app.add_api_route(
            compatibility_path,
            compatibility_card_response,
            methods=["GET"],
        )
    request_handler = DefaultRequestHandler(
        agent_executor=TrainingAgentExecutor(),
        task_store=InMemoryTaskStore(),
        agent_card=agent_card,
    )

    add_a2a_routes_to_fastapi(
        app,
        agent_card_routes=[],
        jsonrpc_routes=create_jsonrpc_routes(
            request_handler,
            rpc_url="/a2a",
            enable_v0_3_compat=True,
        ),
        rest_routes=create_rest_routes(
            request_handler,
            enable_v0_3_compat=True,
            path_prefix="/a2a",
        ),
    )