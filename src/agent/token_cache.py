# token_cache.py — Agent 365 Observability トークンキャッシュ（OBO / agentic-user 用）
# A365 Observability — best-effort instrumentation (verify against official sample)
#
# instrument-observability Skill の Phase 5（Python OBO path）に沿った実装。
# `use_microsoft_opentelemetry(a365_token_resolver=get_cached_agentic_token)` の解決先。
# メッセージハンドラ側が `exchange_token()` の結果を `cache_agentic_token()` で書き込む。
from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone

_lock = threading.Lock()
_cache: dict[str, tuple[str, datetime]] = {}
_EXPIRY_BUFFER = timedelta(minutes=5)


def cache_agentic_token(
    tenant_id: str, agent_id: str, token: str, expires_in: timedelta = timedelta(hours=1)
) -> None:
    """ターン毎の OBO トークン交換結果をキャッシュする。"""
    key = f"{agent_id}:{tenant_id}"
    expires_at = datetime.now(timezone.utc) + expires_in
    with _lock:
        _cache[key] = (token, expires_at)


def get_cached_agentic_token(agent_id: str, tenant_id: str) -> str | None:
    """exporter が呼ぶ解決器。期限切れなら None を返す（exporter 側は再試行/スキップする）。"""
    key = f"{agent_id}:{tenant_id}"
    with _lock:
        entry = _cache.get(key)
        if entry is None:
            return None
        token, expires_at = entry
        if datetime.now(timezone.utc) + _EXPIRY_BUFFER >= expires_at:
            del _cache[key]
            return None
        return token
