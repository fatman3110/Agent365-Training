# 第2部：Observe（観察する）｜AI 管理者

Agent 365 の 3 本柱の 1 つ目。一元レジストリで「組織にどんなエージェントがいて、何をしているか」を可視化する。

>**前提**：先に エージェントを動かして観測データを作っておくこと。一度も動かしていないと、この節の画面は何も表示されない。

> ⚠️ Microsoft Agent 365 / Copilot Studio は Preview を多く含む。UI 名やメニュー位置は変わり得るので、詰まったら Microsoft Learn で最新を確認すること。

**目次**

- [第2部：Observe（観察する）｜AI 管理者](#第2部observe観察するai-管理者)
  - [1. Agent Registry をタブ別に確認する](#1-agent-registry-をタブ別に確認する)
  - [2. Single Agent Map で可視化する（Preview）](#2-single-agent-map-で可視化するpreview)
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
> 組織設定「**レポートで、ユーザー、グループ、サイトの名前を非表示にする（Display concealed user, group, and site names in all reports）**」が有効だと、ユーザー名が MD5 ハッシュで匿名化される（**2021/9/1 以降は既定でオン**）。Single Agent Map もこの設定に従う。実名に戻すには、Global Administrator が [Microsoft 365 管理センター](https://admin.microsoft.com/) › **設定 › 組織設定 › サービス › レポート** で当該チェックを外して保存する（反映まで数分。M365／Teams の全レポートに一括で効くので他レポートも実名化される点に注意）。出典: [agent-map – Single Agent Map](https://learn.microsoft.com/microsoft-365/admin/manage/agent-map?view=o365-worldwide#single-agent-map-preview)、[使用状況レポートの実名表示](https://learn.microsoft.com/microsoft-365/admin/activity-reports/activity-reports?view=o365-worldwide#show-user,-group,-or-site-details-in-usage-reports)


## 3. 観測を 4 画面で追う（同じ Run を突き合わせる｜実践ラボ）

エージェントを動かして作った **1回の実行（Run）** が、Microsoft の複数ポータルに**同じもの**として記録されていることを、自分の手で追いかける。これが「見える化（Observe）」の実技。
参考: [a365handson Step 7 実習ラボ](https://github.com/ninjyanaka/a365handson/blob/main/07-observability-lab.md)

**追う順番**：(1) M365 管理センター（件数＝メトリクス）→ (2) Entra サインインログ（認証イベント＝ログ）→ (3) Purview（対話の中身）→ (4) Defender（KQL で横断照合＝実行トレース）
**必要ロール（閲覧）**：AI Reader（M365）／Reports Reader（Entra）／Content Viewer 相当（Purview）／Security Reader（Defender）

**(1) 発話して Run を1件つくる**（`echo`/`now` を1回呼び、**時刻と質問内容を控える**）

**(2) M365 管理センターで「件数」を確認（メトリクス）**

- [管理センター](https://admin.microsoft.com/) › **Agents › All agents › 対象 › Activity**
- 控えた時刻に近い行が**増えている**ことを確認（反映に数分かかることがある）
- ここで見えるのは「実行があった」という**メトリクス（件数）**。対話の中身は見えない（→ (4) Purview）

**(3) Entra サインインログで「認証イベント」を確認（ログ）**

- [Entra 管理センター](https://entra.microsoft.com/) › **Agents › Agent identities › 対象 › Activity › Sign-in logs**
- フィルタ **Is Agent = Yes**。控えた時刻付近のイベントを開き **Correlation ID** を控える
- 「何を話したか」ではなく「**いつ・どの ID として認証されたか**」のログ

**(4) Purview Activity explorer で「対話の中身」を確認**

- [Purview](https://purview.microsoft.com/) › **DSPM for AI（AI observability）› Activity explorer › AI activities**
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
