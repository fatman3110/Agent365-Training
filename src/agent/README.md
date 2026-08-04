# src/agent — エージェント本体（頭脳）

Agent 365 に登録する**独自エージェント本体**のスターターコード。自前ホストの OSS LLM（Qwen を Ollama サイドカー経由・OpenAI 互換 API で呼ぶ）で応答する、**非 AI Teammate** のエージェントである。App Service にコンテナとしてデプロイする。

> スターター（Preview 前提）。パッケージ名・API は着手時に現行 SDK / Microsoft Learn で確認すること。ホスティング層（`start_server.py`）はこのフォルダに同梱済み（`make-a365-agent` Skill はホスティング層を生成しないため、手書きで用意している）。

## このエージェントができること

- **会話応答**：Teams / API から届いたメッセージを OSS LLM（Qwen）に渡し、日本語で簡潔に返す。
- **A2A 応答**：Teams と同じエージェントロジックを A2A v1（JSON-RPC / HTTP+JSON）でも公開する。
- **S2S（サービスプリンシパル）で動く**：トークンの取得は `start_server.py` がバックグラウンドで行う（`observability/token_service.py` の 3-hop FMI チェーン）。メッセージハンドラ（`app.py`）は per-turn のトークン交換に一切関与しない。
- **可観測性**：`instrument-observability` Skill により配線済み（S2S）。`InvokeAgentScope` でターンを計装し、`observability/token_cache.py` へバックグラウンド更新されたトークンを exporter が読み出して Agent 365 Observability（S2S エンドポイント）へ送信、Observe / Single Agent Map に反映される。LLM 呼び出し（`openai` SDK）は distro が自動計装するため `InferenceScope` は手動配線していない。

## 各ファイルの意味

| ファイル | 役割 |
|---|---|
| `start_server.py` | FastAPI ホスティング層。`MsalConnectionManager` + `CloudAdapter` による Teams `/api/messages` と A2A endpointを同じポートで公開する。S2S 観測トークンのバックグラウンド取得もここで起動する |
| `a2a_server.py` | A2A v1 Agent Card、JSON-RPC、HTTP+JSONルートとExecutor。`X-A2A-API-Key`を要求する |
| `agent_service.py` | Teams / A2A 共通の1ターン実行。`InvokeAgentScope`でチャネル名を含めて計装し、`llm.chat_complete()`を呼ぶ |
| `app.py` | Teams向け`AgentApplication`本体。共通ターン実行を呼び出す。`/help`コマンドも持つ |
| `llm.py` | OSS LLM クライアント。Ollama サイドカー（OpenAI 互換）へ接続し、`SYSTEM_PROMPT` とモデル名（環境変数）で応答を生成する。起動時ブロックを避けるため遅延初期化＋ウォームアップ待ちを行う。distro 初期化後は自動計装される |
| `observability_setup.py` | Agent 365 Observability の初期化。`use_microsoft_opentelemetry(...)` で exporter を有効化し（S2S エンドポイント）、`a365_token_resolver` を `observability/token_cache.get_cached_token` に配線する |
| `observability/token_service.py` | S2S 観測トークンのバックグラウンド取得（3-hop FMI チェーン）。起動時に1回取得＋以後50分毎ループ |
| `observability/token_cache.py` | S2S トークンキャッシュ。`token_service.py` が書き込み、`observability_setup.py` の exporter 解決器が読み出す |
| `requirements.txt` | このエージェントが必要とする Python パッケージ一覧（`microsoft-opentelemetry` ・ `microsoft-agents-hosting-*` ・ `microsoft-agents-authentication-msal` ・ `msal` ・ `httpx` 等） |
| `Dockerfile` | App Service にデプロイするコンテナ定義。`start_server.py`（このフォルダ同梱）を起点に起動する |

## A2A endpoint

デプロイ後は次のendpointを公開する。

| 用途 | URL |
|---|---|
| A2A JSON-RPC | `POST https://<host>/a2a` |
| A2A HTTP+JSON | `POST https://<host>/a2a/message:send` |
| Agent Card（endpoint） | `GET https://<host>/a2a` |
| Agent Card（endpoint配下） | `GET https://<host>/a2a/.well-known/agent.json` |
| Agent Card（endpoint配下の互換パス） | `GET https://<host>/a2a/.well-known/agent-card.json` |
| Agent Card | `GET https://<host>/.well-known/agent.json` |
| Agent Card（互換パス） | `GET https://<host>/.well-known/agent-card.json` |

App Serviceには次の環境変数が必要。

| 変数 | 用途 |
|---|---|
| `A2A_API_KEY` | A2A要求の`X-A2A-API-Key`ヘッダーと比較する秘密値 |
| `A2A_PUBLIC_BASE_URL` | Agent Cardに掲載する公開HTTPS URL |
| `OLLAMA_KEEP_ALIVE` | 推論後もモデルをメモリに保持する期間。既定値は`24h` |
| `OLLAMA_MAX_TOKENS` | 1応答の最大生成トークン数。Copilotのタイムアウトを避ける既定値は`64` |
| `OLLAMA_TIMEOUT_SECONDS` | Ollama API呼び出しのタイムアウト秒数。既定値は`90`、許容範囲は`10`～`180` |
| `OLLAMA_WARMUP_TIMEOUT_SECONDS` | 起動時にモデルpullと初回ロードを待つ上限秒数。既定値は`300` |

FastAPIの起動処理は、Ollamaサイドカーのモデルpullと初回ロードが完了するまで待機する。
App Serviceでは **Always On** と十分なコンテナー起動猶予時間も有効化し、Copilotの初回呼び出しが
モデル準備処理と競合しないようにする。

Copilot Studioでは **外部エージェントに接続 > Agent2Agent** を選択し、endpointに
`https://<host>/a2a`、認証に **API key**、ヘッダー名に`X-A2A-API-Key`を指定する。
キー値はApp Serviceの環境変数から安全な経路で取得し、ソースやドキュメントには保存しない。

## 関連

- 作成・デプロイ手順：[docs/part1c-custom-agent.md](../../docs/part1c-custom-agent.md)
