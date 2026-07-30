# Copyright (c) Microsoft Corporation. Licensed under the MIT License.
# A365 観測性の初期化。configure() を一度だけ呼び、span を A365 にエクスポートする。
# token_resolver は host が exchange_token でキャッシュしたエージェンティックトークンを返す。
import logging
import os
import sys

from microsoft_agents_a365.observability.core.config import configure, is_configured
import token_cache
from token_cache import get_cached_agentic_token

logger = logging.getLogger(__name__)

# host は microsoft_agents ロガーにしかハンドラを付けないため、root と観測性ロガーに
# stdout ハンドラを付けて configure / exporter の INFO ログをコンテナログに出す。
if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
_obs_logger = logging.getLogger("microsoft_agents_a365.observability")
_obs_logger.setLevel(logging.INFO)
if not _obs_logger.handlers:
    _h = logging.StreamHandler(sys.stdout)
    _h.setFormatter(logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s"))
    _obs_logger.addHandler(_h)

_configured = False


def _token_resolver(agent_id: str, tenant_id: str) -> str | None:
    # exporter は (agent_id, tenant_id) の順で呼ぶ。キャッシュのキーは (tenant_id, agent_id)。
    token = get_cached_agentic_token(tenant_id, agent_id)
    if token:
        return token
    # フォールバック: host は recipient.agentic_app_id（Blueprint 相当 id）でキャッシュするが、
    # span/AgentDetails は get_agentic_instance_id()（AUID）を使うため id が食い違い得る。
    # 同一テナントのキャッシュ済みトークンを返す（このコンテナは自分のトークンのみ保持）。
    for key, val in token_cache._agentic_token_cache.items():
        if key.startswith(f"{tenant_id}:") and val:
            logger.info("token_resolver: フォールバックでキャッシュトークンを使用 (key=%s, 要求 agent=%s)", key, agent_id)
            return val
    logger.warning("token_resolver: トークン未発見 (agent=%s, tenant=%s)", agent_id, tenant_id)
    return None


def configure_observability() -> bool:
    """A365 観測性を初期化する（多重呼び出しは無視）。"""
    global _configured
    if _configured or is_configured():
        _configured = True
        return True
    ok = configure(
        service_name=os.getenv("OBSERVABILITY_SERVICE_NAME", "ai-teammate"),
        service_namespace=os.getenv("OBSERVABILITY_SERVICE_NAMESPACE", "agent365-training"),
        token_resolver=_token_resolver,
        cluster_category=os.getenv("PYTHON_ENVIRONMENT", "prod"),
    )
    _configured = bool(ok)
    if ok:
        logger.info("✅ A365 observability configured")
    else:
        logger.warning("⚠️ A365 observability configuration failed")
    return _configured



def is_observability_configured() -> bool:
    return _configured or is_configured()
