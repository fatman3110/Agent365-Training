# 第2部：Agent 365 ハンズオン（AI 管理者）

このパートは **AI 管理者**の作業。[第1部](./part1-setup.md)で作ったエージェントを、Microsoft の管理画面から **観察（Observe）→ 管理（Govern）→ 保護（Secure）** の 3 本柱で扱う。この 3 本柱は Microsoft Learn の [Agent 365 概要](https://learn.microsoft.com/ja-jp/microsoft-agent-365/overview) が定義する構成に沿う。

> ⚠️ Microsoft Agent 365 は Preview を多く含む。コマンド・API・UI は変わり得るので、詰まったら [Microsoft Learn](https://learn.microsoft.com/ja-jp/microsoft-agent-365/overview) で最新を確認すること。

3 本柱の全体像：

| 柱 | 目的（Learn） | 本パートの節 | 主な画面 |
|----|--------------|-------------|---------|
| **Observe（観察する）** | 一元レジストリで可視化し、使用状況・アクティビティ・正常性を把握。リスクシグナルを早期特定 | §3 | M365 管理センター |
| **Govern（管理）** | ライフサイクル管理・アクセス制御・コンプライアンスを一元化し、一貫したガードレールを確立 | §4 | M365 管理センター / Entra |
| **Secure（保護）** | Entra（リスクベースアクセス）・Purview（情報保護/DLP）・Defender（脅威防御）でエンドツーエンド保護 | §5 | Entra / Purview / Defender |

処理の順序は **①承認して管理下に置く（§1）→ ②実際に動かして観測データを作る（§2）→ ③観察（§3）→ ④管理（§4）→ ⑤保護（§5）**。まず承認して ID を実体化し、実際に動かさないと、観察も統制も保護も何も表示されない。

## 1. 承認して「管理下」に置く

エージェントは**承認されて初めて**利用可能になり、Agent ID が実体化して観察・統制・保護の対象になる。

### 1-1. エージェントを承認する（Requests → Publish）

1. [Microsoft 365 管理センター](https://admin.microsoft.com/) にサインイン
2. **Agents › All agents › Requests** を開く（`Pending review` / `Pending activate` を確認）
3. 対象エージェントを開く（この時点では **Entra agent ID は「—」**）→ **Publish to store**（承認）
4. 「**Publish new agent**」ウィザードを進める：
   1. **Select users** — インストール可能なユーザー（All users / 特定）を選択
   2. **Apply template** — ポリシーテンプレート。条件付きアクセス（例「Block - High Risky Agent」）等を適用（→ §5-2）
   3. **Review permissions** — エージェントが要求する権限を確認し、必要なら管理者同意
   4. **Review and finish → Publish**

<!-- ![Requests タブ](../assets/08-requests.png) -->

✅ 承認が完了するとエージェントは `Pending review` から外れ、利用可能になる。

### 1-2. 自作 MCP（道具）を承認する

エージェント本体（§1-1）とは**別の承認**が必要。第1部で登録申請した自作 MCP（`echo` / `now`）を、管理者が承認して初めてエージェントから呼べるようになる。

1. [Microsoft 365 管理センター](https://admin.microsoft.com/) › **Agents › Tools › Requests (preview)** を開く
2. 対象の MCP（第1部 §0 で決めた `$MCP` の表示名）を開く → **Approve**
3. 求められた管理者同意を付与する（`-A365Proxy` / `-BYO` / ランタイム用のアプリ登録に対する同意）
4. Status が **Available** に変われば承認完了（承認まではエージェントから呼び出せない）

<!-- ![Tools Requests](../assets/08b-tools-requests.png) -->

> **エージェント（§1-1）と MCP（§1-2）は別々に承認する**。両方を Approve して初めて、エージェントが道具を呼べる状態になる。

### 1-3. Teams / Copilot チャネルに接続する

承認しただけでは、まだ Teams からメッセージは届かない。**Teams 開発者ポータルで「宛先（Notification URL）」を設定**して、エージェントを Microsoft 365 のメッセージ基盤に繋ぐ。

1. 第1部で生成された `a365.generated.config.json` の `agentBlueprintId` をコピー
2. ブラウザで開く：`https://dev.teams.microsoft.com/tools/agent-blueprint/<agentBlueprintId>/configuration`
3. **Agent Type = API Based**、**Notification URL = messagingEndpoint**（`a365.generated.config.json` の値）を設定 → **Save**
4. Teams › **Apps** でエージェント名を検索 → **Request Instance / Add**。要求はテナント管理者の承認に回る（[管理センター Requested Agents](https://admin.cloud.microsoft/#/agents/all/requested)）
5. 承認後、Teams でエージェントとチャットできるようになる（→ §2 で実際に動かす）

出典: [Learn: エージェントインスタンスの作成](https://learn.microsoft.com/microsoft-agent-365/developer/create-instance)

<!-- ![Teams Developer Portal 設定](../assets/09-devportal.png) -->

> **AI Teammate との違い**：`@mention`・専用メールボックス・組織図掲載まで行う「AI Teammate」は **Frontier Preview 限定**（[Learn](https://learn.microsoft.com/microsoft-agent-365/developer/get-started#types-of-agents)）。本教材の非 AI Teammate エージェントは **API ベースの bot として Teams で会話**できるところまで。
> この blueprint の Entra agent ID（`agentBlueprintId`）が、そのまま Observability の `agentId` になる（Single Agent Map の突き合わせキー）。

## 2. エージェントを実際に動かす（観測データを作る）

**この節が §3 以降の前提**。Observe（§3）以降の画面は、エージェントを一度も動かしていないと**何も表示されない**。まずクラウド上のエージェントを実際に呼び出し、観測データ（Run）を作る。

### 2-1. エージェントに話しかける（Teams）

§1-3 で Teams に接続したエージェントに、**Teams のチャットで話しかける**（これが現実の利用チャネル）。

1. Teams › **Apps** で追加した自分のエージェントを開く
2. `echo こんにちは` や `今何時？`（`now`）などと送る
3. 応答が返れば、**受信（Teams→エージェント）と送信（エージェント→Teams）の両方**が通っている

> OBO（委任）なので、エージェントは**話しかけたユーザーの代理**として動く。監査ログにも「誰の代理か」が残る。
> 開発中のローカル確認だけなら、App Service の `/chat` に直接 REST してもよい：`curl -X POST "https://$APP.azurewebsites.net/chat" -H "Content-Type: application/json" -d '{"message":"echo hi"}'`（ただし Teams 経由と違い、観測のユーザー属性は付かない場合がある）。

### 2-2. 観測データを厚くするコツ

§3 の画面を見栄えよくするために、少し多めに動かしておく：

- `echo` / `now` を**複数回**呼ぶ → Map の **Tool ノード**が出る（呼ぶほど線が太い）
- **複数ユーザー**で叩く（OBO なので別ユーザーでサインイン）→ **User ノード**が増える
- （デモ映え）ツールを**一定確率で失敗**させ exception rate を **>1%** に → Map で**赤いハイライト線**

> **要件**：E7（Agent 365）＋ Global Administrator か AI Administrator。Usage / 観測はテナント **< 4,000 ユーザー**で有効。反映には数分〜十数分のタイムラグがある。

## 3. Observe（観察する）

一元レジストリで「組織にどんなエージェントがいて、何をしているか」を可視化する。§2 で作った観測データを、ここで確認する。

### 3-1. Agent Registry をタブ別に確認する

管理センター › **Agents › All agents › Registry** で対象を開き、各タブで「登録内容」を確認する。

| タブ | 見るもの |
|------|---------|
| **Details** | Publisher type / Owner / Entra agent ID / Channel |
| **Users** | 利用ユーザー |
| **Data & tools** | Capabilities / Knowledge / **Tools（BYO MCP の echo・now がここに出る）** |
| **Security** | Microsoft Purview（活動監視・機密データ保護）＋ Microsoft Entra（ID 保護・Agent ID）。右上に **Block** |
| **Permissions** | 付与権限（Granted / Delegated） |
| **Activity** | Active users / Sessions / Exceptions と時系列グラフ |

<!-- ![Registry タブ](../assets/10-registry.png) -->

### 3-2. Single Agent Map で可視化する（Preview）

観測データが、エージェント ↔ ユーザー ↔ ツールの関係図として描かれる。

1. 管理センター › **Agents › All Agents › Map**
2. **観測データを持つ**自分のエージェントを選択 → サマリ（users / sessions / exceptions）を確認
3. **All connections** を選択 → **Single Agent Map** が開く

| ノード | 内容 |
|--------|------|
| Agent | 詳細・サマリ活動 |
| User（top 50） | クリックでユーザー詳細 |
| Tool（top 50） | tool calls・exception 数・last activity（**echo / now** が出る） |

- **線の太さ** = interaction volume、**exception >1% の線は赤**
- 空表示なら §2（エージェントを動かす）と [第1部 §5](./part1-setup.md)（観測配線）を見直す

<!-- ![Single Agent Map](../assets/11-single-agent-map.png) -->

> Single Agent Map は「1 エージェント ↔ ユーザー ↔ ツール」に限定で、**agent-to-agent の線は描かれない**。マルチエージェント化は**テナント全体の Agent Map（クラスタ表示）**を豊かにする用途。

### 3-3. 観測を 4 画面で追う（同じ Run を突き合わせる｜実践ラボ）

§2 で作った **1回の実行（Run）** が、Microsoft の複数ポータルに**同じもの**として記録されていることを、自分の手で追いかける。これが「見える化（Observe）」の実技。
参考: [a365handson Step 7 実習ラボ](https://github.com/ninjyanaka/a365handson/blob/main/07-observability-lab.md)

**追う順番**：① M365 管理センター（件数＝メトリクス）→ ② Entra サインインログ（認証イベント＝ログ）→ ③ Purview（対話の中身）→ ④ Defender（KQL で横断照合＝実行トレース）
**必要ロール（閲覧）**：AI Reader（M365）／Reports Reader（Entra）／Content Viewer 相当（Purview）／Security Reader（Defender）

**① 発話して Run を1件つくる**（§2 の方法で `echo`/`now` を1回呼び、**時刻と質問内容を控える**）

**② M365 管理センターで「件数」を確認（メトリクス）**

- [管理センター](https://admin.microsoft.com/) › **Agents › All agents › 対象 › Activity**
- 控えた時刻に近い行が**増えている**ことを確認（反映に数分かかることがある）
- ここで見えるのは「実行があった」という**メトリクス（件数）**。対話の中身は見えない（→ ④ Purview）

**③ Entra サインインログで「認証イベント」を確認（ログ）**

- [Entra 管理センター](https://entra.microsoft.com/) › **Agents › Agent identities › 対象 › Activity › Sign-in logs**
- フィルタ **Is Agent = Yes**。控えた時刻付近のイベントを開き **Correlation ID** を控える
- 「何を話したか」ではなく「**いつ・どの ID として認証されたか**」のログ

**④ Purview Activity explorer で「対話の中身」を確認**

- [Purview](https://purview.microsoft.com/) › **DSPM for AI（AI observability）› Activity explorer › AI activities**
- Timestamp を控えた時刻付近に絞り、`Invoke Agent` / `Copilot Interaction` の行を開く
- **Prompt / Response** が ① の内容と一致することを確認（出ないなら Content Viewer 相当のロール不足を疑う）

**⑤ Defender Advanced Hunting で横断照合（実行トレース）**

- [Defender](https://security.microsoft.com/) › **Hunting › Advanced hunting**
- 直近の Agent 365 活動を一覧して `ConversationId` を1つ控える：

  ```kusto
  CloudAppEvents
  | where Timestamp > ago(1d)
  | where ActionType in ("InvokeAgent", "InferenceCall", "ExecuteToolBySDK", "ExecuteToolByGateway", "ExecuteToolByMCPServer")
  | extend AgentId = tostring(RawEventData.AgentId), ConversationId = tostring(RawEventData.ConversationId)
  | project Timestamp, ActionType, AgentId, ConversationId
  | order by Timestamp desc
  ```

- その `ConversationId` だけに絞り、実行順を確認：

  ```kusto
  CloudAppEvents
  | where tostring(RawEventData.ConversationId) == "<控えた ConversationId>"
  | project Timestamp, ActionType, RawEventData
  | order by Timestamp asc
  ```

- `InvokeAgent → InferenceCall →（あれば）ExecuteTool...` の時系列が **1 Run の実行トレース**。`summarize count() by ActionType` に変えれば呼び出し回数という**メトリクス**にもなる

✅ **Observe 完了条件**：同じ Run が 4 画面で同一エンティティ（時刻・`ConversationId`）として追える＝観測が効いている。

## 4. Govern（管理）

ライフサイクル管理と一貫したガードレール。**設定して終わりにせず、ログ・KQL で「効いた」ことを裏取り**する。
参考: [a365handson Step 8 実習ラボ](https://github.com/ninjyanaka/a365handson/blob/main/08-governance-lab.md)

### 4-1. 統制対象を棚卸しする（AgentsInfo を KQL で）

UI で名前を探すのではなく、**クエリで機械的に**レビュー対象を絞る。[Defender](https://security.microsoft.com/) › **Advanced hunting**：

```kusto
// 最新スナップショット（AgentsInfo は時系列なので arg_max で最新化）
AgentsInfo
| summarize arg_max(Timestamp, *) by AgentId
| where LifecycleStatus != "Deleted"
| project AgentName, Platform, Owners, SharedWith, PublishedStatus, LifecycleStatus
```

```kusto
// 所有者不在（ownerless）— 一括再割当の候補
AgentsInfo
| summarize arg_max(Timestamp, *) by AgentId
| where array_length(Owners) == 0
| project AgentName, Platform, PublishedStatus, LastUpdatedDateTime
```

> `Owners` / `Endpoints` / `DeclaredTools` は dynamic（JSON）列。ここで得た **高リスク／ownerless リスト**が §5-2（CA）や一括統制の入力になる。管理センター **Agents › Overview › Top actions for you › Manage agent risks** とも突き合わせる。

### 4-2. Block（Kill Switch）— 構成保持のまま即時停止

| 粒度 | 対象 | 効果 |
|------|------|------|
| **Blueprint 単位** | エージェント全体 | 組織全体で利用不可。全ユーザー・全 instance に波及 |
| **Instance 単位** | 個々の instance | その instance だけ停止。他は影響なし |

1. 管理センター › **Agents › All agents** で対象を開く（`Available`）→ 右上 **Block**
2. **Block agent** にチェック、任意で Reason を記入 → **Save**
3. ステータスが **Blocked** に。「removed from all users in your organization」。ボタンは **Unblock** に変化
4. 解除は **Unblock** → チェック → Save で `Available` に復帰

<!-- ![Block / Kill Switch](../assets/12-block.png) -->

> **ID 遮断 ≠ プロセス停止（重要）**：Block は「エージェント **ID としての認証**」を止める。出口（LLM/MCP 呼び出し）が **Agent ID トークン（`fmi_path`）** 依存なら egress も止まり応答生成が失敗する（＝キルスイッチ成立）。出口が SAMI/UAMI のままだと **ID は止まってもプロセスは動き続ける** → 完全停止はホスト側（App Service を停止、または Container Apps の操作）が必要。
>
> **検証**：Block 後にエージェントを呼ぶ → Entra **サインインログに Failure** が出ることを確認。詳細の **Status / Conditional access / Failure reason** で「どのポリシーで止まったか」を特定する。

### 4-3. 削除（リタイア）と後片付け

| | Block（無効化） | Permanent delete（削除） |
|--|----------------|--------------------------|
| 何が起きる | 認証・トークン発行を止める。オブジェクトは残る | オブジェクトを消す（子も連鎖削除） |
| 構成・データ | 保持（Unblock で復帰） | 失われる（30 日は論理削除で復元可） |
| クォータ | 消費したまま | 完全削除まで消費（250 上限に注意） |

- 個別: instance 詳細 › **Permanent delete**
- 一括（自前ホスト）: 作業ディレクトリで `a365 cleanup`（**破壊的**。config の blueprint 配下を一括削除）
- orphan アプリ確認: `az ad app list --display-name "<blueprint名>" -o table` → `az ad app delete --id <appId>`

> ⚠️ **後片づけ必須**：学習が終わったら Block ではなく `a365 cleanup` で消し、Azure リソース（App Service / Functions / ACR / ストレージ、まとめて `az group delete -n $RG`）も削除する。連鎖クリーンアップは非同期で数時間〜数日かかることがある。
> **削除後の確認**：§4-1 の `AgentsInfo` KQL で `LifecycleStatus == "Deleted"` に遷移したことを確認（反映にタイムラグあり）。

### 4-4. ガードレールの限界（Agent ID が無いと統制は効かない）

「**見えること ≠ 統制できること**」を体験しておく。

- **Agent ID を主体に持たない**エンティティ（レジストリ同期のみ／素の Entra アプリ登録）は、**一覧には見えても CA の主体にならず統制できない**
- サインインログで、そのエンティティが `Is Agent = No` として扱われることを確認

> これは「**まず観察（Observe）→ Agent ID 発行 → 統制（Govern）**」という順序の必然性を示す。可視化だけでは統制は成立しない。統制には Agent ID の発行（§1）が前提。

✅ **Govern 完了条件**：Block → 実際に停止（サインイン Failure）、Unblock → 復帰、を確認。`AgentsInfo` で対象を機械抽出できる。

## 5. Secure（保護）

Learn の Secure は、**Entra（リスクベースのアクセス制御）・Purview（情報保護 / DLP）・Defender（脅威防御）** の 3 面でエージェントをエンドツーエンドに守る。

| 保護面 | 役割 | 本節 |
|--------|------|------|
| **Microsoft Entra** | ユーザー／エージェントに一貫したリスクベースのアクセス制御（Agent risk による Block 等） | §5-2 |
| **Microsoft Purview** | 情報保護・DLP・リスクセーフガードで機密データ露出を防ぐ | §5-3 |
| **Microsoft Defender** | エージェント活動の脅威検出・調査・対応（Advanced Hunting） | §5-4 |

### 5-1. 全体像

Observe（§3）が「見る」、Govern（§4）が「ライフサイクルを止める／消す」なら、Secure（§5）は「**リスクに応じて自動で守る**」。同じ Entra / Purview / Defender の画面を、ここでは**保護（ポリシー適用・データ保護・脅威検出）**の観点で使う。

### 5-2. 条件付きアクセス — Agent risk = High を Block（Report-only → On）

Entra の条件付きアクセス（CA）で「**すべてのエージェント ID**」を対象に、**Agent risk = High**（Preview）のときトークン発行をブロックする。リスクベースの自動遮断が Secure の中核。**いきなり On にせず、まず Report-only で影響を確認**してから有効化するのが定石。

1. [Entra 管理センター](https://entra.microsoft.com/) › **Protection › Conditional Access** で新規ポリシー作成
2. 次のように構成（例「Block - High Risky Agent」に対応）：

   | 設定 | 値 |
   |------|----|
   | Users / Target | **All agent identities**（対象＝エージェント ID） |
   | Target resources | All agent resources |
   | Conditions | **Agent risk (Preview) = High** |
   | Grant | **Block access** |
   | Enable policy | **Report-only** で作成 |

3. Report-only のまま対象エージェントを数回動かす
4. **Sign-in logs › Service principal sign-ins** で対象を開き、詳細の **Conditional Access** タブが **「Report-only: Would block」** と評価されていることを確認
5. 影響が想定内なら、ポリシーを **On** に切り替える → 以後は実際に Block される

> **CA の対象化・属性適用には Global Administrator が必要**（AI Administrator では不足）。CA の対象化には Entra ID **P1/P2 ＋ ユーザーごとの Agent 365 ライセンス**も要る。
> 出典: [エージェント向け条件付きアクセス](https://learn.microsoft.com/entra/identity/conditional-access/agent-id)

### 5-3. Purview — 機密データの保護（情報保護 / DLP）

§3-3 で Purview を**観察**（Prompt/Response を読む）に使ったが、Secure では**保護**に使う。エージェントが機密データを扱う／外部へ出す動きを、情報保護ラベル・DLP・リスクセーフガードで抑止する。

- [Purview](https://purview.microsoft.com/) › **DSPM for AI** で、エージェントの AI アクティビティに含まれる機密情報の種類・件数を把握
- DLP ポリシーで、機密ラベル付きデータのプロンプト送信やツール経由の持ち出しを制限
- 詳細: [Purview DSPM for AI](https://learn.microsoft.com/purview/ai-microsoft-purview)

> 本教材の `echo` / `now` は機密データを扱わないため DLP は発火しにくい。ここでは「**どこで機密保護をかけるか**」の位置づけを掴めば十分。

### 5-4. Defender — 脅威検出と調査（Advanced Hunting）

Defender はエージェント活動を**脅威防御**の観点で監視する。§3-3 / §4-1 で使った `CloudAppEvents` / `AgentsInfo` は、そのまま**不審な振る舞いの検出**にも使える。

```kusto
// 例：短時間に大量のツール呼び出し／高い失敗率のエージェントを洗い出す
CloudAppEvents
| where Timestamp > ago(1d)
| where ActionType startswith "ExecuteTool"
| summarize Calls = count(), Fails = countif(RawEventData.Success == false) by AgentId = tostring(RawEventData.AgentId)
| extend FailRate = round(1.0 * Fails / Calls, 3)
| where Calls > 100 or FailRate > 0.1
| order by Calls desc
```

- 高リスク該当は §4-1 の棚卸し・§5-2 の CA（Agent risk）へフィードバックする
- 詳細: [Defender Advanced Hunting（AgentsInfo テーブル）](https://learn.microsoft.com/defender-xdr/advanced-hunting-agentsinfo-table)

✅ **Secure 完了条件**：CA を Report-only で「Would block」までログ確認。Purview / Defender でエージェントのデータ・脅威面を見る場所を把握。

---

← 戻る：**[第1部：環境構築](./part1-setup.md)** ｜ [README（概要）](../README.MD)
