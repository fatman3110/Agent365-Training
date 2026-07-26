# 第1部 B：独自エージェント＋独自 MCP を作る（開発者）

自前ホストの LLM（Qwen）で動く**独自エージェント**と、自作の道具（**独自 MCP**）をコードから作って Azure にデプロイし、Agent 365 に登録申請するまで。完了すると、エージェントが Agent 365 に登録され、Azure（クラウド）で動く状態になる。

> 💡 ノーコードで手早く作りたいなら **[第1部 A：Copilot Studio で作る](./part1a-copilot-studio.md)** もある。本ファイル（B）は「フルコードで自前ホスト＋独自 MCP」を学ぶ上級ルート。
>
> ⚠️ Microsoft Agent 365 は Preview を多く含む。コマンド・API は変わり得るので、Microsoft Learn で最新情報を確認すること。

**目次**

- [第1部 B：独自エージェント＋独自 MCP を作る（開発者）](#第1部-b独自エージェント独自-mcp-を作る開発者)
  - [構成ファイル（参考）](#構成ファイル参考)
  - [0. 最初に「名前」を決める（1 回だけ）](#0-最初に名前を決める1-回だけ)
  - [1. ツールを用意して Azure にログインする](#1-ツールを用意して-azure-にログインする)
  - [2. Agent 365 Skills を導入する](#2-agent-365-skills-を導入する)
  - [3. エージェントの「土台」を作る（Blueprint / Agent ID）](#3-エージェントの土台を作るblueprint--agent-id)
  - [4. 道具（MCP）を作ってクラウドに置く](#4-道具mcpを作ってクラウドに置く)
    - [4-1. Azure に空の Function App（入れ物）を作る](#4-1-azure-に空の-function-app入れ物を作る)
    - [4-2. 作った入れ物に MCP コードをアップロードする](#4-2-作った入れ物に-mcp-コードをアップロードする)
  - [5. エージェント本体を実装する](#5-エージェント本体を実装する)
  - [6. Azure にデプロイして「登録」する](#6-azure-にデプロイして登録する)
    - [6-1. コンテナレジストリと App Service を作る](#6-1-コンテナレジストリと-app-service-を作る)
    - [6-2. Ollama（LLM）を sidecar で追加](#6-2-ollamallmを-sidecar-で追加)
    - [6-3. エージェントの endpoint を Agent 365 に登録する](#6-3-エージェントの-endpoint-を-agent-365-に登録する)

完了後は **[第2部 B：承認と観測データ作成](./part2-1b-custom.md)** で承認・Teams 接続・観測データ作成を行い、その後 Observe / Govern / Secure に進む。

## 構成ファイル（参考）

このルートで扱うファイルは **(1) 自作コード**、**(2) `a365 setup all` が自動生成するもの**、**(3) シークレット** の 3 種に分かれる。本リポジトリの [`../src/`](../src) は (1) に相当する。(2)・(3) は各自の環境で生成されるためリポジトリには含まれない。

> 💡 (1)＝エージェントの“頭脳”（何を答え・どの道具を呼ぶか）と“受付・起動”（外部からのメッセージを受け取り頭脳に渡す aiohttp サーバー）。非 AI Teammate 向けにこのホスティング層を自動生成する Skill は無いため、`start_server.py` も (1) として本リポジトリに同梱している。

```text
Agent365-Training/
├── src/                             # (1) 本リポジトリに同梱（あなたが書くコード）
│   ├── agent/                       #   エージェント本体（App Service にデプロイ）
│   │   ├── app.py                   #     頭脳：発言を受け取り AI に渡して返答する
│   │   ├── llm.py                   #     AI（自前ホストの Qwen）に質問して答えをもらう
│   │   ├── start_server.py          #     受付と起動：aiohttp サーバーで外部からのメッセージを app.py へ橋渡し
│   │   ├── observability_setup.py   #     観測の初期化の入口（現行 distro use_microsoft_opentelemetry）
│   │   ├── requirements.txt         #     必要な Python ライブラリ
│   │   └── Dockerfile               #     コンテナ化の定義
│   └── mcp/                         #   自作の道具（MCP・Azure Functions にデプロイ）
│       ├── function_app.py          #     道具の中身（echo / now）
│       ├── host.json                #     Functions 設定（MCP 拡張）
│       ├── local.settings.json      #     Functions のローカル設定（言語=python の判定に必須）
│       └── requirements.txt         #     必要な Python ライブラリ
├── appPackage/manifest.json         # (2) `a365 setup all --m365` が自動生成：エージェントを登録するための情報（名前など）
├── a365.config.json                 # (2) `a365 setup all` に渡す設定ファイル
├── .env                             # (3) 秘密情報：接続キー等。`a365 setup all` が自動で書き込む（共有・コミット禁止）
└── a365.generated.config.json       # (3) 秘密情報：`a365 setup all` が作る ID・同意状況（共有・コミット禁止）
```

## 0. 最初に「名前」を決める（1 回だけ）

以降のコマンドはこの変数をそのまま使う。**`xxxx` を自分用のユニークな文字列に変えて**、ターミナルに貼り付ける（PowerShell）。

```powershell
$RG    = "rg-agent365-training"                # リソースグループ（トレーニング一式をまとめる箱）
$LOC   = "japaneast"                           # リージョン
$ACR   = "acragent365trainingxxxx"             # コンテナレジストリ：Qwen エージェントのコンテナ格納（世界で一意・小文字英数のみ）
$PLAN  = "plan-agent365-training"              # App Service プラン（エージェント本体をホストする土台）
$APP   = "app-agent365-training-agent-xxxx"    # エージェント本体（頭脳）の Web アプリ（世界で一意）
$FUNC  = "func-agent365-training-mcp-xxxx"     # 自作 MCP（道具 echo / now）用の Functions（世界で一意）
$STG   = "sta365trainingmcpxxxx"               # 上記 Functions 用ストレージ（世界で一意・小文字英数のみ・24 文字以内。短縮: a365）
$MCP   = "ext_a365trainingmcp"                 # 自作 MCP サーバー名
```

## 1. ツールを用意して Azure にログインする

まず教材リポジトリ（`src/` の雛形コードを含む）を取得し、その中で作業する。

```powershell
# 教材（本リポジトリ）を clone して作業ディレクトリに入る
git clone https://github.com/fatman3110/Agent365-Training.git
cd Agent365-Training
cd src/agent
```

次に必要なツールを確認する（無ければ各コメントのコマンドで導入）。

```powershell
# バージョンが返れば OK（無ければ各コメントのコマンドで導入）
node --version   # 無ければ: winget install OpenJS.NodeJS.LTS
az   version     # 無ければ: winget install Microsoft.AzureCLI
func --version   # 無ければ: npm i -g azure-functions-core-tools@4
a365 --version   # 無ければ: dotnet tool install -g Microsoft.Agents.A365.DevTools.Cli

# Azure にサインイン
az login
```

## 2. Agent 365 Skills を導入する

これを導入すると、Github Copilot / Claude Code に自然言語で指示したときに、Blueprint 作成（`a365-setup`）や観測の詳細配線（`instrument-observability`）を Skill が代わりに実行してくれる。

```powershell
git clone https://github.com/microsoft/agent365-skills.git
node .\agent365-skills\scripts\install.js   # VS Code の chat.agentSkillsLocations に登録される（Reload Window で反映）
```

## 3. エージェントの「土台」を作る（Blueprint / Agent ID）

> **作業ディレクトリ（重要）**：`a365-setup` / `a365 setup all` は「実行したフォルダ」を**エージェントのプロジェクト**とみなし、そこにリソースを生成する。本教材ではエージェント本体のコードがある **`src/agent`** をプロジェクトとして扱う。

**ターミナルのコマンドではなく、AI チャットに次の指示を送る**と、先ほど導入した Skill が起動し、必要なコマンドを AI が代わりに実行してくれる。

```text
a365-setup を実行して。作業ディレクトリは src/agent。UPN を持たない Agent を OBO（委任）認可で作りたい。
```

> **この指示の意味**
> - **a365-setup を実行して** … Skill（`a365-setup`）を起動する合図
> - **UPN を持たない Agent** … 人間のようなメールアドレス／ログイン名（UPN）を**持たない**エージェント = **非 AI Teammate**
> - **OBO（委任 / on-behalf-of）認可** … エージェントが「今ログインしているユーザーの代理」として権限を借りて動く方式。

Skill が内部で `a365 setup all`を実行し、以下を**自動で**行う。

```text
要件チェック ─▶ Blueprint 作成 ─▶ 資格情報 ─▶ 委任権限の継承 ─▶ Agent Identity 作成(UPN無し) ─▶ 登録 ─▶ ローカルの .env へ接続情報を書き込み
```

途中で 、複数回、画面の指示に従って指示や認証を行う：
1. `[y/N]:` の選択  → `y`
2. ブラウザが開く → サインインと権限の承認

- **成功の判定**：ローカルに作成された `a365.generated.config.json` の **`agentBlueprintId` に ID が入っていること** 

## 4. 道具（MCP）を作ってクラウドに置く

エージェントが使う「道具」を、Azure Functions として建てる。コードは [../src/mcp/](../src/mcp)（`echo` / `now` の 2 ツール）。

### 4-1. Azure に空の Function App（入れ物）を作る

Functions を動かすための Azure リソース（リソースグループ・ストレージ・空の Function App）だけを作る。

```powershell
az group create -n $RG -l $LOC
az storage account create -n $STG -g $RG -l $LOC --sku Standard_LRS `
  --allow-blob-public-access false --min-tls-version TLS1_2
az functionapp create -n $FUNC -g $RG -s $STG `
  --consumption-plan-location $LOC `
  --runtime python --runtime-version 3.11 --functions-version 4 --os-type Linux
```

### 4-2. 作った入れ物に MCP コードをアップロードする

4-1 で作った空の Function App（`$FUNC`）に、[../src/mcp/](../src/mcp) のコードを送り込む。

```powershell
cd ..\mcp        # src/agent から src/mcp へ
func azure functionapp publish $FUNC
cd ..\agent      # src/agent に戻る
```


> この節では**道具を作って Azure に置くだけ**。**Agent 365 への登録は 6 節、承認は [第2部 B](./part2-1b-custom.md)** でまとめて行う。

## 5. エージェント本体を実装する

1. `.env` に ローカル LLM 関連の設定とモニタリング関連の設定、及び MCP エンドポイントを追記。
   ```powershell
   Add-Content ".env" @"
   OLLAMA_BASE_URL=http://localhost:11434/v1
   OLLAMA_MODEL=qwen2.5:3b-instruct-q4_K_M
   ENABLE_A365_OBSERVABILITY=true
   ENABLE_A365_OBSERVABILITY_EXPORTER=true
   MCP_SERVER_URL=https://$FUNC.azurewebsites.net/runtime/webhooks/mcp
   "@
   ```
   > `.env` を直接編集する場合は、`MCP_SERVER_URL` の `<FUNC>` を **`$FUNC` の実際の値**（例: `echo $FUNC` で確認できる文字列）に置き換えること。この値は §6-1 の `az webapp config appsettings set` でそのまま App Service に反映されるため、ここで直し忘れると本番でも道具に繋がらない。
2. 観測の詳細配線は **Skill に任せる**。下の指示を AI チャットに送ると、Skill（`instrument-observability`）が現行ディストロ `use_microsoft_opentelemetry(...)` とスコープ（InvokeAgentScope 等）の配線コードを生成する：
   ```text
   このエージェントに Agent 365 の観測を OBO（委任）で追加して。
   ```

## 6. Azure にデプロイして「登録」する

エージェント本体（(1)＋(2)）をコンテナにして App Service へ。LLM（Qwen）は隣に置く 

```mermaid
flowchart LR
    Teams["Microsoft Teams / Copilot"] -->|"messaging endpoint"| Agent

    subgraph AppSvc["App Service（Linux, マルチコンテナ）"]
        direction LR
        Agent["メインコンテナ\nagent（Python）\napp.py / llm.py"]
        Ollama["サイドカー コンテナ\nollama/ollama\nqwen2.5:3b-instruct"]
        Agent -->|"http://localhost:11434\n（OpenAI 互換 API）"| Ollama
    end

    Agent -->|"MCP over HTTPS"| MCP["Azure Functions\n（echo / now ツール）"]
    Agent -->|"観測値 export"| MAC["Agent 365 Observability"]
```

> **なぜ sidecar 構成にするか**
> - **Ollama** LLM をローカル環境やコンテナ内でそのまま動かせるランタイム
> - **攻撃対象面を増やさない** sidecar 方式にすることで Ollama を外部に公開する必要がなく、認証やネットワーク越しの追加ホップも不要

### 6-1. コンテナレジストリと App Service を作る

```powershell
# コンテナレジストリ
az acr create -n $ACR -g $RG --sku Basic --admin-enabled true

# エージェントのコンテナを ACR 上でビルド（カレント = src/agent。その Dockerfile を使う）
az acr build -r $ACR -t agent:latest .

# Linux プラン（学習用途ではコスト最小の Basic B1 を既定）
az appservice plan create -n $PLAN -g $RG --is-linux --sku B1

# Web アプリ（コンテナ）
az webapp create -n $APP -g $RG -p $PLAN `
  --deployment-container-image-name "$ACR.azurecr.io/agent:latest"

# App Service の環境変数を反映
$settings = Get-Content ".env" | Where-Object { $_ -match '^[^#\s][^=]*=' }
az webapp config appsettings set -n $APP -g $RG --settings $settings
```

> **補足: 作成時に「quota」エラーが出る場合**
> App Service プラン（`Basic B3` など Free/Consumption 以外の tier）は専用 VM を消費するため、サブスクリプション／リージョンの VM 枠が `0` だと `Operation cannot be completed without additional quota`（`Current Limit (Total VMs): 0`）というエラーで失敗する。次のいずれかで対処する。
> 1. **別リージョンで作り直す**（最も手軽。ただし内部サンドボックス系サブスクリプションではリージョンを変えても同じ枠 0 のことがある）。
> 2. **クォータ増加を申請する**:
>    1. [Azure Portal](https://portal.azure.com) の検索ボックスで「**クォータ**」を開く。
>    2. プロバイダー一覧から **App Service** を選ぶ。
>    3. 上部フィルターで**サブスクリプション**と**リージョン**（App Service を作った場所）を選ぶ。
>    4. 対象 SKU の枠（`Basic B1` なら **B1 VMs**）の行で **鉛筆アイコン** をクリックし、新しい上限値を入力 → **送信**。数分でレビューされる。
> 参考: [クォータ増加を申請する](https://learn.microsoft.com/azure/quotas/quickstart-increase-quota-portal)

### 6-2. Ollama（LLM）を sidecar で追加

App Service の **sidecar コンテナ**機能で `ollama/ollama` を横に足し、エージェントは `http://localhost:11434` で呼ぶ。

- [Azure ポータル](https://portal.azure.com/) > App Services > 作成したアプリの管理画面 > 左ナビの「デプロイ」配下 **デプロイ センター** を選択
  - 上部タブで **コンテナー** を選択（メインコンテナ1つだけが表示されている）
  - **追加 → カスタム コンテナー** を選択すると、右側に「コンテナーの追加」ペインが開く。**種類** は自動的に「**サイドカー**」に設定される（選択不要）
  - ペインの入力項目：
    - **名前**：任意（例: `ollama`）
    - **イメージのソース**：**「その他のコンテナー レジストリ」** を選ぶ（`ollama/ollama` は ACR ではなく Docker Hub の公開イメージのため）
    - **イメージの種類**：**パブリック**（認証不要の公開イメージ）
    - **レジストリ サーバー URL**：`https://index.docker.io`（Docker Hub 本体の URL）
    - **イメージとタグ**：`ollama/ollama:latest`（「イメージ」と「タグ」が1つの入力欄にまとまっている）
    - **ポート**：`11434`
    - **スタートアップ コマンド**：空欄のまま（イメージ既定の起動コマンドを使う）
  - **適用** を選択（メイン／サイドカーの2コンテナ構成になる）

### 6-3. エージェントの endpoint を Agent 365 に登録する

ここまでで、エージェント本体はクラウド（App Service）で動く URL を持った。最後に、その **URL（＝メッセージの届け先＝messaging endpoint）を Agent 365 に教え**、エージェントと道具（MCP）を**登録**する。

```powershell
# 次のコマンドの実行時に入力を求められるURLを出力する
echo "https://$APP.azurewebsites.net/api/messages"

# (1) デプロイ後の実 URL を messaging endpoint に反映。エージェントの登録もこの1コマンドで完了する。
# 複数回、画面の指示に従って指示や認証を行う
a365 setup all --m365

# (2) 道具（MCP）を登録申請（Tools › Requests に出るようになる）
#Enter description for tool `echo` → Echoes back the input text.
#Enter description for tool `now` → Returns the current server time.
#Enter publisher name  →  thiraga
#Enter server description  → Custom MCP server for the Agent 365 hands-on training, providing echo and now tools.

a365 develop-mcp register-external-mcp-server `
  --server-name "$MCP" `
  --server-url  "https://$FUNC.azurewebsites.net/runtime/webhooks/mcp" `
  --auth-type   "NoAuth" `
  --tools       "echo,now"
```

- **エージェント**は登録すると承認不要でそのまま 使用可能になる（[Register 段階の仕様](https://learn.microsoft.com/microsoft-agent-365/developer/get-started#adding-agent-365-capabilities-incrementally)。
- 一方、**道具（MCP）は Tools › Requests** に `Pending` として現れ、[管理者の承認と Entra 委任アクセス許可への同意が必須](https://learn.microsoft.com/microsoft-365/admin/manage/manage-tools-for-agent?view=o365-worldwide#review-and-approve-tool-requests)（。
- エージェントを **Teams で使えるようにするフローは [第2部 B](./part2-1b-custom.md)** で別途発生。

> **補足: `a365 setup all` が `wids` クレーム不足で失敗する場合**
> `a365` CLI は、ユーザーの Entra ロールを、アクセストークンに含まれる **`wids` クレーム**から読み取って判定しているため、このクレームが不足していると、必要な権限をもったユーザによる手動作業が必要だと判断されてしまう。
> - **マニフェスト エディターで追加する方法**：
>   1. [Microsoft Entra 管理センター](https://entra.microsoft.com/) を開く
>   2. **Entra ID** >  **アプリの登録** を選択
>   3. すべてのアプリケーションの一覧から対象アプリ（`Agent 365 CLI`）を選んで開く
>   4. そのアプリの詳細画面で左ナビ **マニフェスト** を選択
>   5. JSON 内の `"optionalClaims": null,` を次のブロックに置き換える：
>      ```json
>      "optionalClaims": {
>          "idToken": [],
>          "accessToken": [
>              { "name": "wids", "source": null, "essential": false, "additionalProperties": [] }
>          ],
>          "saml2Token": []
>      },
>      ```
>   6. 上部の **保存** を選択
>   7. `az logout` → `az login` でトークンを取り直したうえでコマンドを再実行。

> **補足: `a365 setup all` の委任アクセス許可（delegated permissions）の同意が 失敗する場合**
> **状況の確認：CLI 検証コマンド**
> ```powershell
> a365 query-entra inheritance
> ```
> 最後の行が `Summary: 5 of 5 resource(s) have effective inheritance ...` になっていれば、実際には全リソースへの許可が揃っている。
>
> **対応：Microsoft Entra 管理センター**
> 1. [Microsoft Entra 管理センター](https://entra.microsoft.com/) を開く
> 2. 左ナビで **Entra ID** > **Agents** > **Agent blueprints** を選択（
> 3. 対象のブループリント（例: `A365-Training-Agent Blueprint`）を選ぶ
> 4. 左ナビ **Access** 配下の **Granted permissions (Preview)** を選択
> 5. **管理者の同意** タブで、要求している全リソース（Microsoft Graph / Agent Tools / Messaging Bot API / Observability API / Power Platform API）の各行が付与済み になっていれば許可済み。付与されていない場合は、手動で付与を行う。


---

→ 次：**[第2部 B：承認と観測データ作成](./part2-1b-custom.md)** ｜ [README（概要）](../README.MD)
