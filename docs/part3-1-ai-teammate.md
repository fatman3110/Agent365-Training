# 第3部 A：AI Teammate を作る（開発者）

**独自の M365 ユーザー ID（UPN・メールボックス・Teams 在席・組織図エントリ）を持つ AI Teammate** を作る。頭脳は **Microsoft Foundry のクラウドモデル**を直接呼ぶ。

第1部C の **S2S エージェント**は「アプリとして」動いたが、AI Teammate は **"人"としてふるまう**（@mention・メール・会議招待で対話できる）。

> ⚠️ Preview を多く含む。コマンド・UI・提供リージョンは変わり得るので Microsoft Learn で最新を確認すること。

**目次**

- [第3部 A：AI Teammate を作る（開発者）](#第3部-aai-teammate-を作る開発者)
  - [0. 名前を決める](#0-名前を決める)
  - [1. サインインを揃える](#1-サインインを揃える)
  - [2. Foundry でモデルをデプロイする（頭脳）](#2-foundry-でモデルをデプロイする頭脳)
  - [3. エージェント本体（src/ai-teammate）を用意する](#3-エージェント本体srcai-teammateを用意する)
  - [4. AI Teammate 化する（Blueprint＋独自 M365 ID）](#4-ai-teammate-化するblueprint独自-m365-id)
  - [5. 公開してインスタンスを作成する](#5-公開してインスタンスを作成する)
  - [6. "人として" 動作確認する](#6-人として-動作確認する)

## 0. 名前を決める

第1部と同じく **`xxxx` を自分用のユニークな文字列**に置換する（既存の `SGT31` 等は使わない）。**既存 RG を再利用**し、既存リソースには触れない。

```powershell
$RG        = "rg-agent365-training"          # 既存 RG を再利用（変更しない）
$LOC       = "japaneast"
$TMNAME    = "a365-teammate-xxxx"            # AI Teammate の a365 --agent-name（20 文字以内）
$FOUNDRYRG = $RG                             # Foundry も同 RG で可
```

## 1. サインインを揃える

サインインは第1部と同様、**`az login` と Teams Toolkit の M365 サインインを同じテナントに揃える**。

```powershell
az login
m365agentstoolkit-cli account login m365
m365agentstoolkit-cli account show   # az account show と同じテナントか確認
```

## 2. Foundry でモデルをデプロイする（頭脳）

AI Teammate の思考エンジンに使うモデルを Foundry にデプロイし、**エンドポイント・API キー・デプロイ名**を控える。

1. [Foundry ポータル](https://ai.azure.com/) にサインイン（右上の **新しい Foundry** トグル ON。第1部B で作成したプロジェクトを再利用してよい）。ホーム画面の下段に **API キー** と **Azure OpenAI エンドポイント**（`https://<リソース名>.openai.azure.com/openai/v1` 形式）が表示される。
2. モデルをデプロイする：ホームの **「モデルの選択」› モデルを探す** から使うモデル（例 `gpt-4o-mini`）を開き **デプロイ**（デプロイ名・種類は既定のままで可）。
   - デプロイ済みモデルは **「モデルを使用する」› デプロイの表示** で一覧・デプロイ名を確認できる。
3. 次の3つを控える（次節の `.env` に使う）：
   | 控える値 | 取得場所 |
   |---------|---------|
   | **Azure OpenAI エンドポイント**（`.../openai/v1`） | ホーム画面「Azure OpenAI エンドポイント」右のコピーアイコン |
   | **API キー** | ホーム画面「API キー」右のコピーアイコン |
   | **デプロイ名** | 「モデルを使用する › デプロイの表示」で確認 |

> Foundry の **v1 API** は `api-version` 不要で、**OpenAI クライアントの `base_url` に `.../openai/v1/` を渡すだけ**で呼べる（Azure 専用クライアント不要）。同梱の `llm.py` はこの方式。
> 出典: [Azure OpenAI in Foundry Models v1 API](https://learn.microsoft.com/azure/foundry/openai/api-version-lifecycle#code-changes)

## 3. エージェント本体（src/ai-teammate）を用意する

このリポジトリに完成済みの `src/ai-teammate/`（`llm.py` / `requirements.txt`）を同梱している。**接続情報（`.env`）を用意して疎通確認するだけ**でよい。

**1. `.env` を作る**（`<...>` を 2 節で控えた値に置換。`.env` はコミットしない）

```powershell
cd src/ai-teammate
Set-Content .env @"
AZURE_OPENAI_BASE_URL=https://<リソース名>.openai.azure.com/openai/v1/
AZURE_OPENAI_API_KEY=<キー>
AZURE_OPENAI_DEPLOYMENT=<デプロイ名>
"@
```

**2. ローカルで疎通確認**

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -c "import llm; print(llm.chat_complete('こんにちは、自己紹介して'))"
```

> `llm.py` は第1部C の `chat_complete()` 構造のまま、**OpenAI クライアントの `base_url` を Foundry の v1 エンドポイント（`.../openai/v1/`）に向けるだけ**（`api-version` 不要）。identity（独自 M365 ID）・ホスティング層・観測性は次の 4 節でスキルが生成・配線する。

## 4. AI Teammate 化する（Blueprint＋独自 M365 ID）

第1部C と同じ **スキル駆動**で進める。`src/ai-teammate` を開いた状態で、**AI チャット（GitHub Copilot は Agent モード）** に次を指示する：

```text
このエージェント（src/ai-teammate）を Agent 365 の AI Teammate にして。独自の M365 ID（UPN・メールボックス・Teams 在席）を持たせたい。
```

スキル（`a365-setup` → `make-ai-teammate`）が起動し、対話に沿って次を行う：

1. スタック検出 → capabilities で **AI Teammate** を選択（Register・Observability も自動同梱）
2. ホスティング層（Python は aiohttp）＋ `AgentApplication` ＋通知処理を生成
3. 内部で **`a365 setup all --aiteammate --m365`** を実行 → **Blueprint ＋ Agentic User（UPN 付き）＋ Agent ID** を払い出し（`--authmode` は使わない）

- 途中の `[y/N]` 承認・ブラウザ認証は画面の指示どおりに進める。
- **成功の判定**：`a365.generated.config.json` に `agentBlueprintId` が入り、Entra に **Agent Identity と 1:1 の User Account** が作られる。

> ⚠️ S2S との違い：ここでは **`--authmode` を付けない**。AI Teammate は自分の M365 ユーザー ID（agentic-user）で動くため。
> 出典: [AI teammate（get-started）](https://learn.microsoft.com/microsoft-agent-365/developer/get-started#ai-teammate)

## 5. 公開してインスタンスを作成する

AI Teammate は「**instance 作成**」まで行って初めて M365 で人として動く。スキルが以下を案内する：

1. **publish**：`a365 publish` で Teams/M365 パッケージを生成 → **M365 管理センターへアップロード（手動）**
2. **管理者承認**：管理センター **エージェント › すべてのエージェント › 要求** で承認
3. **インスタンス要求／作成**：AI Teammate は blueprint から **instance を作成**して初めて UPN・メールボックスが有効化される（管理センター主導）
4. **Teams への接続**：Notification URL 等の再確認（スキル／画面の指示に従う）

> 手順の一次情報: [Create an instance](https://learn.microsoft.com/microsoft-agent-365/developer/create-instance) ／ [Testing](https://learn.microsoft.com/microsoft-agent-365/developer/testing)
> ⚠️ 具体の画面・タブ名は Preview で変わり得るため、スキルの案内と上記 Learn を都度確認する。

## 6. "人として" 動作確認する

インスタンス有効化後、**第1部C の S2S エージェントとの違い**を体験する：

- **Teams で @mention** して会話する（S2S エージェントは Bot 的、AI Teammate は"人"として在席）
- **メールを送る**（AI Teammate は自分のメールボックスで受信・返信できる）
- **ディレクトリ／組織図**に載っていることを確認（マネージャー配下）

その後、[第2部](./part2-2-observe.md) の Observe / Govern / Secure で、**独自 ID エージェント**としての見え方（アクティビティ・ガバナンス・保護）を確認する。

---

← 戻る：[第3部 概要](./part3-0-overview.md) ｜ 次：**[3-B：自作 MCP サーバー（BYO MCP）](./part3-2-byo-mcp.md)**
