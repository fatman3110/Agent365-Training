# 第3部 B：自作 MCP サーバー（BYO MCP）を作って A365 に登録する

第1部B で「MCP は Agent 365 Tooling Gateway 経由でないと A365 に載らない」ことを見た。ここでは **自作のリモート MCP サーバー**を実装・ホストし、**`a365 develop-mcp` で BYO 登録 → 管理者承認**することで、実際に A365 の統制下に載せる。

> ⚠️ **BYO MCP は Preview**・リージョン依存（管理センターの MCP 承認機能が未提供の地域あり）。承認には **AI Administrator / Global Administrator** が必要。
> 出典: [Manage tools for agents（BYO MCP server）](https://learn.microsoft.com/microsoft-365/admin/manage/manage-tools-for-agent#bring-your-own-byo-mcp-server)

**目次**

- [第3部 B：自作 MCP サーバー（BYO MCP）を作って A365 に登録する](#第3部-b自作-mcp-サーバーbyo-mcpを作って-a365-に登録する)
  - [0. 名前を決める](#0-名前を決める)
  - [1. 簡易 MCP サーバーを実装する](#1-簡易-mcp-サーバーを実装する)
  - [2. Azure にホストする（公開 HTTPS エンドポイント）](#2-azure-にホストする公開-https-エンドポイント)
  - [3. A365 に BYO 登録する](#3-a365-に-byo-登録する)
  - [4. 管理者が承認する](#4-管理者が承認する)
  - [5. クライアントから呼んで確認する](#5-クライアントから呼んで確認する)
  - [6. 呼び出しを監視する](#6-呼び出しを監視する)

## 0. 名前を決める

```powershell
$RG      = "rg-agent365-training"                 # 既存 RG を再利用（変更しない）
$LOC     = "japaneast"
$MCPAPP  = "app-agent365-training-mcp-xxxx"        # MCP をホストする Web アプリ（世界で一意）
$MCPPLAN = "plan-agent365-training"               # 既存プランを再利用可
$MCPNAME = "mcp-custom-xxxx"                       # BYO 登録時の server-name
$MCPKEY  = "<推測されにくい長いランダム文字列>"     # APIKey 認証用（シークレット・コミット禁止）
```

## 1. 簡易 MCP サーバーを実装する

`src/mcp-server/` に、**ツールを1〜2個公開するだけ**のリモート MCP サーバーを作る（例：社内 FAQ を返す `search_faq`）。ポイントだけ:

- **リモート MCP**（HTTP で待ち受ける）であること。BYO は remote MCP のみ対象。
- **APIKey 認証**：リクエストヘッダ（例 `x-api-key`）で `$MCPKEY` を検証する。
- ツール名（例 `search_faq`）は登録時の `--tools` と一致させる。

構成例：

```text
src/mcp-server/
├── server.py          # MCP サーバー本体（ツール search_faq を公開・APIKey 検証）
├── requirements.txt   # mcp（Python MCP SDK）等
└── Dockerfile         # App Service へデプロイ用（第1部C と同じ要領）
```

> 実装は「動くリモート MCP エンドポイント」であれば方式は自由（Python MCP SDK / FastMCP 等）。学びの主眼は**実装そのものではなく、A365 への BYO 登録・承認・統制**にある。

## 2. Azure にホストする（公開 HTTPS エンドポイント）

第1部C と同じ要領で App Service（コンテナ）にデプロイし、**公開 HTTPS の MCP エンドポイント**を得る。

```powershell
# イメージをビルドして App Service にデプロイ（第1部C 5-1 と同じ流れ・別名リソース）
az acr build -r <既存ACR名> -t mcp-server:latest ./src/mcp-server
az webapp create -n $MCPAPP -g $RG -p $MCPPLAN --deployment-container-image-name "<既存ACR名>.azurecr.io/mcp-server:latest"
# APIKey を環境変数に反映
az webapp config appsettings set -n $MCPAPP -g $RG --settings MCP_API_KEY=$MCPKEY
```

- 得られる MCP エンドポイント例：`https://<$MCPAPP>.azurewebsites.net/mcp`
- 疎通確認（MCP クライアント or curl でツール一覧が返ること）。

> ⚠️ `.sh`/`entrypoint` を含む場合は **LF 改行**にすること（第1部C で対処済みの CRLF 問題と同根。リポジトリの `.gitattributes` で `*.sh text eol=lf` 済み）。

## 3. A365 に BYO 登録する

開発者が **Agent 365 CLI** でリモート MCP を登録する（APIKey をヘッダで渡す例）：

```powershell
a365 develop-mcp register-external-mcp-server `
  --server-name  $MCPNAME `
  --server-url   "https://$MCPAPP.azurewebsites.net/mcp" `
  --publisher    "Contoso" `
  --description  "社内 FAQ を返すカスタム MCP" `
  --auth-type    APIKey `
  --api-key-location Header `
  --api-key-name x-api-key `
  --tools        "search_faq"
```

登録後、**管理者レビューに提出**される。

> 認証方式は `APIKey` / `ExternalOAuth` / `EntraOAuth` から選択。本章は簡易に `APIKey`。
> 出典: [Manage tools for agents（register-external-mcp-server）](https://learn.microsoft.com/microsoft-365/admin/manage/manage-tools-for-agent#bring-your-own-byo-mcp-server)

## 4. 管理者が承認する

AI 管理者（**AI Administrator / Global Administrator**）が M365 管理センターで承認する：

1. [M365 管理センター](https://admin.microsoft.com/) › **エージェント › ツール › 要求（Requests）** を開く
2. 登録した MCP（`mcp-custom-xxxx`）を選び、**宣言されたツール（Tools Snapshot）**を確認
3. **承認** → 続けて **Microsoft Entra の tenant-wide consent** を付与
4. 承認後、**エージェント › ツール › レジストリ** に **Available** で表示される

> 反映まで最大 30 分かかる場合がある。ブロックすると全ユーザー・全エージェントに即時適用。
> 出典: [Review and approve tool requests](https://learn.microsoft.com/microsoft-365/admin/manage/manage-tools-for-agent#review-and-approve-tool-requests)

## 5. クライアントから呼んで確認する

承認済み BYO MCP は、対応クライアントで利用できる（**Copilot Studio / VS Code / Claude Code / GitHub Copilot CLI**。Azure AI Foundry・M365 Declarative Agents は未対応）。

Copilot Studio の例：

1. [Copilot Studio](https://copilotstudio.microsoft.com/) で新規/既存エージェントを開く
2. **Tools › MCP Server** で、レジストリから `mcp-custom-xxxx` を選択
3. `search_faq` を呼ぶプロンプトでテスト（初回は APIKey 接続の一回設定を求められる場合あり）

> 出典: [Use an approved MCP server](https://learn.microsoft.com/microsoft-365/admin/manage/manage-tools-for-agent#use-an-approved-mcp-server)

## 6. 呼び出しを監視する

セキュリティチームは **Microsoft Defender 高度なハンティング**で MCP 呼び出し（どのエージェントがいつ呼んだか）を追跡できる。Gateway 経由になったことで、**統制（block）と observability** が効くようになった点が第1部B との違い。

---

← 戻る：[3-A：AI Teammate](./part3-1-ai-teammate.md) ｜ 次：**[3-C：統合](./part3-3-integrate.md)**
