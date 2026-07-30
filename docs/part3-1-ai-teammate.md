# 第3部 A：AI Teammate を作る（開発者）

**独自の M365 ユーザー ID（UPN・メールボックス・Teams 在席・組織図エントリ）を持つ AI Teammate** を作る。頭脳は **Microsoft Foundry のクラウドモデル**を直接呼ぶ。

第1部C の **S2S エージェント**は「アプリとして」動いたが、AI Teammate は **"人"としてふるまう**（@mention・メール・会議招待で対話できる）。

> ⚠️ Preview を多く含む。コマンド・UI・提供リージョンは変わり得るので Microsoft Learn で最新を確認すること。

**目次**

- [第3部 A：AI Teammate を作る（開発者）](#第3部-aai-teammate-を作る開発者)
  - [1. サインインを揃える](#1-サインインを揃える)
  - [2. Foundry でモデルをデプロイする（頭脳）](#2-foundry-でモデルをデプロイする頭脳)
  - [3. エージェント本体（src/ai-teammate）を用意する](#3-エージェント本体srcai-teammateを用意する)
  - [4. AI Teammate 化する（Blueprint＋独自 M365 ID）](#4-ai-teammate-化するblueprint独自-m365-id)
    - [ホスティング層を作る（必須）](#ホスティング層を作る必須)
  - [5. 公開してインスタンスを作成する](#5-公開してインスタンスを作成する)
  - [6. "人として" 動作確認する](#6-人として-動作確認する)

## 1. サインインを揃える

サインインは第1部と同様、**`az login` と Teams Toolkit の M365 サインインを同じテナントに揃える**。

```powershell
az login
m365agentstoolkit-cli account login m365
m365agentstoolkit-cli account show   # az account show と同じテナントか確認
```

## 2. Foundry でモデルをデプロイする（頭脳）

AI Teammate の思考エンジンに使うモデルを Foundry にデプロイし、**エンドポイント・API キー・デプロイ名**を控える。

1. [Foundry ポータル](https://ai.azure.com/) にサインイン。ホーム画面の下段に **API キー** と **Azure OpenAI エンドポイント**（`https://<リソース名>.openai.azure.com/openai/v1` 形式）が表示される。
2. モデルをデプロイする：ホームの **「モデルの選択」› モデルを探す** から使うモデル（例 `gpt-4.1`）を開き **デプロイ**（既定の設定でよい）。
3. 次の3つを控える（次節の `.env` に使う）：
   | 控える値 | 取得場所 |
   |---------|---------|
   | **Azure OpenAI エンドポイント**（`.../openai/v1`） | ホーム画面「Azure OpenAI エンドポイント」右のコピーアイコン |
   | **API キー** | ホーム画面「API キー」右のコピーアイコン |
   | **デプロイ名** | 「モデルを使用する › デプロイの表示」で確認 |

## 3. エージェント本体（src/ai-teammate）を用意する

**1. リポジトリを取得する**（Part 1 で clone 済みならスキップ）

```powershell
git clone https://github.com/fatman3110/Agent365-Training.git
cd Agent365-Training/src/ai-teammate
```

**2. `.env` を作る**（まず 2 節で控えた値を変数に入れ、それを `.env` に書き出す。`.env` はコミットしない）

```powershell
# 2 節で控えた値をそれぞれ貼り付ける
$BASE_URL   = "<Azure OpenAI エンドポイント>"
$API_KEY    = "<キー>"
$DEPLOYMENT = "<デプロイ名>"

# .env に書き出す
Set-Content .env @"
AZURE_OPENAI_BASE_URL=$BASE_URL
AZURE_OPENAI_API_KEY=$API_KEY
AZURE_OPENAI_DEPLOYMENT=$DEPLOYMENT
"@
```

**3. ローカルで疎通確認**

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -c "import llm; print(llm.chat_complete('こんにちは、自己紹介して'))"
```

## 4. AI Teammate 化する（Blueprint＋独自 M365 ID）

第1部C と同じ **スキル駆動**で進める。`src/ai-teammate` を開いた状態で、**AI チャット** に次を指示する：

```text
src/ai-teammate のこのエージェントを Microsoft Agent 365 の AI Teammate にして。
独自の M365 ユーザー ID（UPN・メールボックス・Teams 在席）を持たせ、頭脳は .env の AZURE_OPENAI_* で Foundry のクラウドモデルを使う。
capabilities は AI Teammate、認証は agentic-user（--authmode は付けない）でセットアップして。
```

スキル（`a365-setup` → `make-ai-teammate`）が起動し、対話に沿って **`a365 setup all --aiteammate --m365`** を実行する。これで **Blueprint＋継承権限＋管理者同意**が作成される（`--authmode` は使わない）。

> スキルを使わず直接実行してもよい（結果は同じ）：
> ```powershell
> a365 setup all --aiteammate --m365 -n a365-teammate-xxxx
> ```

- 途中の `[y/N]` 承認・ブラウザ認証は画面の指示どおりに進める。
- **成功の判定**：`Setup completed successfully` が表示され、`a365.generated.config.json` に `agentBlueprintId` が入り、`.env` にテナント・観測性設定が stamp される（シークレットは gitignore 済み）。
- **⚠️ このステップではホスティング層（Teams で動く本体）は作られない**。必ず下の手順で手動作成する。

### ホスティング層を作る（必須）

`llm.py`（頭脳）だけでは Teams のメッセージを受け取れない。**本体（ホスティング層）は本リポジトリに同梱済み**。`src/ai-teammate/` の内訳：

| ファイル | 役割 |
|---------|------|
| `agent.py` | メッセージを `llm.chat_complete` に渡す最小の AI Teammate 本体 |
| `agent_interface.py` | 本体の抽象基底 |
| `host_agent_server.py` | aiohttp サーバー＋A365 ルーティング（`/api/messages`・`/api/health`）|
| `main.py` | 起動エントリ（`python main.py`）|
| `Dockerfile` | App Service デプロイ用（単一コンテナ・Ollama sidecar 無し）|
| `requirements.txt` | 頭脳＋ホスティング／A365 ランタイム依存 |


## 5. 公開してインスタンスを作成する

AI Teammate は「**instance 作成**」まで行って初めて M365 で人として動く。**エンドポイント確定 → publish → 管理センターで instance 作成**の順で進める。

**スキル駆動**：`src/ai-teammate` を開いた状態で、AI チャットに次を指示する：

```text
この AI Teammate（src/ai-teammate）を Teams で動かしたい。
Azure App Service（単一コンテナ）にデプロイしてエンドポイントを作り、blueprint に登録して、
a365 publish でパッケージを作り、M365 管理センターでの instance 作成手順まで案内して。
```

スキル（`make-ai-teammate` の publish フェーズ）が動く場合は案内に従ってよいが、**動かない前提で以下を手動で行う**：

1. **App Service にデプロイしてエンドポイントを得る**（Part 1 未実施でも動くよう必要リソースを**新規作成**する。RG／プランなど**自分のサブスク内**のリソースは冪等に再利用される。**ただし ACR 名とアプリ名は世界で一意**——`xxxx` は必ず**自分だけのユニーク文字列**に置換すること（他テナントが使用済みの名前は `AlreadyInUse` で失敗する）：

   ```powershell
   # --- 名前（xxxx は自分用のユニークな文字列に置換）---
   $RG   = "rg-agent365-training"          # 無ければ作成／有れば再利用
   $LOC  = "japaneast"
   $ACR  = "acragent365xxxx"                # ★世界で一意・英数字のみ。xxxx を自分の値に。空き確認: az acr check-name -n <名前>
   $PLAN = "plan-agent365-teammate-xxxx"
   $APP  = "app-agent365-teammate-xxxx"     # 世界で一意

   # --- リソース作成（いずれも冪等：既存なら再利用しエラーにならない）---
   az group create -n $RG -l $LOC
   az acr create -n $ACR -g $RG --sku Basic --admin-enabled false
   az appservice plan create -n $PLAN -g $RG --is-linux --sku B2

   # カレント = src/ai-teammate。同梱 Dockerfile でイメージをビルド
   az acr build -r $ACR -t ai-teammate:latest .

   # Web アプリ（コンテナ）
   az webapp create -n $APP -g $RG -p $PLAN --deployment-container-image-name "$ACR.azurecr.io/ai-teammate:latest"

   # .env をアプリ設定に反映（AZURE_OPENAI_* / a365 setup が stamp した設定）＋待受ポート
   $settings = Get-Content ".env" | Where-Object { $_ -match '^[^#\s][^=]*=' }
   az webapp config appsettings set -n $APP -g $RG --settings $settings WEBSITES_PORT=3978

   # マネージド ID を有効化し ACR からの pull 権限（AcrPull）を付与
   az webapp identity assign -n $APP -g $RG
   $principalId = az webapp identity show -n $APP -g $RG --query principalId -o tsv
   $acrId = az acr show -n $ACR -g $RG --query id -o tsv
   az role assignment create --assignee $principalId --scope $acrId --role AcrPull 2>$null
   # → エンドポイント：https://$APP.azurewebsites.net/api/messages
   ```

   得たエンドポイントを blueprint に登録（4 節で defer した分をここで設定）：
   ```powershell
   a365 setup blueprint --endpoint-only --messaging-endpoint "https://$APP.azurewebsites.net/api/messages" --m365
   ```
2. **publish**：`a365 publish` で Teams/M365 パッケージ（`manifest.zip`）を生成（アップロードはしない）
3. **管理センターへ手動アップロード**：[M365 管理センター](https://admin.microsoft.com/) › **エージェント › すべてのエージェント** でパッケージを登録
4. **Teams Developer Portal で確認**：Agent Type＝API Based、Notification URL＝登録したエンドポイント
5. **instance 作成／承認**：Teams Apps から **instance を要求** → 管理者が承認 → **UPN・メールボックスが有効化**される

> 一次情報: [Create an instance](https://learn.microsoft.com/microsoft-agent-365/developer/create-instance) ／ [Testing](https://learn.microsoft.com/microsoft-agent-365/developer/testing) ／ [Azure へデプロイ](https://learn.microsoft.com/microsoft-agent-365/developer/deploy-agent-azure)
> ⚠️ **Frontier 未登録テナントでは instance 作成が通らない**ことがある。画面の指示と上記 Learn を都度確認する。

## 6. "人として" 動作確認する

インスタンス有効化後、**第1部C の S2S エージェントとの違い**を体験する：

- **Teams で @mention** して会話する（S2S エージェントは Bot 的、AI Teammate は"人"として在席）
- **メールを送る**（AI Teammate は自分のメールボックスで受信・返信できる）
- **ディレクトリ／組織図**に載っていることを確認（マネージャー配下）

その後、[第2部](./part2-2-observe.md) の Observe / Govern / Secure で、**独自 ID エージェント**としての見え方（アクティビティ・ガバナンス・保護）を確認する。

---

← 戻る：[第3部 概要](./part3-0-overview.md) ｜ 次：**[3-B：自作 MCP サーバー（BYO MCP）](./part3-2-byo-mcp.md)**
