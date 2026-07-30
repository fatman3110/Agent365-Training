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

第1部C と同じ **スキル駆動**で進める。`src/ai-teammate` を開いた状態で、**AI チャット（GitHub Copilot は Agent モード）** に次を指示する：

```text
src/ai-teammate のこのエージェントを Microsoft Agent 365 の AI Teammate にして。
独自の M365 ユーザー ID（UPN・メールボックス・Teams 在席）を持たせ、頭脳は .env の AZURE_OPENAI_* で Foundry のクラウドモデルを使う。
capabilities は AI Teammate、認証は agentic-user（--authmode は付けない）でセットアップして。
```

スキル（`a365-setup` → `make-ai-teammate`）が起動し、対話に沿って次を行う：

1. スタック検出 → capabilities で **AI Teammate** を選択（Register・Observability も自動同梱）
2. ホスティング層（Python は aiohttp）＋ `AgentApplication` ＋通知処理を生成
3. 内部で **`a365 setup all --aiteammate --m365`** を実行 → **Blueprint ＋ Agentic User（UPN 付き）＋ Agent ID** を払い出し（`--authmode` は使わない）

- 途中の `[y/N]` 承認・ブラウザ認証は画面の指示どおりに進める。
- **成功の判定**：`a365.generated.config.json` に `agentBlueprintId` が入り、Entra に **Agent Identity と 1:1 の User Account** が作られる。

## 5. 公開してインスタンスを作成する

AI Teammate は「**instance 作成**」まで行って初めて M365 で人として動く。スキルが以下を案内する：

1. **publish**：`a365 publish` で Teams/M365 パッケージを生成 → **M365 管理センターへアップロード（手動）**
2. **管理者承認**：管理センター **エージェント › すべてのエージェント › 要求** で承認
3. **インスタンス要求／作成**：AI Teammate は blueprint から **instance を作成**して初めて UPN・メールボックスが有効化される（管理センター主導）
4. **Teams への接続**：Notification URL 等の再確認（スキル／画面の指示に従う）

## 6. "人として" 動作確認する

インスタンス有効化後、**第1部C の S2S エージェントとの違い**を体験する：

- **Teams で @mention** して会話する（S2S エージェントは Bot 的、AI Teammate は"人"として在席）
- **メールを送る**（AI Teammate は自分のメールボックスで受信・返信できる）
- **ディレクトリ／組織図**に載っていることを確認（マネージャー配下）

その後、[第2部](./part2-2-observe.md) の Observe / Govern / Secure で、**独自 ID エージェント**としての見え方（アクティビティ・ガバナンス・保護）を確認する。

---

← 戻る：[第3部 概要](./part3-0-overview.md) ｜ 次：**[3-B：自作 MCP サーバー（BYO MCP）](./part3-2-byo-mcp.md)**
