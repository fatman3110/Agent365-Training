# server.py — 最小のリモート MCP サーバー（ツール search_faq を公開）
#
# BYO MCP の学習用リファレンス実装。APIKey 認証としてリクエストヘッダ
# `x-api-key` を環境変数 MCP_API_KEY と定数時間比較で照合する。
# ⚠️ MCP Python SDK のバージョンにより streamable_http_app() の API は変わり得る。
#    実行前に `pip show mcp` でバージョンを確認すること。
import hmac
import os

from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

mcp = FastMCP("faq-mcp")

# デモ用の社内 FAQ（本番は DB や検索サービスに置き換える）
_FAQ = {
    "経費精算の締め日": "経費精算は毎月末の営業日までに申請してください。",
    "有給の申請方法": "勤怠システムから取得日の 3 営業日前までに申請します。",
    "VPN 接続": "社内ポータルの「リモートアクセス」から手順書を参照してください。",
}


@mcp.tool()
def search_faq(query: str) -> str:
    """社内 FAQ を検索して回答文字列を返す。"""
    for key, answer in _FAQ.items():
        if query in key or key in query:
            return answer
    return "該当する FAQ が見つかりませんでした。"


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """x-api-key ヘッダを MCP_API_KEY と照合する。未設定時は素通し（ローカル開発用）。"""

    async def dispatch(self, request, call_next):
        expected = os.environ.get("MCP_API_KEY")
        if expected:
            provided = request.headers.get("x-api-key", "")
            if not hmac.compare_digest(provided, expected):
                return JSONResponse({"error": "unauthorized"}, status_code=401)
        return await call_next(request)


app = mcp.streamable_http_app()
app.add_middleware(ApiKeyMiddleware)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
