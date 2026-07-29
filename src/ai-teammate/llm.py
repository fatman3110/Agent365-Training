# llm.py — Microsoft Foundry（Azure OpenAI v1 API・OpenAI 互換）クライアント
#
# 第1部C の Ollama 版（src/agent/llm.py）を Foundry モデルに差し替えたもの。
# Foundry の v1 エンドポイント（.../openai/v1/）を OpenAI クライアントの base_url に渡すだけ
# （api-version 不要・Azure 専用クライアント不要）。
# observability_setup.configure_observability() を先に呼べば自動計装され gen_ai span が出る。
from os import environ

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

_client: OpenAI | None = None


def get_llm() -> OpenAI:
    """Foundry（Azure OpenAI v1）クライアントを返す（初回のみ生成）。"""
    global _client
    if _client is None:
        _client = OpenAI(
            base_url=environ["AZURE_OPENAI_BASE_URL"],  # 例: https://<resource>.openai.azure.com/openai/v1/
            api_key=environ["AZURE_OPENAI_API_KEY"],
        )
    return _client


DEFAULT_SYSTEM_PROMPT = "あなたは日本語で簡潔に答えるアシスタントです。"
SYSTEM_PROMPT = environ.get("SYSTEM_PROMPT", DEFAULT_SYSTEM_PROMPT)


def chat_complete(user_text: str) -> str:
    """ユーザー入力を Foundry モデルに渡し、応答テキストを返す（ツール呼び出しなし）。"""
    response = get_llm().chat.completions.create(
        model=environ["AZURE_OPENAI_DEPLOYMENT"],  # Azure はモデル名ではなく「デプロイ名」を渡す
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ],
    )
    return response.choices[0].message.content or ""
