# 第2部：Observe（観察する）｜AI 管理者

Agent 365 の 3 本柱の 1 つ目。一元レジストリで「組織にどんなエージェントがいて、何をしているか」を可視化する。

>**前提**：先に エージェントを動かして観測データを作っておくこと。一度も動かしていないと、この節の画面は何も表示されない。

> ⚠️ Microsoft Agent 365 / Copilot Studio は Preview を多く含む。UI 名やメニュー位置は変わり得るので、詰まったら Microsoft Learn で最新を確認すること。

**目次**

- [第2部：Observe（観察する）｜AI 管理者](#第2部observe観察するai-管理者)
  - [1. Agent Registry をタブ別に確認する](#1-agent-registry-をタブ別に確認する)
  - [2. Single Agent Map で可視化する](#2-single-agent-map-で可視化する)
  - [3. 観測を 4 画面で追う（同じ Run を突き合わせる｜実践ラボ）](#3-観測を-4-画面で追う同じ-run-を突き合わせる実践ラボ)

## 1. Agent Registry をタブ別に確認する

管理センター › **Agents › All agents › Registry** で対象を開き、組織に存在する AI エージェントを確認する。

| タブ | 見るもの |
|------|---------|
| **Details** | Publisher type / Owner / Entra agent ID / Channel |
| **Users** | 利用ユーザー |
| **Data & tools** | Capabilities / Knowledge / Tools（利用している MCP はここに表示される） |
| **Security** | Microsoft Purview（活動監視・機密データ保護）＋ Microsoft Entra（ID 保護・Agent ID）。右上に **Block** |
| **Permissions** | 付与権限（Granted / Delegated） |
| **Activity** | Active users / Sessions / Exceptions と時系列グラフ |

## 2. Single Agent Map で可視化する

観測データが、ツール ↔ エージェント ↔ ユーザー の関係図として描かれる。

1. 管理センター › **Agents › All Agents › Map**
2. **観測データを持つ**自分のエージェントを選択 
3. **All connections** を選択 → **Single Agent Map** が開く

> **User 名がハッシュ文字列で匿名化される場合**
> 組織設定「**レポートで、ユーザー、グループ、サイトの名前を非表示にする**」が有効だと、ユーザー名が MD5 ハッシュで匿名化される。実名に戻すには、Global Administrator が [Microsoft 365 管理センター](https://admin.microsoft.com/) › **設定 › 組織設定 › サービス › レポート** で当該チェックを外して保存


## 3. アクティビティを複数のツールから確認

エージェントの動作記録は、複数ポータルにそれぞれの側面で記録される。これによって、 IT 管理者やセキュリティ管理者等、役割の異なる担当者が自分の慣れたツールで運用を行うことを支援する。

**本トレーニングでの確認順**：(1) M365 管理センター（件数＝メトリクス）→ (2) Entra サインインログ（認証イベント＝ログ）→ (3) Purview（対話の中身）→ (4) Defender（KQL で横断照合＝実行トレース）

**(1) M365 管理センターで「件数」を確認（メトリクス）**

- [管理センター](https://admin.microsoft.com/) › **Agents › All agents › 対象 › Activity**
- ここで見えるのは「実行があった」という**メトリクス（件数）**。対話の中身は見えない
  
**(2) Entra サインインログで「認証イベント」を確認（ログ）**

- [Entra 管理センター](https://entra.microsoft.com/) › **Entra ID › Agents › Agent identities › 対象 › Activity › Sign-in logs**
- 「何を話したか」ではなく「**いつ・どの ID として認証されたか**」のログ
- エージェントが**ユーザーに代わって（委任）**動いた実行では、**どのユーザーのために動いたか**（対象ユーザー）も記録される。つまり「誰が使ったか」まで追える。一方、エージェントが**自身の ID で（自律）**動いた実行にはユーザーが紐づかず、エージェント ID 自身の認証として記録される（出典: [What are agent identities – Delegated access](https://learn.microsoft.com/entra/agent-id/what-are-agent-identities#what-agent-identities-enable)、[Agent 365 Identity – 認証フロー](https://learn.microsoft.com/microsoft-agent-365/developer/identity#authentication-flows)）

**(3) Purview Activity explorer で「対話の中身」を確認**

- [Purview](https://purview.microsoft.com/) › **DSPM › 発見 › アクティビティエクスプローラー › AI あくてぃびてｌ**
- Timestamp を控えた時刻付近に絞り、`Invoke Agent` / `Copilot Interaction` の行を開く
- **Prompt / Response** が (1) の内容と一致することを確認（出ないなら Content Viewer 相当のロール不足を疑う）

**(5) Defender Advanced Hunting で横断照合（実行トレース）**

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

---

← 戻る：**[第2部 B：承認と観測データ作成](./part2-1b-custom.md)** ｜ 次：**[第2部：Govern（管理）](./part2-3-govern.md)** ｜ [README（概要）](../README.MD)
