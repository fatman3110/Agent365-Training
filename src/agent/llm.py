# llm.py — OSS LLM（Ollama sidecar, OpenAI 互換）クライアント
#
# observability_setup.configure_observability() を先に呼んでおけば、この openai 呼び出しは
# distro により自動計装され、gen_ai span が出る（手動計装は不要）。
from os import environ
import re
import time

from openai import APIConnectionError, NotFoundError, OpenAI

_client: OpenAI | None = None


def _bounded_int(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(environ.get(name, str(default)))
    except ValueError:
        value = default
    return max(minimum, min(value, maximum))


def get_llm() -> OpenAI:
    """初回呼び出し時に Ollama sidecar への接続を確立する（最大 60 秒待つ）。"""
    global _client
    if _client is not None:
        return _client
    client = OpenAI(
        base_url=environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
        api_key="ollama",
        timeout=float(_bounded_int("OLLAMA_TIMEOUT_SECONDS", 90, 10, 180)),
        max_retries=0,
    )
    for _ in range(60):  # warmup を待つ（App Service warmup プローブ失敗を避ける）
        try:
            client.models.list()
            _client = client
            return client
        except APIConnectionError:
            time.sleep(1)
    raise RuntimeError("Ollama sidecar not ready after 60 retries")


DEFAULT_SYSTEM_PROMPT = "あなたは日本語で簡潔に答えるアシスタントです。"
SYSTEM_PROMPT = environ.get("SYSTEM_PROMPT", DEFAULT_SYSTEM_PROMPT)
MODEL = environ.get("OLLAMA_MODEL", "qwen2.5:3b-instruct-q4_K_M")
_configured_keep_alive = environ.get("OLLAMA_KEEP_ALIVE", "24h")
KEEP_ALIVE = _configured_keep_alive if re.fullmatch(r"[1-9]\d*[smh]", _configured_keep_alive) else "24h"
MAX_TOKENS = _bounded_int("OLLAMA_MAX_TOKENS", 64, 1, 256)
WARMUP_TIMEOUT_SECONDS = _bounded_int("OLLAMA_WARMUP_TIMEOUT_SECONDS", 300, 30, 540)
WARMUP_REQUEST_TIMEOUT_SECONDS = _bounded_int(
    "OLLAMA_WARMUP_REQUEST_TIMEOUT_SECONDS", 180, 30, 240
)


def warm_up_llm() -> None:
    """Wait for the configured model to exist, then load it into memory."""
    client = get_llm().with_options(
        timeout=float(WARMUP_REQUEST_TIMEOUT_SECONDS),
        max_retries=0,
    )
    deadline = time.monotonic() + WARMUP_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        try:
            client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": "ready"}],
                max_tokens=1,
                extra_body={"keep_alive": KEEP_ALIVE},
            )
            return
        except (APIConnectionError, NotFoundError):
            time.sleep(1)
    raise RuntimeError(
        f"Ollama model {MODEL!r} was not ready after {WARMUP_TIMEOUT_SECONDS} seconds"
    )


def chat_complete(user_text: str) -> str:
    """ユーザー入力を LLM に渡し、応答テキストを返す（ツール呼び出しなし）。"""
    response = get_llm().chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ],
        max_tokens=MAX_TOKENS,
        extra_body={"keep_alive": KEEP_ALIVE},
    )
    return response.choices[0].message.content or ""
