# src/agent — エージェント本体（頭脳）

Agent 365 に登録する**独自エージェント本体**のスターターコード。自前ホストの OSS LLM（Qwen を Ollama サイドカー経由・OpenAI 互換 API で呼ぶ）で応答する、**非 AI Teammate** のエージェントである。App Service にコンテナとしてデプロイする。

> スターター（Preview 前提）。パッケージ名・API は着手時に現行 SDK / Microsoft Learn で確認すること。ホスティング層（`start_server.py`）はこのフォルダに同梱済み（`make-a365-agent` Skill はホスティング層を生成しないため、手書きで用意している）。

## このエージェントができること

- **会話応答**：Teams / API から届いたメッセージを OSS LLM（Qwen）に渡し、日本語で簡潔に返す。
- **S2S（サービスプリンシパル）で動く**：トークンの取得は `start_server.py` がバックグラウンドで行う（`observability/token_service.py` の 3-hop FMI チェーン）。メッセージハンドラ（`app.py`）は per-turn のトークン交換に一切関与しない。
- **可観測性**：`instrument-observability` Skill により配線済み（S2S）。`InvokeAgentScope` でターンを計装し、`observability/token_cache.py` へバックグラウンド更新されたトークンを exporter が読み出して Agent 365 Observability（S2S エンドポイント）へ送信、Observe / Single Agent Map に反映される。LLM 呼び出し（`openai` SDK）は distro が自動計装するため `InferenceScope` は手動配線していない。

## 各ファイルの意味

| ファイル | 役割 |
|---|---|
| `start_server.py` | ホスティング層（受付・起動）。`load_agent_configuration()` で `.env` を読み込み、`build_adapter(config)` が `MsalConnectionManager` + `CloudAdapter` を組み立てて `/api/messages` / `/api/health` を待ち受ける aiohttp サーバーを起動する。S2S 観測トークンのバックグラウンド取得（`observability/token_service.py`）もここで起動する |
| `app.py` | エージェント本体。`AgentApplication` を組み立て、`InvokeAgentScope` でターンを計装しつつ `llm.chat_complete()` を呼んで返信する。per-turn のトークン交換には一切関与しない。`/help` コマンドも持つ |
| `llm.py` | OSS LLM クライアント。Ollama サイドカー（OpenAI 互換）へ接続し、`SYSTEM_PROMPT` とモデル名（環境変数）で応答を生成する。起動時ブロックを避けるため遅延初期化＋ウォームアップ待ちを行う。distro 初期化後は自動計装される |
| `observability_setup.py` | Agent 365 Observability の初期化。`use_microsoft_opentelemetry(...)` で exporter を有効化し（S2S エンドポイント）、`a365_token_resolver` を `observability/token_cache.get_cached_token` に配線する |
| `observability/token_service.py` | S2S 観測トークンのバックグラウンド取得（3-hop FMI チェーン）。起動時に1回取得＋以後50分毎ループ |
| `observability/token_cache.py` | S2S トークンキャッシュ。`token_service.py` が書き込み、`observability_setup.py` の exporter 解決器が読み出す |
| `requirements.txt` | このエージェントが必要とする Python パッケージ一覧（`microsoft-opentelemetry` ・ `microsoft-agents-hosting-*` ・ `microsoft-agents-authentication-msal` ・ `msal` ・ `httpx` 等） |
| `Dockerfile` | App Service にデプロイするコンテナ定義。`start_server.py`（このフォルダ同梱）を起点に起動する |

## 関連

- 作成・デプロイ手順：[docs/part1c-custom-agent.md](../../docs/part1c-custom-agent.md)
