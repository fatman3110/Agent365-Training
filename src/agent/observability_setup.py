# observability_setup.py — Agent 365 Observability 初期化（現行 microsoft-opentelemetry distro）
#
# A365 Observability — best-effort instrumentation (verify against official sample)
# A365 auth mode: obo（非 AI Teammate・委任）
#
# instrument-observability Skill（Phase 3/5, Python OBO path）に沿った実装。
# ターン毎のトークン交換（app.py の `_setup_observability_token`）が `token_cache.py` へ
# 書き込み、ここで登録する解決器 `get_cached_agentic_token` が exporter からの
# エクスポート時に読み出す。InvokeAgentScope などの意味スコープは app.py 側で配線する。
#
# 旧 API（microsoft_agents_a365.observability.core.configure + Agent365ExporterOptions）は非推奨。
from microsoft.opentelemetry import use_microsoft_opentelemetry

from token_cache import get_cached_agentic_token


def configure_observability() -> None:
    """OpenTelemetry + Agent 365 exporter を初期化する。

    他モジュール（openai / LangChain 等）を import する「前」に呼ぶこと。
    そうすると対象ライブラリが自動計装され、gen_ai span が自動で出る。
    """
    use_microsoft_opentelemetry(
        enable_a365=True,
        a365_enable_observability_exporter=True,  # ★この2つ目のフラグが無いと span を送らない
        a365_token_resolver=get_cached_agentic_token,
    )
