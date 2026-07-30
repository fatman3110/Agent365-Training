# 第3部 B：自作 MCP サーバー（BYO MCP）を作って A365 に登録する

第1部B で「MCP は Agent 365 Tooling Gateway 経由でないと A365 に載らない」ことを見た。ここでは **自作のリモート MCP サーバー**を実装・ホストし、**`a365 develop-mcp` で BYO 登録 → 管理者承認**することで、実際に A365 の統制下に載せる。

> ⚠️ **BYO MCP は Preview**。承認には **AI Administrator / Global Administrator** が必要。
>
> **地域について**：自作 MCP を **App Service でホストする地域（JapanEast 等）は自分のインフラ**なので制約にならない（A365 から見れば公開 HTTPS エンドポイント）。一方、**管理センターの MCP 承認機能（Tooling Gateway）がテナントの geo で提供済みか**は Preview の展開次第で、Learn は個別地域表を出さず [Feature Geography レポート](https://aka.ms/FeatureGeographicAvailabilityReport) での確認を案内している。「JapanEast だから可否」と断定できる根拠は無いので、**テナントの Feature Geography で確認**すること。
> 出典: [Manage tools for agents（BYO MCP server）](https://learn.microsoft.com/microsoft-365/admin/manage/manage-tools-for-agent#bring-your-own-byo-mcp-server)

**目次**

- [第3部 B：自作 MCP サーバー（BYO MCP）を作って A365 に登録する](#第3部-b自作-mcp-サーバーbyo-mcpを作って-a365-に登録する)
  - [1. 簡易 MCP サーバーを実装する](#1-簡易-mcp-サーバーを実装する)
  - [2. Azure にホストする（公開 HTTPS エンドポイント）](#2-azure-にホストする公開-https-エンドポイント)
  - [3. A365 に BYO 登録する](#3-a365-に-byo-登録する)
  - [4. 管理者が承認する](#4-管理者が承認する)
  - [5. クライアントから呼んで確認する](#5-クライアントから呼んで確認する)
  - [6. 呼び出しを監視する](#6-呼び出しを監視する)

## 1. 簡易 MCP サーバーを実装する

このリポジトリに完成済みの `src/mcp-server/`（`server.py` / `requirements.txt` / `Dockerfile`）を同梱している。**ツール `search_faq`（社内 FAQ を返す）を公開するだけ**の最小リモート MCP で、`x-api-key` ヘッダーで `MCP_API_KEY` を照合する。

- **リモート MCP**（HTTP 待受）・**APIKey 認証**（`x-api-key`）・**ツール名 `search_faq`** の3点が BYO 登録時の指定と対応する。
- 学びの主眼は**実装そのものではなく、A365 への BYO 登録・承認・統制**にある。実装を差し替えても以降の手順は同じ。

## 2. Azure にホストする（公開 HTTPS エンドポイント）

第1部C と同じ要領で App Service（コンテナ）にデプロイし、**公開 HTTPS の MCP エンドポイント**を得る。変数は [3部概要](./part3-0-overview.md) で定義済み。

```powershell
# --- リソース作成（いずれも冪等：既存なら再利用。第1部・3-A 未実施でも動く）---
az group create -n $RG -l $LOC
az acr create -n $MCPACR -g $RG --sku Basic --admin-enabled false
az appservice plan create -n $MCPPLAN -g $RG --is-linux --sku B1

# 同梱 Dockerfile でイメージをビルド
az acr build -r $MCPACR -t mcp-server:latest ./src/mcp-server

# Web アプリ（コンテナ）
az webapp create -n $MCPAPP -g $RG -p $MCPPLAN --deployment-container-image-name "$MCPACR.azurecr.io/mcp-server:latest"

# マネージド ID を有効化し ACR からの pull 権限（AcrPull）を付与（admin 無効 ACR 対応）
az webapp identity assign -n $MCPAPP -g $RG
$mcpPrincipal = az webapp identity show -n $MCPAPP -g $RG --query principalId -o tsv
$mcpAcrId = az acr show -n $MCPACR -g $RG --query id -o tsv
az role assignment create --assignee $mcpPrincipal --scope $mcpAcrId --role AcrPull 2>$null
$mcpAppId = az webapp show -n $MCPAPP -g $RG --query id -o tsv
az resource update --ids "$mcpAppId/config/web" --set properties.acrUseManagedIdentityCreds=true

# APIKey と待受ポートを反映
az webapp config appsettings set -n $MCPAPP -g $RG --settings MCP_API_KEY=$MCPKEY WEBSITES_PORT=8000
```

- 得られる MCP エンドポイント例：`https://$MCPAPP.azurewebsites.net/mcp`
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

← 戻る：[3-A：AI Teammate](./part3-1-ai-teammate.md)
