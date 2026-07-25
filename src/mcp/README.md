# src/mcp — 自作 MCP（道具）

エージェントが呼ぶ**独自 MCP サーバー**のスターターコード。学習用のダミーツールを 2 つだけ持つ。Azure Functions の MCP ツールトリガー（`mcpToolTrigger`）で公開し、Agent 365 に BYO MCP として登録する。

> スターター（Preview 前提）。バインド仕様・拡張バンドルは着手時に現行の Azure Functions / SDK で確認すること。

## この MCP が持つ道具（機能）

| ツール名 | 機能 | 入力 |
|---|---|---|
| `echo` | 入力された文字列をそのまま返す | `text`（string） |
| `now` | 現在の UTC 時刻（ISO 8601）を返す | なし |

いずれも副作用のない安全なダミーで、エージェントが「道具を呼ぶ」流れと、その実行が Observe / Single Agent Map の Tool ノードに出ることを体験するためのものである。

## 各ファイルの意味

| ファイル | 役割 |
|---|---|
| `function_app.py` | 道具の実装。`echo` / `now` を `mcpToolTrigger` バインドで定義する |
| `host.json` | Azure Functions ホスト設定。MCP 拡張を含む Experimental extension bundle を指定する |
| `requirements.txt` | この MCP が必要とする Python パッケージ一覧 |

## エンドポイントとデプロイ

- MCP エンドポイント：`https://<関数アプリ>.azurewebsites.net/runtime/webhooks/mcp`
- デプロイ：`func azure functionapp publish <FUNCTION_APP_NAME>`

## 関連

- 作成・登録手順：[docs/part1b-custom-agent.md](../../docs/part1b-custom-agent.md)
- エージェント本体：[src/agent](../agent)
