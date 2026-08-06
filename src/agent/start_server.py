# start_server.py — ホスティング層（受付・起動、S2S 観測トークンのバックグラウンド取得）
from __future__ import annotations

import asyncio
import hmac
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response
from microsoft_agents.activity.config import load_configuration_from_env
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.hosting.fastapi import CloudAdapter
from microsoft.opentelemetry.a365.hosting import (
    ObservabilityHostingManager,
    ObservabilityHostingOptions,
)

from observability.token_service import acquire_initial_token, run_token_service
from llm import warm_up_llm

logger = logging.getLogger(__name__)

_MAX_REQUEST_BYTES = 1_048_576
_PUBLIC_A2A_DISCOVERY_PATHS = {
    "/.well-known/agent-card.json",
    "/.well-known/agent.json",
    "/.well-known/agentcard.json",
    "/.well-known/agentCard.json",
    "/.well-known/agent_card.json",
    "/a2a",
    "/a2a/.well-known/agent-card.json",
    "/a2a/.well-known/agent.json",
    "/a2a/.well-known/agentcard.json",
    "/a2a/.well-known/agentCard.json",
    "/a2a/.well-known/agent_card.json",
}

_A365_TENANT_ID = os.environ.get("AGENT365OBSERVABILITY__TENANTID", "")
_A365_AGENT_ID = os.environ.get("AGENT365OBSERVABILITY__AGENTID", "")
_A365_CLIENT_ID = os.environ.get("AGENT365OBSERVABILITY__CLIENTID", "")
_A365_CLIENT_SECRET = os.environ.get("AGENT365OBSERVABILITY__CLIENTSECRET", "")
_A365_ENABLED = bool(_A365_TENANT_ID and _A365_AGENT_ID and _A365_CLIENT_ID and _A365_CLIENT_SECRET)


def load_agent_configuration() -> dict:
    """.env の CONNECTIONS__* / AGENTAPPLICATION__* / CONNECTIONSMAP__* をパースする。"""
    return load_configuration_from_env(dict(os.environ))


def build_adapter(config: dict) -> tuple[CloudAdapter, MsalConnectionManager]:
    """CloudAdapter と ConnectionManager を構築する（Teams チャネル認証用。Observability の
    S2S トークン取得とは独立している）。"""
    connection_manager = MsalConnectionManager(**config)
    adapter = CloudAdapter(connection_manager=connection_manager)

    ObservabilityHostingManager.configure(
        adapter.middleware_set,
        ObservabilityHostingOptions(enable_baggage=True, enable_output_logging=True),
    )
    return adapter, connection_manager


async def _handle_messages(request: Request, agent_app) -> Response:
    try:
        body = await request.json()
    except Exception:
        body = {}
    if not isinstance(body, dict):
        return JSONResponse(status_code=400, content={"error": "Invalid activity payload"})
    sender = body.get("from")
    logger.info(
        "[/api/messages] type=%s sender_present=%s text_present=%s",
        body.get("type"), isinstance(sender, dict), bool(body.get("text")),
    )
    try:
        return await agent_app.adapter.process(request, agent_app)
    except Exception:
        logger.exception("[/api/messages] adapter.process failed")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"},
        )


async def _handle_health(_request: Request) -> JSONResponse:
    return JSONResponse(
        {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}
    )


async def _handle_privacy(_request: Request) -> HTMLResponse:
    return HTMLResponse(
        "<html><body><h1>Privacy Statement</h1><p>This is a training/demo agent. "
        "No personal data is retained beyond the current conversation turn.</p></body></html>"
    )


async def _handle_terms(_request: Request) -> HTMLResponse:
    return HTMLResponse(
        "<html><body><h1>Terms of Use</h1><p>This is a training/demo agent provided "
        "as-is for Agent 365 hands-on purposes only.</p></body></html>"
    )


async def _start_observability_token_service() -> asyncio.Task | None:
    if not _A365_ENABLED:
        logger.warning("Agent365 observability credentials not configured — skipping token service.")
        return None
    try:
        await acquire_initial_token(
            tenant_id=_A365_TENANT_ID,
            agent_id=_A365_AGENT_ID,
            blueprint_client_id=_A365_CLIENT_ID,
            blueprint_client_secret=_A365_CLIENT_SECRET,
        )
    except Exception:
        logger.warning("Initial observability token acquisition failed; will retry in background.", exc_info=True)

    return asyncio.create_task(
        run_token_service(
            tenant_id=_A365_TENANT_ID,
            agent_id=_A365_AGENT_ID,
            blueprint_client_id=_A365_CLIENT_ID,
            blueprint_client_secret=_A365_CLIENT_SECRET,
        )
    )


async def _stop_observability_token_service(task: asyncio.Task | None) -> None:
    if task:
        task.cancel()


def create_app(agent_app) -> FastAPI:
    """Teams と A2A を同じ HTTP サーフェスに公開する。"""
    from a2a_server import add_a2a_routes

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        token_task = await _start_observability_token_service()
        try:
            logger.info("Waiting for the configured Ollama model to become ready.")
            await asyncio.to_thread(warm_up_llm)
            logger.info("Ollama model is loaded and ready.")
            yield
        finally:
            await _stop_observability_token_service(token_task)

    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def secure_a2a(request: Request, call_next):
        is_public_discovery = (
            request.method in {"GET", "OPTIONS"}
            and request.url.path in _PUBLIC_A2A_DISCOVERY_PATHS
        )
        if request.url.path.startswith("/a2a") and not is_public_discovery:
            expected_key = os.environ.get("A2A_API_KEY", "")
            supplied_key = request.headers.get("X-A2A-API-Key", "")
            if not expected_key or not hmac.compare_digest(supplied_key, expected_key):
                return JSONResponse(status_code=401, content={"error": "Unauthorized"})

        if request.method in {"POST", "PUT", "PATCH"}:
            content_length = request.headers.get("content-length")
            if content_length:
                try:
                    if int(content_length) > _MAX_REQUEST_BYTES:
                        return JSONResponse(status_code=413, content={"error": "Request too large"})
                except ValueError:
                    return JSONResponse(status_code=400, content={"error": "Invalid Content-Length"})

            body = bytearray()
            async for chunk in request.stream():
                if len(body) + len(chunk) > _MAX_REQUEST_BYTES:
                    return JSONResponse(status_code=413, content={"error": "Request too large"})
                body.extend(chunk)
            request._body = bytes(body)
        return await call_next(request)

    async def messages(request: Request) -> Response:
        return await _handle_messages(request, agent_app)

    app.add_api_route("/api/messages", messages, methods=["POST"])
    app.add_api_route("/api/health", _handle_health, methods=["GET"])
    app.add_api_route("/privacy", _handle_privacy, methods=["GET"])
    app.add_api_route("/terms", _handle_terms, methods=["GET"])
    add_a2a_routes(app)
    return app


async def run_server(agent_app) -> None:
    """FastAPI サーバーを起動し、Teams と A2A の両方を公開する。"""
    app = create_app(agent_app)

    port = int(os.getenv("PORT", "3978"))
    logger.info("Agent server running on port %d (Teams + A2A)", port)
    server = uvicorn.Server(uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info"))
    await server.serve()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from app import AGENT_APP

    asyncio.run(run_server(AGENT_APP))
