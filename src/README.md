# src/ — スターターコード（① あなたが用意するコード）

このフォルダは README 本編「構成ファイル」の **① あなたが用意するコード**（Preview スターター）です。
Agent 365 の **② ホスティング層・manifest（Skills 生成）** と **③ ID・`.env`（`a365 setup all` 生成／シークレット）** は
各テナント・各マシンで生成されるため、ここには含まれません。

## すぐ使えるもの / 生成が要るもの

| ファイル | 状態 | 備考 |
|---|---|---|
| `function_app.py` | **単体で動く**（Azure Functions） | `func azure functionapp publish <FUNCTION_APP_NAME>` でデプロイ。MCP: `/runtime/webhooks/mcp` |
| `llm.py` | すぐ使える | Ollama sidecar（OpenAI 互換）へ接続 |
| `obo.py` | すぐ使える | MSAL の OBO 交換。`.env` の値が必要 |
| `observability_setup.py` | 要 SDK | `microsoft_agents_a365` が必要（Skills / setup で導入） |
| `app.py` | 要スキャフォールド | `start_server.py`（Skills 生成）に依存。`a365 setup all` 後に差し込む |
| `requirements.txt` | 参考 | 実パッケージ名は生成物に合わせる |
| `.env.example` | テンプレ | 実値は `a365 setup all` がスタンプ（`.env` はコミット禁止） |

## 使い方（概略・README 本編 §1〜§6 参照）

1. `a365 setup all`（非 AI Teammate / OBO）で **ID・`.env`・ホスティング層** を生成
2. 生成された骨格に本フォルダの `app.py` / `llm.py` / `obo.py` / `observability_setup.py` を配置・配線
3. `function_app.py` を Azure Functions にデプロイ（BYO MCP）
4. App Service にデプロイ → `a365 publish` → 管理センターで承認

> ⚠️ **Preview 前提**。パッケージ名・SDK API・Functions の MCP バインドは変わり得るため、
> 着手時に現行 SDK / Microsoft Learn で必ず確認すること。
