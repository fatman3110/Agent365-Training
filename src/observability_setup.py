# observability_setup.py — Agent 365 Observability 配線（OBO エンドポイント）
#
# ★ スターター（Preview 前提）。パッケージ名・API は現行 SDK で要確認。
# use_s2s_endpoint=False で OBO 用の /observability/... エンドポイントへ送る。
from microsoft_agents_a365.observability.core import configure
from microsoft_agents_a365.observability.core.exporters.agent365_exporter_options import (
    Agent365ExporterOptions,
)

from obo import exchange_obo

# per-request のユーザートークンを供給するための簡易ストア。
# 実装では request context（ミドルウェア等）からアサーションを渡す。
_current_user_token: dict[str, str] = {}


def set_user_assertion(assertion: str) -> None:
    """メッセージ処理の入口で、そのターンのユーザートークンを登録する。"""
    _current_user_token["assertion"] = assertion


def _token_resolver(agent_id: str, tenant_id: str) -> str | None:
    assertion = _current_user_token.get("assertion")
    return exchange_obo(assertion) if assertion else None


def setup_observability(agent_name: str = "myagent") -> None:
    """OBO エンドポイント向けに Observability exporter を初期化する。"""
    configure(
        service_name=f"{agent_name}-runtime",
        service_namespace="ai.agents.selfhosted",
        exporter_options=Agent365ExporterOptions(
            token_resolver=_token_resolver,
            use_s2s_endpoint=False,  # ★OBO: /observability/... (agentic token cache)
        ),
    )
