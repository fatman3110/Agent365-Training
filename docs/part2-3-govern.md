# 第2部：Govern（管理）｜AI 管理者

Agent 365 の 3 本柱の 2 つ目。ライフサイクル管理と一貫したガードレール。**設定して終わりにせず、画面・ログで「効いた」ことを裏取り**する。

> ⚠️ Microsoft Agent 365 / Copilot Studio は Preview を多く含む。UI 名やメニュー位置は変わり得るので、詰まったら Microsoft Learn で最新を確認すること。

**目次**

- [第2部：Govern（管理）｜AI 管理者](#第2部govern管理ai-管理者)
  - [1. 統制対象を棚卸しする（M365 管理センター）](#1-統制対象を棚卸しするm365-管理センター)
  - [2. Block（Kill Switch）— 構成保持のまま即時停止](#2-blockkill-switch-構成保持のまま即時停止)
  - [3. 削除（リタイア）と後片付け](#3-削除リタイアと後片付け)
  - [4. ガードレールの限界（Agent ID が無いと統制は効かない）](#4-ガードレールの限界agent-id-が無いと統制は効かない)
  - [5. カスタムポリシーテンプレートを作る](#5-カスタムポリシーテンプレートを作る)
    - [5-1. 前提](#5-1-前提)
    - [5-2. Entra で 3 種のポリシーを作る（必要なものだけ）](#5-2-entra-で-3-種のポリシーを作る必要なものだけ)
    - [5-3. M365 管理センターでテンプレートを作る](#5-3-m365-管理センターでテンプレートを作る)
  - [6. 条件付きアクセス — Agent risk = High を Block（Report-only → On）](#6-条件付きアクセス--agent-risk--high-を-blockreport-only--on)

## 1. 統制対象を棚卸しする（M365 管理センター）

まず「どのエージェントを統制するか」を絞る。KQL は不要で、[Microsoft 365 管理センター](https://admin.microsoft.com/) の画面で一覧・フィルタできる。

1. **Agents › All agents › Registry** で全エージェントを一覧
2. **Status / Publisher type / Platform / Channel** のフィルタで対象を絞る
3. **Agents › Overview › Top actions for you** の **Agents without owners（所有者不在）** / **Agents at risk（リスクあり）** から、要対応のエージェントを直接開く
4. 必要なら **Export** で一覧を Excel / CSV に出し、棚卸し記録にする

> 補足：一括処理・自動化したい場合は [Defender](https://security.microsoft.com/) › Advanced hunting の `AgentsInfo` テーブルを KQL で引く方法を活用可能

## 2. Block（Kill Switch）— 構成保持のまま即時停止

Block には 2 つの粒度がある。**本節の手順（下記 1〜4）はエージェント全体の Block**。インスタンス単位の Block は別 UI（Instances タブ）で、しかも AI Teammate エージェントにのみ存在するため本教材では対象外。

| 粒度 | どこで | 効果 |
|------|--------|------|
| **エージェント全体**（本節の手順） | Agents › All agents › 対象 › **Block** | 組織全体で利用不可。全ユーザーから外れ、インストール済みのユーザーからも削除される。複数インスタンスがあれば全 instance に波及 |
| **インスタンス単位** | エージェント詳細の **Instances** タブ › 対象 instance › **Block** | その instance だけ停止（実行中の動作も止まる）。**Instances タブは AI Teammate エージェントにのみ表示**されるため、非 AI Teammate の本教材では対象外 |

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
> **削除後の確認**：レジストリの一覧から対象が消える（`LifecycleStatus` が `Deleted` に遷移する）ことを確認（反映にタイムラグあり）。

## 4. ガードレールの限界（Agent ID が無いと統制は効かない）

「**見えること ≠ 統制できること**」を体験しておく。

- **Agent ID を主体に持たない**エンティティ（レジストリ同期のみ／素の Entra アプリ登録）は、**一覧には見えても CA の主体にならず統制できない**
- サインインログで、そのエンティティが `Is Agent = No` として扱われることを確認

> これは「**まず観察（Observe）→ Agent ID 発行 → 統制（Govern）**」という順序の必然性を示す。可視化だけでは統制は成立しない。統制には Agent ID の発行（[承認と管理下配置](./part2-1b-custom.md)）が前提。

## 5. カスタムポリシーテンプレートを作る

テンプレートは、複数のポリシーを束ねてエージェントへ**一括適用するガバナンスの仕組み**（Microsoft も policy templates を governance 機能と位置づける）。承認ウィザードの「テンプレートの適用」で選べる**カスタムテンプレート**は、ここで事前に作る。既定テンプレートで足りるなら本節はスキップしてよい。カスタムテンプレートには **条件付きアクセス・アクセスパッケージ・カスタムセキュリティ属性** の 3 種の Entra ポリシーを束ねられる。

### 5-1. 前提

- **先に Entra でポリシーを作成**しておく（未作成だとテンプレート作成時に選べない）
- カスタムセキュリティ属性ポリシーには、Global 管理者・AI 管理者ともに **Attribute Assignment Administrator** ロールが必要（Global 管理者なら自分でロール付与に同意できる）
- **AI 管理者**はアクセスパッケージの作成・適用は可能だが、**条件付きアクセスとカスタムセキュリティ属性には権限不足**（Global 管理者が必要）
- Entra カスタムポリシーの適用には **Agent 365 ライセンス**が必要

### 5-2. Entra で 3 種のポリシーを作る（必要なものだけ）

| ポリシー | 用途 | 作り方 |
|----------|------|--------|
| **条件付きアクセス（CA）** | Agent risk 等の条件でトークン発行を制御 | 本ファイル 6 節（CA）の手順。要点：Entra › **Conditional Access › + Create new policy** → **Assignments** を開き **Agents** に適用 → **Select agents** で対象の Agent ID を**1つ以上**選ぶ（必須；選ばないとテンプレート一覧に出ない）→ 条件・制御を設定して保存 |
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

## 6. 条件付きアクセス — Agent risk = High を Block（Report-only → On）

条件付きアクセス（CA）は、5 節のテンプレートに束ねられる「前提ポリシー」の 1 つ。Entra の CA で「**すべてのエージェント ID**」を対象に、**Agent risk = High**（Preview）のときトークン発行をブロックする。エージェント ID を主体にしたリスクベースの自動遮断で、**いきなり On にせず、まず Report-only で影響を確認**してから有効化するのが定石。

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
> 条件付きアクセスはリスクベースのアクセス制御（[Secure](./part2-4-secure.md) の考え方）でもあるが、テンプレートに束ねる前提ポリシーとして本節（Govern）でまとめて扱う。
> 出典: [エージェント向け条件付きアクセス](https://learn.microsoft.com/entra/identity/conditional-access/agent-id)

✅ **Govern 完了条件**：Block → 実際に停止（サインイン Failure）、Unblock → 復帰、を確認。レジストリで統制対象を絞り込める。カスタムテンプレートを使う場合は承認ウィザードに自作テンプレートが並び、CA は Report-only で「Would block」まで評価されることを確認。

---

← 戻る：**[第2部：Observe（観察する）](./part2-2-observe.md)** ｜ 次：**[第2部：Secure（保護）](./part2-4-secure.md)** ｜ [README（概要）](../README.MD)
