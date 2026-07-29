# llm.py — Microsoft Foundry（Azure OpenAI 互換）クライアント
#
# 第1部C の Ollama 版（src/agent/llm.py）を Foundry モデルに差し替えたもの。
# observability_setup.configure_observability() を先に呼べば、この openai 呼び出しは
# distro により自動計装され、gen_ai span が出る（手動計装は不要）。
from os import environ

from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

_client: AzureOpenAI | None = None


def get_llm() -> AzureOpenAI:
    """Foundry（Azure OpenAI）クライアントを返す（初回のみ生成）。"""
    global _client
    if _client is None:
        _client = AzureOpenAI(
            azure_endpoint=environ["AZURE_OPENAI_ENDPOINT"],
            api_key=environ["AZURE_OPENAI_API_KEY"],
            api_version=environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21"),
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
