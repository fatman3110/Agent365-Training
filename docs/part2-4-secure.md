# 第2部：Secure（保護）｜AI 管理者

Agent 365 の 3 本柱の 3 つ目。Learn の Secure は、**Entra（リスクベースのアクセス制御）・Purview（情報保護 / DLP）・Defender（脅威防御）** の 3 面でエージェントをエンドツーエンドに守る。

> ▶ **前提**：[第2部 A](./part2-1a-copilotstudio.md) / [B](./part2-1b-custom.md) で承認済み、[Observe](./part2-2-observe.md)・[Govern](./part2-3-govern.md) を確認済みであること。
>
> ⚠️ Microsoft Agent 365 は Preview を多く含む（Agent risk 条件など）。UI・提供条件は変わり得る。

| 保護面 | 役割 | 本節 |
|--------|------|------|
| **Microsoft Entra** | ユーザー／エージェントに一貫したリスクベースのアクセス制御（Agent risk による Block 等） | 2 節 |
| **Microsoft Purview** | 情報保護・DLP・リスクセーフガードで機密データ露出を防ぐ | 3 節 |
| **Microsoft Defender** | エージェント活動の脅威検出・調査・対応（Advanced Hunting） | 4 節 |

**目次**

- [1. 全体像](#1-全体像)
- [2. 条件付きアクセス — Agent risk = High を Block](#2-条件付きアクセス--agent-risk--high-を-blockreport-only--on)
- [3. Purview — 機密データの保護](#3-purview--機密データの保護情報保護--dlp)
- [4. Defender — 脅威検出と調査](#4-defender--脅威検出と調査advanced-hunting)
- [5. カスタムポリシーテンプレートを作る](#5-カスタムポリシーテンプレートを作る)

## 1. 全体像

[Observe](./part2-2-observe.md) が「見る」、[Govern](./part2-3-govern.md) が「ライフサイクルを止める／消す」なら、Secure は「**リスクに応じて自動で守る**」。同じ Entra / Purview / Defender の画面を、ここでは**保護（ポリシー適用・データ保護・脅威検出）**の観点で使う。

## 2. 条件付きアクセス — Agent risk = High を Block（Report-only → On）

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
> このポリシーは [Govern の棚卸し](./part2-3-govern.md) や [承認ウィザードのテンプレート](./part2-1b-custom.md) から参照される「事前準備するポリシー」の実体でもある。
> 出典: [エージェント向け条件付きアクセス](https://learn.microsoft.com/entra/identity/conditional-access/agent-id)

## 3. Purview — 機密データの保護（情報保護 / DLP）

[Observe の 4 画面ラボ](./part2-2-observe.md) で Purview を**観察**（Prompt/Response を読む）に使ったが、Secure では**保護**に使う。エージェントが機密データを扱う／外部へ出す動きを、情報保護ラベル・DLP・リスクセーフガードで抑止する。

- [Purview](https://purview.microsoft.com/) › **DSPM for AI** で、エージェントの AI アクティビティに含まれる機密情報の種類・件数を把握
- DLP ポリシーで、機密ラベル付きデータのプロンプト送信やツール経由の持ち出しを制限
- 詳細: [Purview DSPM for AI](https://learn.microsoft.com/purview/ai-microsoft-purview)

> 本教材の `echo` / `now` は機密データを扱わないため DLP は発火しにくい。ここでは「**どこで機密保護をかけるか**」の位置づけを掴めば十分。

## 4. Defender — 脅威検出と調査（Advanced Hunting）

Defender はエージェント活動を**脅威防御**の観点で監視する。[Observe の 4 画面ラボ](./part2-2-observe.md) や [Govern の棚卸し](./part2-3-govern.md) で使った `CloudAppEvents` / `AgentsInfo` は、そのまま**不審な振る舞いの検出**にも使える。

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

- 高リスク該当は [Govern の棚卸し](./part2-3-govern.md) や本節の CA（Agent risk）へフィードバックする
- 詳細: [Defender Advanced Hunting（AgentsInfo テーブル）](https://learn.microsoft.com/defender-xdr/advanced-hunting-agentsinfo-table)

✅ **Secure 完了条件**：CA を Report-only で「Would block」までログ確認。Purview / Defender でエージェントのデータ・脅威面を見る場所を把握。

## 5. カスタムポリシーテンプレートを作る

承認ウィザードの「テンプレートの適用」で選べる**カスタムテンプレート**は、ここで事前に作る。既定テンプレートで足りるなら本節はスキップしてよい。カスタムテンプレートには **条件付きアクセス・アクセスパッケージ・カスタムセキュリティ属性** の 3 種の Entra ポリシーを束ねられる。

### 5-1. 前提

- **先に Entra でポリシーを作成**しておく（未作成だとテンプレート作成時に選べない）
- カスタムセキュリティ属性ポリシーには、Global 管理者・AI 管理者ともに **Attribute Assignment Administrator** ロールが必要（Global 管理者なら自分でロール付与に同意できる）
- **AI 管理者**はアクセスパッケージの作成・適用は可能だが、**条件付きアクセスとカスタムセキュリティ属性には権限不足**（Global 管理者が必要）
- Entra カスタムポリシーの適用には **Agent 365 ライセンス**が必要

### 5-2. Entra で 3 種のポリシーを作る（必要なものだけ）

| ポリシー | 用途 | 作り方 |
|----------|------|--------|
| **条件付きアクセス（CA）** | Agent risk 等の条件でトークン発行を制御 | 本ファイル 2 節の手順。要点：Entra › **Conditional Access › + Create new policy** → **Assignments** を開き **Agents** に適用 → **Select agents** で対象の Agent ID を**1つ以上**選ぶ（必須；選ばないとテンプレート一覧に出ない）→ 条件・制御を設定して保存 |
| **アクセスパッケージ** | リソース・ロール・ポリシーを束ねてエージェントのアクセス権を付与 | Entra ID Governance › Entitlement management でアクセスパッケージを作成し、エージェント ID が要求できるように設定（[Learn](https://learn.microsoft.com/entra/id-governance/entitlement-management-access-package-create#allow-users-service-principals-and-agent-identities-in-your-directory-to-request-the-access-package)） |
| **カスタムセキュリティ属性** | エージェント ID に組織固有のメタデータを付与してきめ細かなアクセス制御 | Entra でカスタムセキュリティ属性を定義・割り当て（[Learn](https://learn.microsoft.com/entra/fundamentals/custom-security-attributes-overview)） |

> CA・カスタムセキュリティ属性は **Global 管理者**が必要（AI 管理者では不足）。CA を「すべてのエージェント ID」にスコープすると M365 管理センターで自動選択され上書き不可。
> ⚠️ Entra ポリシーはエージェントが **Entra 認証で**リソースにアクセスする前提。Entra 認証でないエージェントには割り当てても実行時に強制されないことがある。

### 5-3. M365 管理センターでテンプレートを作る

1. [Microsoft 365 管理センター](https://admin.microsoft.com/) › **Agents › Settings › Templates › Add a New Template**
2. テンプレート名・説明を入力し、「自分のアクセスで動くエージェントに適用するか」を指定
3. **Next** → 追加したいカスタムポリシー（5-2 で作った CA / アクセスパッケージ / カスタムセキュリティ属性）を選ぶ
4. 内容を確認して **Save template**

> Microsoft 既定ポリシーはロックされ編集不可。カスタムポリシーだけ追加できる。テンプレート適用（Entra カスタムポリシー）には **Agent 365 ライセンス**が必要。AI 用テンプレートのシナリオは Frontier テナント限定の Preview。
> 出典: [Learn: ポリシーテンプレート](https://learn.microsoft.com/microsoft-agent-365/admin/policy-template)

作ったテンプレートは、承認ウィザードの「テンプレートの適用」ドロップダウンに既定テンプレートと並んで表示される。

---

← 戻る：**[第2部：Govern（管理）](./part2-3-govern.md)** ｜ [README（概要）](../README.MD)
