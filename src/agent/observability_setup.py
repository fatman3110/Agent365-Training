# observability_setup.py — Agent 365 Observability 初期化（S2S）
from microsoft.opentelemetry import use_microsoft_opentelemetry

from observability import token_cache


def configure_observability() -> None:
    """他モジュール（openai 等）の import より前に呼ぶこと（自動計装のため）。"""
    use_microsoft_opentelemetry(
        enable_a365=True,
        a365_enable_observability_exporter=True,
        a365_use_s2s_endpoint=True,
        a365_token_resolver=lambda agent_id, tenant_id: token_cache.get_cached_token(agent_id, tenant_id) or "",
    )
