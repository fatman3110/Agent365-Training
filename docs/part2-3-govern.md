# 第2部：Govern（管理）｜AI 管理者

Agent 365 の 3 本柱の 2 つ目。ライフサイクル管理と一貫したガードレール。**設定して終わりにせず、ログ・KQL で「効いた」ことを裏取り**する。
参考: [a365handson Step 8 実習ラボ](https://github.com/ninjyanaka/a365handson/blob/main/08-governance-lab.md)

> ▶ **前提**：[第2部 A](./part2-1a-copilotstudio.md) / [B](./part2-1b-custom.md) で承認済み、[Observe](./part2-2-observe.md) で可視化を確認済みであること。
>
> ⚠️ Microsoft Agent 365 は Preview を多く含む（Agent risk 条件など）。UI・提供条件は変わり得る。

**目次**

- [1. 統制対象を棚卸しする（AgentsInfo を KQL で）](#1-統制対象を棚卸しするagentsinfo-を-kql-で)
- [2. Block（Kill Switch）](#2-blockkill-switch構成保持のまま即時停止)
- [3. 削除（リタイア）と後片付け](#3-削除リタイアと後片付け)
- [4. ガードレールの限界](#4-ガードレールの限界agent-id-が無いと統制は効かない)

## 1. 統制対象を棚卸しする（AgentsInfo を KQL で）

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

> `Owners` / `Endpoints` / `DeclaredTools` は dynamic（JSON）列。ここで得た **高リスク／ownerless リスト**が [Secure の条件付きアクセス](./part2-4-secure.md)や一括統制の入力になる。管理センター **Agents › Overview › Top actions for you › Manage agent risks** とも突き合わせる。

## 2. Block（Kill Switch）— 構成保持のまま即時停止

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

## 3. 削除（リタイア）と後片付け

| | Block（無効化） | Permanent delete（削除） |
|--|----------------|--------------------------|
| 何が起きる | 認証・トークン発行を止める。オブジェクトは残る | オブジェクトを消す（子も連鎖削除） |
| 構成・データ | 保持（Unblock で復帰） | 失われる（30 日は論理削除で復元可） |
| クォータ | 消費したまま | 完全削除まで消費（250 上限に注意） |

- 個別: instance 詳細 › **Permanent delete**
- 一括（自前ホスト）: 作業ディレクトリで `a365 cleanup`（**破壊的**。config の blueprint 配下を一括削除）
- orphan アプリ確認: `az ad app list --display-name "<blueprint名>" -o table` → `az ad app delete --id <appId>`

> ⚠️ **後片づけ必須**：学習が終わったら Block ではなく `a365 cleanup` で消し、Azure リソース（App Service / Functions / ACR / ストレージ、まとめて `az group delete -n $RG`）も削除する。連鎖クリーンアップは非同期で数時間〜数日かかることがある。
> **削除後の確認**：1 節 の `AgentsInfo` KQL で `LifecycleStatus == "Deleted"` に遷移したことを確認（反映にタイムラグあり）。

## 4. ガードレールの限界（Agent ID が無いと統制は効かない）

「**見えること ≠ 統制できること**」を体験しておく。

- **Agent ID を主体に持たない**エンティティ（レジストリ同期のみ／素の Entra アプリ登録）は、**一覧には見えても CA の主体にならず統制できない**
- サインインログで、そのエンティティが `Is Agent = No` として扱われることを確認

> これは「**まず観察（Observe）→ Agent ID 発行 → 統制（Govern）**」という順序の必然性を示す。可視化だけでは統制は成立しない。統制には Agent ID の発行（[承認と管理下配置](./part2-1b-custom.md)）が前提。

✅ **Govern 完了条件**：Block → 実際に停止（サインイン Failure）、Unblock → 復帰、を確認。`AgentsInfo` で対象を機械抽出できる。

---

← 戻る：**[第2部：Observe（観察する）](./part2-2-observe.md)** ｜ 次：**[第2部：Secure（保護）](./part2-4-secure.md)** ｜ [README（概要）](../README.MD)
