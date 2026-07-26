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

このルートで扱うファイルは **(1) 自作コード**、**(2) `a365 setup all` / Skills が自動生成するもの**、**(3) シークレット** の 3 種に分かれる。本リポジトリの [`../src/`](../src) は (1) に相当する。(2)・(3) は各自の環境で生成されるためリポジトリには含まれない。

> 💡 (1)＝エージェントの“頭脳”（何を答え・どの道具を呼ぶか）、(2)＝“受付と起動”（外部からのメッセージを受け取り (1) に渡すサーバー部分）の役割。(2) は定型の認証・ルーティング等で SDK に紐づくため、Skills に自動生成させる。

```text
Agent365-Training/
├── src/                             # (1) 本リポジトリに同梱（あなたが書くコード）
│   ├── agent/                       #   エージェント本体（App Service にデプロイ）
│   │   ├── app.py                   #     頭脳：発言を受け取り AI に渡して返答する
│   │   ├── llm.py                   #     AI（自前ホストの Qwen）に質問して答えをもらう
│   │   ├── obo.py                   #     「ログイン中ユーザーの代理」で動くためのトークン取得
│   │   ├── observability_setup.py   #     「誰が・どの道具を使ったか」を Agent 365 に送る設定
│   │   ├── requirements.txt         #     必要な Python ライブラリ
│   │   └── Dockerfile               #     コンテナ化の定義
│   └── mcp/                         #   自作の道具（MCP・Azure Functions にデプロイ）
│       ├── function_app.py          #     道具の中身（echo / now）
│       ├── host.json                #     Functions 設定（MCP 拡張）
│       └── requirements.txt         #     必要な Python ライブラリ
├── start_server.py                  # (2) Skills が自動生成：受付と起動（外部からのメッセージを (1) へ橋渡し）
├── appPackage/manifest.json         # (2) Skills が自動生成：エージェントを登録するための情報（名前など）
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
$MCP   = "agent365-training-mcp"               # 自作 MCP サーバーの表示名（管理センターに出る名前）
```

## 1. ツールを用意して Azure にログインする

```powershell
# バージョンが返れば OK（無ければ各コメントのコマンドで導入）
node --version   # 無ければ: winget install OpenJS.NodeJS.LTS
az   version     # 無ければ: winget install Microsoft.AzureCLI
func --version   # 無ければ: npm i -g azure-functions-core-tools@4
a365 --version   # 無ければ: dotnet tool install -g Microsoft.Agents.A365.DevTools.Cli

# Azure にサインイン
az login
az account set --subscription "<SUBSCRIPTION_ID>"
```

## 2. Agent 365 Skills を導入する

これを導入すると、Github Copilot / Claude Code に自然言語で指示したときに、(2)「受付と起動」のサーバー部分（`start_server.py`）等を自動生成してくれる。

```powershell
git clone https://github.com/microsoft/agent365-skills.git
node .\agent365-skills\scripts\install.js   # VS Code の chat.agentSkillsLocations に登録される（Reload Window で反映）
```

> **Skills が何をしてくれるか（重要）**
> - `make-a365-agent` … (2) ホスティング層（Python は aiohttp の `start_server.py`）＋ `a365.config.json` を生成
> - `instrument-observability` … OpenTelemetry を配管するコードを生成
> - `a365-setup` … 前提チェック＋ Blueprint 作成の入口

## 3. エージェントの「土台」を作る（Blueprint / Agent ID）

**ターミナルのコマンドではなく、AI チャットに次の指示を送る**と、先ほど導入した Skill が起動し、必要なコマンドを AI が代わりに実行してくれる。

```text
a365-setup を実行して。UPN を持たない Agent を OBO（委任）認可で作りたい。
```

> **この指示の意味**
> - **a365-setup を実行して** … Skill（`a365-setup`）を起動する合図
> - **UPN を持たない Agent** … 人間のようなメールアドレス／ログイン名（UPN）を**持たない**エージェント = **非 AI Teammate**
> - **OBO（委任 / on-behalf-of）認可** … エージェントが「今ログインしているユーザーの代理」として権限を借りて動く方式。

Skill が内部で `a365 setup all`を実行し、以下を**自動で**行う。

```text
要件チェック ─▶ Blueprint 作成 ─▶ 資格情報 ─▶ 委任権限の継承 ─▶ Agent Identity 作成(UPN無し) ─▶ 登録 ─▶ ローカルの .env へ接続情報を書き込み
```

途中で **2 回**、画面の指示に従って承認する：
1. **アプリ権限の付与** … `Assign this application permission now? [y/N]:` → `y`
2. **委任権限の管理者同意** … ブラウザが開く → サインイン → **Allow**

確認：

```powershell
a365 query-entra                                   # Entra 登録状態
Get-Content a365.generated.config.json | ConvertFrom-Json | Select-Object completed, agentBlueprintId
```

- `completed` が `True`、`a365.config.json` の `aiTeammate` が `false` なら成功
- ⚠️ `.env` と `a365.generated.config.json` は**コミット禁止**（`.gitignore` 済み）

## 4. 道具（MCP）を作ってクラウドに置く

エージェントが使う「道具」を、Azure Functions として建てる。コードは [../src/mcp/](../src/mcp)（`echo` / `now` の 2 ツール）。

### 4-1. Azure に空の Function App（入れ物）を作る

Functions を動かすための Azure リソース（リソースグループ・ストレージ・空の Function App）だけを作る。

```powershell
az group create -n $RG -l $LOC
az storage account create -n $STG -g $RG -l $LOC --sku Standard_LRS
az functionapp create -n $FUNC -g $RG -s $STG `
  --consumption-plan-location $LOC `
  --runtime python --runtime-version 3.11 --functions-version 4 --os-type Linux
```

### 4-2. 作った入れ物に MCP コードをアップロードする

4-1 で作った空の Function App（`$FUNC`）に、[../src/mcp/](../src/mcp) のコードを送り込む。

```powershell
cd ..\src\mcp        # function_app.py / host.json / requirements.txt があるフォルダ
func azure functionapp publish $FUNC
# → 公開 URL: https://$FUNC.azurewebsites.net/runtime/webhooks/mcp
cd ..\..\docs
```


> この節では**道具を作って Azure に置くだけ**。**Agent 365 への登録は 6 節、承認は [第2部 B](./part2-1b-custom.md)** でまとめて行う。

## 5. エージェント本体を実装する

これも 3 節 と同じく、**AI チャットに打ち込む自然言語の指示**。Copilot Chat（または Claude Code）に次を送ると、Skill（`make-a365-agent`）が (2) の受付・起動サーバーを生成する。

```text
非 AI Teammate のエージェントを OBO（委任）で作りたい。(2) の受付・起動サーバーを Python / aiohttp で生成して。
```

> **この指示の意味（初学者向け）**
> - **非 AI Teammate のエージェントを OBO（委任）で** … 3 節 で作ったのと同じ種類のエージェントとして扱う合図。Skill はこの言葉で生成するコードの形（認証の配線など）を判定する
> - **(2) の受付・起動サーバーを Python / aiohttp で生成して** … (2)「受付と起動」（`start_server.py`）を、Python の Web サーバーライブラリ **aiohttp** で作ってほしい、という依頼。このサーバーが外部からのメッセージを受け付けて (1)（`app.py`）に渡す

`make-a365-agent` が **`start_server.py`（(2)受付・起動）** を生成する。ここに **[../src/agent/](../src/agent) の中身（(1)あなたのコード）を配置・接続**する。

やること（B・具体手順）：
1. `../src/agent/` の `app.py` / `llm.py` / `obo.py` / `observability_setup.py` を、生成されたプロジェクト直下（`start_server.py` と同じ場所）にコピー
2. `app.py` はすでに `from start_server import build_adapter` で (2) に差し込む形になっている（そのまま使える）
3. `.env` に LLM と観測の設定を追記
   ```dotenv
   OLLAMA_BASE_URL=http://localhost:11434/v1
   OLLAMA_MODEL=qwen2.5:3b-instruct-q4_K_M
   ENABLE_A365_OBSERVABILITY=true
   ENABLE_A365_OBSERVABILITY_EXPORTER=true
   ```
4. 観測配線は Skill に任せてもよい。下の指示を AI チャットに送ると、Skill（`instrument-observability`）が OpenTelemetry の配線コードを生成する：
   ```text
   このエージェントに Agent 365 の観測を OBO（委任）で追加して。
   ```
   > **意味**：「このエージェントに Agent 365 の観測（誰が・どの道具を使ったかの記録送信）を、**OBO（委任）**で追加して」という依頼。`observability_setup.py` 相当の配線を代わりに書いてくれる。

## 6. Azure にデプロイして「登録」する

エージェント本体（(1)＋(2)）をコンテナにして App Service へ。**LLM（Qwen）は隣に置く Ollama コンテナ（sidecar）**で動かす。

### 6-1. コンテナレジストリと App Service を作る

```powershell
# コンテナレジストリ
az acr create -n $ACR -g $RG --sku Basic --admin-enabled true

# エージェントのコンテナを ACR 上でビルド（src/agent の Dockerfile を使う）
az acr build -r $ACR -t agent:latest ..\src\agent

# Linux プラン（Ollama を載せるためメモリ多めの P1v3。学習後は必ず削除）
az appservice plan create -n $PLAN -g $RG --is-linux --sku P1V3

# Web アプリ（コンテナ）
az webapp create -n $APP -g $RG -p $PLAN `
  --deployment-container-image-name "$ACR.azurecr.io/agent:latest"
```

### 6-2. Ollama（LLM）を sidecar で追加

App Service の **sidecar コンテナ**機能で `ollama/ollama` を横に足し、エージェントは `http://localhost:11434` で呼ぶ。

- [Azure ポータル](https://portal.azure.com/) → 対象 Web アプリ → **デプロイ センター → コンテナー（サイドカー）** → **追加**
  - イメージ：`ollama/ollama:latest`／ポート：`11434`
- 参考：[App Service の sidecar コンテナー](https://learn.microsoft.com/azure/app-service/tutorial-custom-container-sidecar)


### 6-3. エージェントの endpoint を Agent 365 に登録する

ここまでで、エージェント本体はクラウド（App Service）で動く URL を持った。最後に、その **URL（＝メッセージの届け先＝messaging endpoint）を Agent 365 に教え**、エージェントと道具（MCP）を**登録**する。

```powershell
# (1) デプロイ後の実 URL を messaging endpoint に反映（＝エージェントの住所を最新化。）
#    --m365 を付けると Teams / Microsoft 365 Copilot チャネル用に messaging endpoint を登録する
a365 setup all --m365

# (2) エージェントを登録申請（Agents › Requests に Pending で出る）
a365 publish

# (3) 道具（MCP）を登録申請（Tools › Requests に Pending で出る）
a365 develop-mcp register-external-mcp-server `
  --server-name "$MCP" `
  --server-url  "https://$FUNC.azurewebsites.net/runtime/webhooks/mcp" `
  --auth-type   "NoAuth" `
  --tools       "echo,now"
```

- **`--m365`** … Teams / Copilot から話しかけられる「M365 エージェント」として messaging endpoint を登録する（[Learn: setup](https://learn.microsoft.com/microsoft-agent-365/developer/registration)）。
- 登録すると、**エージェントは Agents › Requests、道具（MCP）は Tools › Requests** に `Pending` として現れる。**承認と Teams への接続は [第2部 B](./part2-1b-custom.md)** で行う。

---

→ 次：**[第2部 B：承認と観測データ作成](./part2-1b-custom.md)** ｜ [README（概要）](../README.MD)
