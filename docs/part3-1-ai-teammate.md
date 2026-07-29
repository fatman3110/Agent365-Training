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

AI Teammate の思考エンジンに使うモデルを Foundry にデプロイし、**エンドポイント・キー・デプロイ名**を控える。

1. [Foundry ポータル](https://ai.azure.com/) にサインイン（第1部B で作成済みのプロジェクトを再利用してよい）
2. 左ペインの **マイアセット（My assets）› モデル + エンドポイント（Models + endpoints）** を開く
3. **＋ モデルのデプロイ（Deploy model）› 基本モデルをデプロイ（Deploy base model）** を選ぶ
4. モデル一覧から `gpt-4o-mini`（テスト用途なら十分）を選び **確認（Confirm）**
5. デプロイ構成で次を設定：
   | 項目 | 値 |
   |------|----|
   | **デプロイ名（Deployment name）** | 例 `gpt-4o-mini`（**コードで使う名前**。任意に決めてよい） |
   | **デプロイの種類（Deployment type）** | `Global Standard` 等（テスト用途はそのままで可） |
   | （任意）レート制限（TPM）／コンテンツフィルター | 既定のままで可 |
6. **デプロイ（Deploy）** を押し、**プロビジョニング状態（Provisioning state）が「Succeeded（成功）」** になるまで待つ
7. デプロイ詳細画面で以下を控える（次節の `.env` に使う）：
   - **ターゲット URI（Target URI）＝エンドポイント**（`https://<リソース名>.openai.azure.com/` 形式。末尾の `/openai/deployments/...` は含めずベース URL を使う）
   - **キー（Key）**
   - **デプロイ名（Deployment name）**（手順5で決めた名前）
   - **API バージョン**（OpenAI SDK 互換で呼ぶ場合に必要。例 `2024-10-21`）

> 出典（Foundry でのモデルデプロイ手順）: [Deploy a model（Azure OpenAI in Foundry）](https://learn.microsoft.com/azure/ai-foundry/openai/how-to/create-resource#deploy-a-model)
> ⚠️ UI 名称・既定値は Preview で変わり得るため、画面表示と上記 Learn を都度確認する。

## 3. エージェント本体（src/ai-teammate）を用意する

既存 `src/agent/`（第1部C）はコピー元として**読み取りのみ**。新規に `src/ai-teammate/` を作り、**LLM 呼び出しを Foundry モデルに向ける**（Ollama → Foundry の差し替えが本質）。

1. `src/ai-teammate/` を作成（最小構成）。ホスティング層・`AgentApplication`・観測性は **4 節でスキルが生成**するので、ここでは LLM コアだけ置く：
   ```text
   src/ai-teammate/
   ├── llm.py            # Foundry モデルを呼ぶ chat completion（Ollama→Foundry の差分はここだけ）
   ├── requirements.txt
   └── .env              # 接続情報（コミット禁止）
   ```

2. `requirements.txt`（最小。ホスティング／観測性の依存は 4 節でスキルが追記）：
   ```text
   openai>=1.0
   python-dotenv>=1.0
   ```

3. `.env`（第1部C の `OLLAMA_*` を Foundry 用に置き換え。値は 2 節で控えたもの。キーはコミットしない）：
   ```text
   AZURE_OPENAI_ENDPOINT=https://<リソース名>.openai.azure.com/
   AZURE_OPENAI_API_KEY=<2節で控えたキー>
   AZURE_OPENAI_DEPLOYMENT=<2節で控えたデプロイ名>
   AZURE_OPENAI_API_VERSION=2024-10-21
   ```

4. `llm.py`（第1部C の Ollama 版と**同じ「ツール無しのシンプル chat completion」構造**。接続先を Foundry に変えるだけ。関数名は第1部C の `llm.py` に合わせる）：
   ```python
   import os
   from openai import AzureOpenAI
   from dotenv import load_dotenv

   load_dotenv()

   _client = AzureOpenAI(
       azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
       api_key=os.environ["AZURE_OPENAI_API_KEY"],
       api_version=os.environ["AZURE_OPENAI_API_VERSION"],
   )
   _DEPLOYMENT = os.environ["AZURE_OPENAI_DEPLOYMENT"]

   def ask(prompt: str) -> str:
       """ユーザーの発話を Foundry モデルに投げ、テキスト応答を返す（ツール呼び出しなし）。"""
       resp = _client.chat.completions.create(
           model=_DEPLOYMENT,          # Azure はモデル名ではなく「デプロイ名」を渡す
           messages=[{"role": "user", "content": prompt}],
       )
       return resp.choices[0].message.content or ""
   ```

5. ローカルで疎通確認（任意）：
   ```powershell
   cd src/ai-teammate
   pip install -r requirements.txt
   python -c "import llm; print(llm.ask('こんにちは、自己紹介して'))"
   ```

> ここまでで「**Foundry モデルで応答する最小エージェント**」が完成。identity（独自 M365 ID）・ホスティング層・観測性は次の 4 節でスキルが生成・配線する。

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
