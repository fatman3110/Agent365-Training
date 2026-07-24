# 第2部：Agent 365 ハンズオン（AI 管理者）

> このパートは **AI 管理者**の作業。[Microsoft 365 管理センター](https://admin.microsoft.com/)（Copilot Control System）と [Microsoft Entra 管理センター](https://entra.microsoft.com/) で、[第1部](./part1-setup.md)で作った内容を確認し、**観測を4画面で追い、ガバナンスが「効いていること」をログ／KQL で検証**する。
> 参考: [a365handson Step 4（登録）](https://github.com/ninjyanaka/a365handson/blob/main/04-register.md) ｜ [Step 7 実習ラボ（観測）](https://github.com/ninjyanaka/a365handson/blob/main/07-observability-lab.md) ｜ [Step 8 実習ラボ（ガバナンス）](https://github.com/ninjyanaka/a365handson/blob/main/08-governance-lab.md)
>
> ⚠️ Agent 365 は Preview を多く含みます（Agent risk 条件・Single Agent Map・ラベル配置など）。UI 名や提供条件は変わり得るので、詰まったら各節のリンク先で最新を確認してください。

## 1. 管理者が承認する（Requests → Publish）

エージェントは承認されて初めて利用可能になる。

1. [Microsoft 365 管理センター](https://admin.microsoft.com/) にサインイン
2. **Agents › All agents › Requests** を開く（`Pending review` / `Pending activate` を確認）
3. 対象エージェントを開く（この時点では **Entra agent ID は「—」**）→ **Publish to store**（承認）
4. 「**Publish new agent**」ウィザードを進める：
   1. **Select users** — インストール可能なユーザー（All users / 特定）を選択
   2. **Apply template** — ポリシーテンプレート。条件付きアクセス（例「Block - High Risky Agent」）等を適用（→ §6）
   3. **Review permissions** — エージェントが要求する権限を確認し、必要なら管理者同意
   4. **Review and finish → Publish**

<!-- ![Requests タブ](../assets/08-requests.png) -->

> **BYO MCP の承認も同様**：**Agents › Tools › Requests (preview)** で `<MCP_NAME>` を開き **Approve** →（`-A365Proxy` / `-BYO` / ランタイムの）管理者同意 → Status が **Available**（承認まで利用不可）。

✅ 承認が完了するとエージェントは `Pending review` から外れ、利用可能になる。

## 2. Entra Agent ID を確認する

承認済みの blueprint を「使える実体」にすると（instance 化）、**Entra Agent ID が「—」から実値の GUID に変わる**。

1. 管理センター › **Agents** で対象 blueprint を開く → **`+ Add instance`**（または対象の登録を有効化）
2. 作成後、blueprint / instance の **Overview の Entra agent ID** が実値化することを確認
3. [Entra 管理センター](https://entra.microsoft.com/) › **Agent identities**（Enterprise apps）で同じ Agent ID が見えることを確認

<!-- ![Entra Agent ID 実値化](../assets/09-agentid.png) -->

> **本教材は非 AI Teammate** のため、**agent user（UPN）や Teams の `@mention` は作られない**（それは AI Teammate 専用）。本エージェントの呼び出しは Copilot Studio カスタムエンジン / REST（App Service の `/chat`）/ OBO クライアント経由で行う。
> この Entra agent ID の値が、そのまま Observability の `agentId` になる（Single Agent Map の突き合わせキー）。

## 3. Agent Registry をタブ別に確認する

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

## 4. Single Agent Map で可視化する（Preview）

観測データが、エージェント ↔ ユーザー ↔ ツールの関係図として描かれる。**Map を点灯させるには、クラウド上のエージェントを実際に呼び出して活動を作る**必要がある。

### 4.0 Map 点灯用のアクティビティを作る（クラウドのエージェントを呼ぶ）

承認済み（§1）のエージェントを、クラウド経由で実際に使って観測データを溜める：

- `echo` / `now` を**複数回**呼ぶ → Map の **Tool ノード**が出る（呼ぶほど線が太い）
- **複数ユーザー**で叩く（OBO なので別ユーザーでサインイン）→ **User ノード**が増える
- （デモ映え）ツールを**一定確率で失敗**させ exception rate を **>1%** に → Map で**赤いハイライト線**
- 呼び出し方法：Copilot Studio カスタムエンジン / REST（App Service の `/chat`）/ OBO クライアント

**要件**：E7（Agent 365）＋ Global Administrator か AI Administrator。Usage/観測はテナント **< 4,000 ユーザー**で有効。

1. 管理センター › **Agents › All Agents › Map**
2. **観測データを持つ**自分のエージェントを選択 → サマリ（users / sessions / exceptions）を確認
3. **All connections** を選択 → **Single Agent Map** が開く

| ノード | 内容 |
|--------|------|
| Agent | 詳細・サマリ活動 |
| User（top 50） | クリックでユーザー詳細 |
| Tool（top 50） | tool calls・exception 数・last activity（**echo / now** が出る） |

- **線の太さ** = interaction volume、**exception >1% の線は赤**
- 空表示なら [第1部 §5](./part1-setup.md)（観測配線）と §4.0（アクティビティ生成）を見直す

<!-- ![Single Agent Map](../assets/11-single-agent-map.png) -->

> Single Agent Map は「1 エージェント ↔ ユーザー ↔ ツール」に限定で、**agent-to-agent の線は描かれない**。マルチエージェント化は**テナント全体の Agent Map（クラスタ表示）**を豊かにする用途。

## 5. 観測を4画面で追う（同じ Run を突き合わせる｜実践ラボ）

§4 で活動を作ったら、その **1回の実行（Run）** が Microsoft の複数ポータルに**同じもの**として記録されていることを、自分の手で追いかける。ここが「見える化（Observe）」の実技。
> 参考: [a365handson Step 7 実習ラボ](https://github.com/ninjyanaka/a365handson/blob/main/07-observability-lab.md)

**追う順番**：① M365 管理センター（件数＝メトリクス）→ ② Entra サインインログ（認証イベント＝ログ）→ ③ Purview（対話の中身）→ ④ Defender（KQL で横断照合＝実行トレース）

**必要ロール（閲覧）**：AI Reader（M365）／Reports Reader（Entra）／Content Viewer 相当（Purview）／Security Reader（Defender）

### 5.1 発話して Run を1件つくる

- §4.0 の方法でエージェントを **1回** 呼ぶ（`echo`/`now` のように**ツール呼び出しを伴う**質問だと後段が見やすい）
- **時刻と質問内容を控える**（後の画面で行を探す手がかりになる）

### 5.2 M365 管理センターで「件数」を確認（メトリクス）

1. [管理センター](https://admin.microsoft.com/) › **Agents › All agents › 対象 › Activity**
2. §5.1 で控えた時刻に近い行が**増えている**ことを確認（反映に数分かかることがある）

> ここで見えるのは「実行があった」という**メトリクス（件数）**。対話の中身は見えない（→ 5.4 Purview）。

### 5.3 Entra サインインログで「認証イベント」を確認（ログ）

1. [Entra 管理センター](https://entra.microsoft.com/) › **Agents › Agent identities › 対象 › Activity › Sign-in logs**
2. フィルタ **Is Agent = Yes**。控えた時刻付近のイベントを開き **Correlation ID** を控える

> 「何を話したか」ではなく「**いつ・どの ID として認証されたか**」のログ。

### 5.4 Purview Activity explorer で「対話の中身」を確認

1. [Purview](https://purview.microsoft.com/) › **DSPM for AI（AI observability）› Activity explorer › AI activities**
2. Timestamp を控えた時刻付近に絞り、`Invoke Agent` / `Copilot Interaction` の行を開く
3. **Prompt / Response** が §5.1 の内容と一致することを確認

> Prompt/Response が出ないなら **Content Viewer 相当のロール不足**を疑う。

### 5.5 Defender Advanced Hunting で横断照合（実行トレース）

1. [Defender](https://security.microsoft.com/) › **Hunting › Advanced hunting**
2. 直近の Agent 365 活動を一覧して `ConversationId` を1つ控える：

   ```kusto
   CloudAppEvents
   | where Timestamp > ago(1d)
   | where ActionType in ("InvokeAgent", "InferenceCall", "ExecuteToolBySDK", "ExecuteToolByGateway", "ExecuteToolByMCPServer")
   | extend AgentId = tostring(RawEventData.AgentId), ConversationId = tostring(RawEventData.ConversationId)
   | project Timestamp, ActionType, AgentId, ConversationId
   | order by Timestamp desc
   ```

3. その `ConversationId` だけに絞り、実行順を確認：

   ```kusto
   CloudAppEvents
   | where tostring(RawEventData.ConversationId) == "<控えた ConversationId>"
   | project Timestamp, ActionType, RawEventData
   | order by Timestamp asc
   ```

> `InvokeAgent → InferenceCall →（あれば）ExecuteTool...` の時系列が **1 Run の実行トレース**。`summarize count() by ActionType` に変えれば呼び出し回数という**メトリクス**にもなる。

✅ **完了条件**：同じ Run が 4画面で同一エンティティ（時刻・`ConversationId`）として追える＝観測が効いている。

## 6. ガバナンスを検証する — 棚卸し / Block / 条件付きアクセス / 削除

ガバナンスは **「見える化 → ルールで統制 → 効いていることを検証」** のループ。設定して終わりにせず、**ログ・KQL で「効いた」ことを裏取り**する。
> 参考: [a365handson Step 8 実習ラボ](https://github.com/ninjyanaka/a365handson/blob/main/08-governance-lab.md)

### 6.0 統制対象を棚卸しする（AgentsInfo を KQL で）

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

> `Owners` / `Endpoints` / `DeclaredTools` は dynamic（JSON）列。ここで得た **高リスク／ownerless リスト**が 6.2（CA）や一括統制の入力になる。管理センター **Agents › Overview › Top actions for you › Manage agent risks** とも突き合わせる。

### 6.1 Block（Kill Switch）— 構成保持のまま即時停止

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

### 6.2 条件付きアクセス（Report-only → On で検証）

さらに広く止めるなら Entra の条件付きアクセス（CA）で「**すべてのエージェント ID**」を対象にトークン発行をブロックできる（既存・新規の Agent ID をまとめて認証不可）。**いきなり On にせず、まず Report-only で影響を確認**してから有効化するのが定石。

1. [Entra 管理センター](https://entra.microsoft.com/) › **Protection › Conditional Access** で新規ポリシー作成
2. 次のように構成（本編の例「Block - High Risky Agent」に対応）：

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

### 6.3 削除（リタイア）と後片付け

| | Block（無効化） | Permanent delete（削除） |
|--|----------------|--------------------------|
| 何が起きる | 認証・トークン発行を止める。オブジェクトは残る | オブジェクトを消す（子も連鎖削除） |
| 構成・データ | 保持（Unblock で復帰） | 失われる（30 日は論理削除で復元可） |
| クォータ | 消費したまま | 完全削除まで消費（250 上限に注意） |

- 個別: instance 詳細 › **Permanent delete**
- 一括（自前ホスト）: 作業ディレクトリで `a365 cleanup`（**破壊的**。config の blueprint 配下を一括削除）
- orphan アプリ確認: `az ad app list --display-name "<blueprint名>" -o table` → `az ad app delete --id <appId>`

> ⚠️ **後片づけ必須**：学習が終わったら Block ではなく `a365 cleanup` で消し、Azure リソース（App Service / Functions / ACR / ストレージ、まとめて `az group delete -n $RG`）も削除する。連鎖クリーンアップは非同期で数時間〜数日かかることがある。
> **削除後の確認**：6.0 の `AgentsInfo` KQL で `LifecycleStatus == "Deleted"` に遷移したことを確認（反映にタイムラグあり）。

### 6.4 ガードレールの限界（Agent ID が無いと CA は効かない）

最後に「**見えること ≠ 統制できること**」を体験しておく。

- **Agent ID を主体に持たない**エンティティ（レジストリ同期のみ／素の Entra アプリ登録）は、**一覧には見えても CA の主体にならず統制できない**
- サインインログで、そのエンティティが `Is Agent = No` として扱われることを確認

> これは「**まず見える化（Observe）→ Agent ID 発行 → 統制（Govern）**」という順序の必然性を示す。可視化だけでは統制は成立しない。統制には Agent ID の発行（§1〜§2）が前提。

✅ **完了条件**：Block → 実際に停止（サインイン Failure）、Unblock → 復帰、を確認。CA を Report-only で「Would block」までログ確認。Single Agent Map に自分の agent・Tool（echo/now）・User が描画される。

---

← 戻る：**[第1部：環境構築](./part1-setup.md)** ｜ [README（概要）](../README.MD)
