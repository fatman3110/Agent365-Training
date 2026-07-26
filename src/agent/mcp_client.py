# mcp_client.py — 道具（MCP）を呼び出す薄いクライアント
#
# ★ スターター（Preview 前提）。§4 でデプロイした Function App の MCP エンドポイント
# （/runtime/webhooks/mcp、Streamable HTTP transport）に接続し、ツール一覧取得と呼び出しを行う。
# 参考: https://learn.microsoft.com/azure/azure-functions/functions-bindings-mcp#connect-to-your-mcp-server
from __future__ import annotations

import os
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# 例: https://<func-app-name>.azurewebsites.net/runtime/webhooks/mcp
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "")


async def list_mcp_tools() -> list[dict[str, Any]]:
    """MCP サーバーが提供するツール一覧を、OpenAI tool calling 用の形式に変換して返す。

    MCP_SERVER_URL が未設定、または接続に失敗した場合は空リストを返す
    （ツール無しでも通常のチャット応答は継続できるようにするため）。
    """
    if not MCP_SERVER_URL:
        return []
    try:
        async with streamablehttp_client(MCP_SERVER_URL) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.list_tools()
                return [
                    {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description or "",
                            "parameters": tool.inputSchema or {"type": "object", "properties": {}},
                        },
                    }
                    for tool in result.tools
                ]
    except Exception as exc:  # noqa: BLE001 — ツール一覧取得の失敗で会話全体を止めない
        print(f"[mcp_client] list_tools failed: {exc}")
        return []


async def call_mcp_tool(name: str, arguments: dict[str, Any]) -> str:
    """MCP ツールを 1 回呼び出し、テキスト結果を返す。"""
    if not MCP_SERVER_URL:
        raise RuntimeError("MCP_SERVER_URL is not configured")
    async with streamablehttp_client(MCP_SERVER_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(name, arguments)
            parts = [c.text for c in result.content if getattr(c, "type", "") == "text"]
            return "\n".join(parts) if parts else str(result.content)
