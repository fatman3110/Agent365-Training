# 第1部：環境構築（開発者）

> 開発者（VS Code / ターミナル）の作業。**コピペで手を動かせる**よう、実コマンドを載せています。
> 完了すると、エージェントが Agent 365 に登録され、Azure（クラウド）で動く状態になります。
>
> ⚠️ Microsoft Agent 365 は Preview を多く含みます。コマンド・API は変わり得るので、詰まったら各節のリンク先（Microsoft Learn）で最新を確認してください。

## 0. 最初に「名前」を決める（1 回だけ）

以降のコマンドはこの変数をそのまま使います。**`xxxx` を自分用のユニークな文字列に変えて**、ターミナルに貼り付けてください（PowerShell）。

```powershell
$RG    = "rg-agent365-training"        # リソースグループ
$LOC   = "japaneast"                   # リージョン
$ACR   = "acragent365xxxx"             # コンテナレジストリ（世界で一意・小文字英数のみ）
$PLAN  = "plan-agent365"               # App Service プラン
$APP   = "app-agent365-xxxx"           # エージェント本体の Web アプリ（世界で一意）
$FUNC  = "func-agent365-mcp-xxxx"      # MCP 用 Functions（世界で一意）
$STG   = "stagent365mcpxxxx"           # Functions 用ストレージ（世界で一意・小文字英数のみ）
$MCP   = "mymcp"                        # MCP サーバーの表示名
```

## 1. ツールを用意して Azure にログインする

```powershell
# バージョンが返れば OK（無ければ各コメントのコマンドで導入）
node --version   # 18+
az   version     # Azure CLI（無ければ: winget install Microsoft.AzureCLI）
func --version   # Azure Functions Core Tools（無ければ: npm i -g azure-functions-core-tools@4）
a365 --version   # 無ければ: dotnet tool install -g Microsoft.Agents.A365.DevTools.Cli

# Azure にサインイン
az login
az account set --subscription "<SUBSCRIPTION_ID_または名前>"
```

## 2. Agent 365 Skills を導入する

Copilot / Claude Code に自然言語で指示すると、**②「受付と起動」のサーバー部分（`start_server.py`）・観測配線・MCP 追加を自動生成**してくれます（あなたは①の中身だけ書けばよい）。

```powershell
# GitHub Copilot CLI（gh skill 対応版）
gh skill add microsoft/agent365-skills

# gh skill 非対応版 / VS Code agent mode の場合
git clone https://github.com/microsoft/agent365-skills.git
node <clone>/scripts/install.js   # VS Code の chat.agentSkillsLocations に登録される（Reload Window で反映）
```

> **Skills が何をしてくれるか（重要）**
> - `make-a365-agent` … ②ホスティング層（Python は aiohttp の `start_server.py`）＋ `a365.config.json` を生成
> - `instrument-observability` … 観測（OpenTelemetry）配線コードを生成
> - `a365-setup` … 前提チェック＋ Blueprint 作成の入口

## 3. エージェントの「土台」を作る（Blueprint / Agent ID）

VS Code の Copilot Chat（または Claude Code）に、次を**そのまま貼って**実行させます。

```text
a365-setup を実行して。UPN を持たない Agent を OBO（委任）認可で作りたい。
Make this a non-AI-Teammate Agent using OBO (delegated / on-behalf-of).
```

Skill が内部で `a365 setup all`（`--aiteammate` は付けない）を実行し、以下を**自動で**行います。

```text
要件チェック ─▶ Blueprint 作成 ─▶ 資格情報 ─▶ 委任権限の継承 ─▶ Agent Identity(UPN無し) ─▶ 登録 ─▶ .env スタンプ
```

途中で **2 回**、画面の指示に従って承認します：
1. **アプリ権限の付与** … `Assign this application permission now? [y/N]:` → `y`
2. **委任権限の管理者同意** … ブラウザが開く → サインイン → **Allow**

> **このコマンドが生成するもの（C）**：エージェントの ID に加えて、**②`start_server.py`（受付・起動）** と **③`.env`（接続情報）**、**②`a365.config.json`** が作られます。これらが「土台」です。だから **§5 のアプリ実装より先**に実行します。

確認：

```powershell
a365 query-entra                                   # Entra 登録状態
Get-Content a365.generated.config.json | ConvertFrom-Json | Select-Object completed, agentBlueprintId
```

- `completed` が `True`、`a365.config.json` の `aiTeammate` が `false` なら成功
- ⚠️ `.env` と `a365.generated.config.json` は**コミット禁止**（`.gitignore` 済み）

## 4. 道具（MCP）を作ってクラウドに置く

エージェントが使う「道具」を、Azure Functions として建てます。コードは [../src/mcp/](../src/mcp)（`echo` / `now` の 2 ツール）。

### 4-1. Azure に Functions を作る（コピペ）

```powershell
az group create -n $RG -l $LOC
az storage account create -n $STG -g $RG -l $LOC --sku Standard_LRS
az functionapp create -n $FUNC -g $RG -s $STG `
  --consumption-plan-location $LOC `
  --runtime python --runtime-version 3.11 --functions-version 4 --os-type Linux
```

### 4-2. MCP コードをデプロイ

```powershell
cd ..\src\mcp        # function_app.py / host.json / requirements.txt があるフォルダ
func azure functionapp publish $FUNC
# → 公開 URL: https://$FUNC.azurewebsites.net/runtime/webhooks/mcp
cd ..\..\docs
```

> MCP の Functions 拡張は Preview。`host.json` の `extensionBundle` は MCP 対応版（Experimental バンドル）を指定済み。うまく出ない場合は [Azure Functions リモート MCP のドキュメント](https://learn.microsoft.com/azure/azure-functions/) で最新のバンドル版を確認。

> この節では**道具を作って Azure に置くだけ**。**Agent 365 への登録は §6、承認は [第2部 §1](./part2-handson.md)** でまとめて行います。

## 5. エージェント本体を実装する

Copilot / Claude Code に、②の受付・起動サーバーを生成させます。

```text
Make this a non-AI-Teammate Agent using OBO. Python / aiohttp のホスティング層を生成して。
```

`make-a365-agent` が **`start_server.py`（②受付・起動）** を生成します。ここに **[../src/agent/](../src/agent) の中身（①あなたのコード）を配置・接続**します。

やること（B・具体手順）：
1. `../src/agent/` の `app.py` / `llm.py` / `obo.py` / `observability_setup.py` を、生成されたプロジェクト直下（`start_server.py` と同じ場所）にコピー
2. `app.py` はすでに `from start_server import build_adapter` で②に差し込む形になっている（そのまま使える）
3. `.env` に LLM と観測の設定を追記
   ```dotenv
   OLLAMA_BASE_URL=http://localhost:11434/v1
   OLLAMA_MODEL=qwen2.5:3b-instruct-q4_K_M
   ENABLE_A365_OBSERVABILITY=true
   ENABLE_A365_OBSERVABILITY_EXPORTER=true
   ```
4. 観測配線は Skill に任せてもよい：
   ```text
   Add A365 observability to this agent (delegated / OBO).
   ```

> **①と②の役割**：①（`app.py` ほか）＝“頭脳”、②（`start_server.py`）＝“受付・起動”。①だけでは受信口が無く、②だけでは中身が無い。両方そろって動きます。

## 6. Azure にデプロイして「登録」する

エージェント本体（①＋②）をコンテナにして App Service へ。**LLM（Qwen）は隣に置く Ollama コンテナ（sidecar）**で動かします。

### 6-1. コンテナレジストリと App Service を作る（コピペ）

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

### 6-2. Ollama（LLM）を sidecar で追加（★このステップだけ少し高度）

App Service の **sidecar コンテナ**機能で `ollama/ollama` を横に足し、エージェントは `http://localhost:11434` で呼びます。

- Azure ポータル → 対象 Web アプリ → **デプロイ センター → コンテナー（サイドカー）** → **追加**
  - イメージ：`ollama/ollama:latest`／ポート：`11434`
- 参考：[App Service の sidecar コンテナー](https://learn.microsoft.com/azure/app-service/tutorial-custom-container-sidecar)

> 😌 **もっと簡単に済ませたい場合**：Ollama の sidecar を使わず、**Azure OpenAI などのマネージド LLM** に向ける手もあります（`llm.py` の接続先を差し替えるだけ）。コスト最優先で自前ホストにこだわらないなら、まずこちらで動かすのが楽です。

### 6-3. messaging endpoint を更新して「登録」する

```powershell
# デプロイ後の実 URL を messaging endpoint に反映（冪等・再実行安全）
a365 setup all

# ① エージェントを登録（Agents › Requests に Pending で出る）
a365 publish

# ② 道具（MCP）を登録（Tools › Requests に Pending で出る）
a365 develop-mcp register-external-mcp-server `
  --server-name "$MCP" `
  --server-url  "https://$FUNC.azurewebsites.net/runtime/webhooks/mcp" `
  --auth-type   "NoAuth" `
  --tools       "echo,now"
```

登録すると、**エージェントは Agents › Requests、道具（MCP）は Tools › Requests** に `Pending` として現れます。**ここから先が第2部**（管理者による承認＝管理下配置）。

---

→ 次：**[第2部：Agent 365 ハンズオン](./part2-handson.md)** ｜ [README（概要）](../README.MD)
