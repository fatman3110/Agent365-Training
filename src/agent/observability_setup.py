# observability_setup.py — Agent 365 Observability 初期化（現行 microsoft-opentelemetry distro）
#
# ★ 参考実装。ここでは「配線の入口」だけを示す。ターン毎のトークン交換や
#   InvokeAgentScope / InferenceScope などの詳細計装は、instrument-observability Skill が
#   現行 SDK に沿った検証済みの形で生成する（「このエージェントに Agent 365 の観測を OBO で追加して」）。
#
# 旧 API（microsoft_agents_a365.observability.core.configure + Agent365ExporterOptions）は非推奨。
from microsoft.opentelemetry import use_microsoft_opentelemetry
from microsoft.opentelemetry.a365.hosting.token_cache_helpers import AgenticTokenCache

# 観測トークンの解決器（OBO / agentic-user）。exporter がエクスポート毎に呼ぶ。
_token_cache = AgenticTokenCache()


def configure_observability() -> None:
    """OpenTelemetry + Agent 365 exporter を初期化する。

    他モジュール（openai / LangChain 等）を import する「前」に呼ぶこと。
    そうすると対象ライブラリが自動計装され、gen_ai span が自動で出る。
    """
    use_microsoft_opentelemetry(
        enable_a365=True,
        a365_enable_observability_exporter=True,  # ★この2つ目のフラグが無いと span を送らない
        a365_token_resolver=_token_cache.get_observability_token,
    )
