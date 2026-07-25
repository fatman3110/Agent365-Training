# src/agent — エージェント本体（頭脳）

Agent 365 に登録する**独自エージェント本体**のスターターコード。自前ホストの OSS LLM（Qwen を Ollama サイドカー経由・OpenAI 互換 API で呼ぶ）で応答する、**非 AI Teammate** のエージェントである。App Service にコンテナとしてデプロイする。

> スターター（Preview 前提）。パッケージ名・API は着手時に現行 SDK / Microsoft Learn で確認すること。ホスティング層（`start_server.py`）は Skills（`make-a365-agent`）が生成する想定で、このフォルダには含まれない。

## このエージェントができること

- **会話応答**：Teams / API から届いたメッセージを OSS LLM（Qwen）に渡し、日本語で簡潔に返す。
- **OBO（委任）で動く**：話しかけたユーザーの代理としてトークンを取得し、監査に「誰の代理か」を残す。
- **自作 MCP（道具）の利用**：別ディレクトリ [`../mcp`](../mcp) の `echo` / `now` などの道具を呼べる（承認後）。
- **可観測性**：実行トレースを Agent 365 Observability（OBO エンドポイント）へ送り、Observe / Single Agent Map に反映させる。

## 各ファイルの意味

| ファイル | 役割 |
|---|---|
| `app.py` | エージェント本体。`AgentApplication` を組み立て、メッセージ受信（`message` アクティビティ）で `llm.chat_complete()` を呼んで返信する。`/help` コマンドも持つ |
| `llm.py` | OSS LLM クライアント。Ollama サイドカー（OpenAI 互換）へ接続し、`SYSTEM_PROMPT` とモデル名（環境変数）で応答を生成する。起動時ブロックを避けるため遅延初期化＋ウォームアップ待ちを行う |
| `obo.py` | OBO（On-Behalf-Of）トークン交換。受け取ったユーザートークンを、観測スコープのトークンに MSAL で交換する |
| `observability_setup.py` | Agent 365 Observability の exporter 配線。OBO 用エンドポイント（`use_s2s_endpoint=False`）へ送るよう初期化し、ターンごとのユーザートークンを resolver に供給する |
| `requirements.txt` | このエージェントが必要とする Python パッケージ一覧 |
| `Dockerfile` | App Service にデプロイするコンテナ定義。`start_server.py`（Skills 生成）を起点に起動する |

## 関連

- 作成・デプロイ手順：[docs/part1b-custom-agent.md](../../docs/part1b-custom-agent.md)
- 自作 MCP（道具）：[src/mcp](../mcp)
