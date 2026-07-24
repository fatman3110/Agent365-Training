# function_app.py — BYO MCP サーバー（学習用ダミーツール: echo / now）
#
# ★ スターター（Preview 前提）。Azure Functions の MCP tool trigger（mcpToolTrigger）を使用。
# バインド仕様は現行の Azure Functions / SDK で要確認。
# デプロイ: func azure functionapp publish <FUNCTION_APP_NAME>
# MCP エンドポイント: https://<app>.azurewebsites.net/runtime/webhooks/mcp
import datetime
import json

import azure.functions as func

app = func.FunctionApp()

_ECHO_PROPS = json.dumps(
    [
        {
            "propertyName": "text",
            "propertyType": "string",
            "description": "echo する文字列",
        }
    ]
)


@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="echo",
    description="入力をそのまま返す",
    toolProperties=_ECHO_PROPS,
)
def echo(context) -> str:
    args = json.loads(context).get("arguments", {})
    return args.get("text", "")


@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="now",
    description="現在の UTC 時刻を返す",
    toolProperties="[]",
)
def now(context) -> str:
    return datetime.datetime.utcnow().isoformat() + "Z"
