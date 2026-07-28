# llm.py — OSS LLM（Ollama sidecar, OpenAI 互換）クライアント
#
# observability_setup.configure_observability() を先に呼んでおけば、この openai 呼び出しは
# distro により自動計装され、gen_ai span が出る（手動計装は不要）。
from os import environ
import time

from openai import OpenAI, APIConnectionError

_client: OpenAI | None = None


def get_llm() -> OpenAI:
    """初回呼び出し時に Ollama sidecar への接続を確立する（最大 60 秒待つ）。"""
    global _client
    if _client is not None:
        return _client
    client = OpenAI(
        base_url=environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
        api_key="ollama",
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


def chat_complete(user_text: str) -> str:
    """ユーザー入力を LLM に渡し、応答テキストを返す（ツール呼び出しなし）。"""
    response = get_llm().chat.completions.create(
        model=environ.get("OLLAMA_MODEL", "qwen2.5:3b-instruct-q4_K_M"),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ],
    )
    return response.choices[0].message.content or ""
