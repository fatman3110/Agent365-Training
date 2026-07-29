# 第3部 A：AI Teammate を作る（開発者）

**独自の M365 ユーザー ID（UPN・メールボックス・Teams 在席・組織図エントリ）を持つ AI Teammate** を作る。頭脳は **Microsoft Foundry のクラウドモデル**を直接呼ぶ（第1部C の自前 Qwen とは異なり、Ollama/Docker は不要）。

第1部C の **S2S エージェント**は「アプリとして」動いたが、AI Teammate は **"人"としてふるまう**（@mention・メール・会議招待で対話できる）。

> ⚠️ **Frontier preview 必須**：AI Teammate は **[Frontier program](https://adoption.microsoft.com/copilot/frontier-program/) 登録済みテナント限定**。未登録の場合は本章は「読み物」に留め、[3-B（自作 MCP）](./part3-2-byo-mcp.md) へ進む。
> 出典: [Get started with Agent 365 development](https://learn.microsoft.com/microsoft-agent-365/developer/get-started)

> ⚠️ Preview を多く含む。コマンド・UI・提供リージョンは変わり得るので Microsoft Learn で最新を確認すること。

**目次**

- [第3部 A：AI Teammate を作る（開発者）](#第3部-aai-teammate-を作る開発者)
  - [0. 名前を決める](#0-名前を決める)
  - [1. 前提を確認する](#1-前提を確認する)
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

## 1. 前提を確認する

| 項目 | 要件 |
|------|------|
| Frontier | **登録済みテナント**（未登録だと AI Teammate 不可） |
| ライセンス | E7 / Agent 365、Teams |
| Entra ロール | **Global Administrator**（全工程）または **Agent ID Developer**（OAuth2 付与は GA へハンドオフ） |
| ツール | 第1部 1 節と同じ（`node` / `az` / `a365` / `m365agentstoolkit-cli`）＋ Python 3.11+ |
| AI コーディングアシスタント | GitHub Copilot（**Agent モード**）または Claude Code。Agent 365 Skills 導入済み（第1部C 2 節） |

> 出典（ロール要件）: [AI-guided setup prerequisites](https://learn.microsoft.com/microsoft-agent-365/developer/get-started#ai-guided-setup-prerequisites)

サインインは第1部と同様、**`az login` と Teams Toolkit の M365 サインインを同じテナントに揃える**。

```powershell
az login
m365agentstoolkit-cli account login m365
m365agentstoolkit-cli account show   # az account show と同じテナントか確認
```

## 2. Foundry でモデルをデプロイする（頭脳）

AI Teammate の思考エンジンに使うモデルを Foundry にデプロイし、**エンドポイントとキー**を控える。

1. [Foundry ポータル](https://ai.azure.com/) にサインイン（第1部B で作成済みのプロジェクトを再利用してよい）
2. プロジェクトを開き、**モデル + エンドポイント**（モデルカタログ）から `gpt-4o-mini` 等をデプロイ
3. デプロイの詳細画面で以下を控える：
   - **ターゲット URI（エンドポイント）**
   - **キー**
   - **デプロイ名**（`OLLAMA_MODEL` の代わりに使う）

> テスト用途なので小型モデル（`gpt-4o-mini` 等）で十分。第1部C の「自前 Qwen」を「Foundry モデル」に置き換えるだけ。

## 3. エージェント本体（src/ai-teammate）を用意する

既存 `src/agent/` はコピー元として**読み取りのみ**。新規に `src/ai-teammate/` を作り、**LLM 呼び出しを Foundry モデルに向ける**。

1. `src/ai-teammate/` を作成し、最小構成（`app.py` / `llm.py` / `requirements.txt` 等）を置く。
2. `.env` にモデル接続情報を記述（キーはコミットしない）：
   ```text
   AZURE_OPENAI_ENDPOINT=<手順2で控えたターゲット URI>
   AZURE_OPENAI_API_KEY=<手順2で控えたキー>
   AZURE_OPENAI_DEPLOYMENT=<手順2で控えたデプロイ名>
   ```
3. `llm.py` は **OpenAI SDK 互換**で Foundry モデルを呼ぶだけのシンプルな chat completion にする（第1部C の Ollama 版と同じ構造で、接続先を Foundry に変えるだけ）。

> ここでは「動く agent プロジェクト」があれば十分。identity・ホスティング層・観測性は次の 4 節でスキルが生成する。

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
