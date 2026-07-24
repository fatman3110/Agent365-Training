# obo.py — OBO（On-Behalf-Of）トークン交換
#
# ★ スターター（Preview 前提）。MSAL の一般的な OBO 実装例。
# Agent 365 の agentic token cache を使う場合は SDK 側の resolver に委譲する。
from os import environ

import msal

_cca = msal.ConfidentialClientApplication(
    client_id=environ.get("CONNECTIONS__SERVICE_CONNECTION__SETTINGS__CLIENTID", ""),
    authority=f"https://login.microsoftonline.com/{environ.get('TENANT_ID', '')}",
    # 本番は Managed Identity / Workload Identity（FIC）推奨。学習時のみ secret。
    client_credential=environ.get("CLIENT_SECRET"),
)

# 観測用スコープ（例）。実値は a365 setup all / Learn に従って設定する。
OBS_SCOPE = [environ.get("OBS_SCOPE", "api://<obs-app-id>/Agent365.Observability.OtelWrite")]


def exchange_obo(user_assertion: str) -> str | None:
    """受け取ったユーザートークンを観測スコープの OBO トークンに交換する。"""
    result = _cca.acquire_token_on_behalf_of(
        user_assertion=user_assertion, scopes=OBS_SCOPE
    )
    return result.get("access_token")
