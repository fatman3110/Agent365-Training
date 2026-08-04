# observability/token_service.py — S2S 観測トークン取得（3-hop FMI チェーン）
#
# Hop1+2: Blueprint（client secret）→ Agent Identity への FMI トークン
#         （MSAL Python は fmi_path 未対応のため httpx で直接 POST する）
# Hop3:   Agent Identity が Hop1+2 のトークンをアサーションにして Observability API トークンを取得
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

import httpx
import msal

from observability import token_cache

logger = logging.getLogger(__name__)

FMI_SCOPE = "api://AzureADTokenExchange/.default"
OBSERVABILITY_SCOPES = ["api://9b975845-388f-4429-889e-eab1ef63949c/.default"]
REFRESH_INTERVAL_SECONDS = 50 * 60  # 有効期限1時間に対して余裕を持たせる


async def acquire_initial_token(
    tenant_id: str, agent_id: str, blueprint_client_id: str, blueprint_client_secret: str
) -> None:
    await _acquire_and_cache_token(tenant_id, agent_id, blueprint_client_id, blueprint_client_secret)


async def run_token_service(
    tenant_id: str, agent_id: str, blueprint_client_id: str, blueprint_client_secret: str
) -> None:
    logger.info("ObservabilityTokenService started (S2S, refresh every %ds).", REFRESH_INTERVAL_SECONDS)
    while True:
        try:
            await _acquire_and_cache_token(tenant_id, agent_id, blueprint_client_id, blueprint_client_secret)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.warning(
                "Observability token acquisition failed; will retry in %ds.",
                REFRESH_INTERVAL_SECONDS,
                exc_info=True,
            )
        await asyncio.sleep(REFRESH_INTERVAL_SECONDS)


async def _acquire_and_cache_token(
    tenant_id: str, agent_id: str, blueprint_client_id: str, blueprint_client_secret: str
) -> None:
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    fmi_token = await _acquire_fmi_token(token_url, blueprint_client_id, blueprint_client_secret, agent_id)

    identity_app = msal.ConfidentialClientApplication(
        client_id=agent_id,
        client_credential={"client_assertion": fmi_token},
        authority=f"https://login.microsoftonline.com/{tenant_id}",
    )
    result = await asyncio.to_thread(
        identity_app.acquire_token_for_client,
        scopes=OBSERVABILITY_SCOPES,
    )
    if "access_token" not in result:
        raise RuntimeError(
            f"Observability token acquisition failed (Hop 3): "
            f"{result.get('error')}: {result.get('error_description')}"
        )

    token_cache.cache_token(
        agent_id,
        tenant_id,
        result["access_token"],
        expires_in=timedelta(seconds=int(result.get("expires_in", 3600))),
    )
    logger.info("Observability token refreshed for agent_id=%s.", agent_id)


async def _acquire_fmi_token(
    token_url: str, blueprint_client_id: str, blueprint_client_secret: str, agent_id: str
) -> str:
    data = {
        "grant_type": "client_credentials",
        "client_id": blueprint_client_id,
        "client_secret": blueprint_client_secret,
        "scope": FMI_SCOPE,
        "fmi_path": agent_id,
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(token_url, data=data)
    response.raise_for_status()
    body = response.json()
    if "access_token" not in body:
        raise RuntimeError(f"FMI token acquisition failed (Hop 1+2): {body}")
    return body["access_token"]
