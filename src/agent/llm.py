# llm.py — OSS LLM（Ollama sidecar, OpenAI 互換）クライアント
#
# ★ スターター（Preview 前提）。
# observability_setup.configure_observability() を先に呼んでおけば、この openai 呼び出しは
# microsoft-opentelemetry ディストロにより自動計装され、gen_ai span が出る（手動計装は不要）。
# 起動時ブロック回避のため、LLM 接続は遅延初期化（初回メッセージ時）にする。
from os import environ
import json
import time

from openai import OpenAI, APIConnectionError

from mcp_client import call_mcp_tool, list_mcp_tools

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


async def chat_complete_with_tools(user_text: str) -> str:
    """ユーザー入力を LLM に渡し、必要に応じて MCP の道具（echo/now）を
    OpenAI tool calling 経由で呼び出しながら応答を作る。

    学習用の簡易実装：ツール呼び出しは最大 1 往復（モデルが複数回連続で呼ぶケースは未対応）。
    MCP サーバー未設定・接続失敗時はツール無しの通常の応答にフォールバックする。
    """
    model = environ.get("OLLAMA_MODEL", "qwen2.5:3b-instruct-q4_K_M")
    client = get_llm()
    tools = await list_mcp_tools()

    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_text},
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools or None,
    )
    message = response.choices[0].message

    if message.tool_calls:
        messages.append(message.model_dump(exclude_none=True))
        for tool_call in message.tool_calls:
            args = json.loads(tool_call.function.arguments or "{}")
            try:
                result_text = await call_mcp_tool(tool_call.function.name, args)
            except Exception as exc:  # noqa: BLE001 — ツール呼び出し失敗で会話を止めない
                result_text = f"(tool error: {exc})"
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result_text,
                }
            )
        response = client.chat.completions.create(model=model, messages=messages)
        message = response.choices[0].message

    return message.content or ""
