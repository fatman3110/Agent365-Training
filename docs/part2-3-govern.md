# 第2部：Govern（管理）｜AI 管理者

Agent 365 の 3 本柱の 2 つ目。ライフサイクル管理と一貫したガードレール。**設定して終わりにせず、画面・ログで「効いた」ことを裏取り**する。

> ⚠️ Microsoft Agent 365 / Copilot Studio は Preview を多く含む。UI 名やメニュー位置は変わり得るので、詰まったら Microsoft Learn で最新を確認すること。

**目次**

- [第2部：Govern（管理）｜AI 管理者](#第2部govern管理ai-管理者)
  - [1. ガバナンスの前提（Agent ID が無いと統制は効かない）](#1-ガバナンスの前提agent-id-が無いと統制は効かない)
  - [2. 統制対象を棚卸しする](#2-統制対象を棚卸しする)
  - [3. Block（Kill Switch）— 構成保持のまま即時停止](#3-blockkill-switch-構成保持のまま即時停止)
  - [4. 削除（リタイア）](#4-削除リタイア)
  - [5. カスタムポリシーテンプレートを作る](#5-カスタムポリシーテンプレートを作る)
    - [5-1. Entra で 3 種のポリシーを作成](#5-1-entra-で-3-種のポリシーを作成)
    - [5-2. M365 管理センターでテンプレートを作る](#5-2-m365-管理センターでテンプレートを作る)
  - [6. 条件付きアクセス — Agent risk = High を Block（Report-only → On）](#6-条件付きアクセス--agent-risk--high-を-blockreport-only--on)

## 1. ガバナンスの前提（Agent ID が無いと統制は効かない）

「**見えること ≠ 統制できること**」である

- **Agent ID を主体に持たない**エンティティ（レジストリ同期のみ／素の Entra アプリ登録）は、**一覧には見えても統制できない**

## 2. 統制対象を棚卸しする

まず「どのエージェントを統制するか」を絞る。KQL は不要で、[Microsoft 365 管理センター](https://admin.microsoft.com/) の画面で一覧・フィルタできる。

1. **Agents › All agents › Registry** で全エージェントを一覧
2. **Status / Publisher type / Platform / Channel** のフィルタで対象を絞る
3. **Agents › Overview › Top actions for you** の **Agents without owners（所有者不在）** / **Agents at risk（リスクあり）** から、要対応のエージェントを直接開く
4. 必要なら **Export** で一覧を Excel / CSV に出し、棚卸し記録にする

> 補足：一括処理・自動化したい場合は [Microsoft Defender ポータル](https://security.microsoft.com/) › Advanced hunting の `AgentsInfo` テーブルを KQL で引く方法もある

## 3. Block（Kill Switch）— 構成保持のまま即時停止

Block には 2 つの粒度がある。**本節の手順（下記 1〜4）はエージェント全体の Block**。インスタンス単位の Block は、AI Teammate エージェントにのみ存在するため本教材では対象外。

| 粒度 | どこで | 効果 |
|------|--------|------|
| **エージェント全体**（本節の手順） | Agents › All agents › 対象 › **Block** | 組織全体で利用不可。全ユーザーから外れ、インストール済みのユーザーからも削除される。複数インスタンスがあれば全 instance に波及 |
| **インスタンス単位** | エージェント詳細の **Instances** タブ › 対象 instance › **Block** | その instance だけ停止（実行中の動作も止まる）。**Instances タブは AI Teammate エージェントにのみ表示**されるため、本教材では対象外 |

1. [Microsoft 365 管理センター](https://admin.microsoft.com/) › **Agents › All agents** で対象を開く（`Available`）→ 右上 **Block**
2. **Block agent** にチェック、任意で Reason を記入 → **Save**
3. ステータスが **Blocked** に。
4. 解除は **Unblock** → チェック → Save で `Available` に復帰

> **「Block ＝ ID を止める」であって「プロセスを止める」ではない（重要）**：Block が止めるのは、エージェントの **Entra Agent ID による認証（トークンの発行）**。エージェントの中身（サーバープロセス）まで止まるかは、**外部（LLM や MCP）を呼ぶときに何の資格情報を使っているか**による。
> - エージェントが **Agent ID のトークンで外部を呼ぶ**構成なら、Block でその呼び出しも失敗する（＝キルスイッチ成立）。
> - エージェントが **Agent ID とは別の資格情報**（アプリ自身の ID や API キーなど）で外部を呼ぶ構成なら、**ID は止まってもプロセスは動き続ける** ため、完全に止めるにはホスト側（例：App Service を停止）で止める必要がある。

## 4. 削除（リタイア）

Block は「一時停止」。完全に削除したい場合は、ルートに応じた手順でエージェント本体（と、自前ホストなら Azure リソースまで）消す。

| | Block（無効化） | Delete（削除） |
|--|----------------|----------------|
| 何が起きる | 認証・トークン発行を止める。オブジェクトは残る | Blueprint / Agent ID を消す（関連する Entra オブジェクトも削除） |
| 構成・データ | 保持（Unblock で復帰） | 失われる（30 日は論理削除で復元可） |

片付けはルートによって異なる。

**パターン A（Copilot Studio）**：[Microsoft 365 管理センター](https://admin.microsoft.com/) › **Agents › 対象エージェント › 完全に削除する**（または [Copilot Studio](https://copilotstudio.microsoft.com/) 側で **Agents › 対象 › … › Delete**）

**パターン B（自前ホスト）**：

1. 作業ディレクトリで `a365 cleanup`（**破壊的**。config の Blueprint 配下＝Blueprint と Agent ID、関連する Entra アプリ登録を一括削除）
2. 取り残し確認：`az ad app list --display-name "<blueprint名>" -o table` → 残っていれば `az ad app delete --id <appId>`
3. Azure リソースを削除：App Service / Functions / ACR / ストレージをまとめて `az group delete -n $RG`

## 5. カスタムポリシーテンプレートを作る

テンプレートは、複数のポリシーを束ねてエージェントへ**一括適用するガバナンスの仕組み**。承認タイミングで「テンプレートの適用」で選べる**カスタムテンプレート**は、ここで事前に作る。テンプレートでは **条件付きアクセス・アクセスパッケージ・カスタムセキュリティ属性** の 3 種の Entra ポリシーを束ねられる。

### 5-1. Entra で 3 種のポリシーを作成

テンプレートに束ねる前提として、対象ポリシーを先に作る。ここでは**影響の少ない具体例**で 1 つずつ作る（必要なものだけでよい）。いずれも [Microsoft Entra 管理センター](https://entra.microsoft.com/) で行う。

**(a) 条件付きアクセス（CA）— Report-only（影響ゼロ）**

Report-only なら実際のブロックは起きない。作成手順は本ファイルの [6 節](#6-条件付きアクセス--agent-risk--high-を-blockreport-only--on) を参照（**Assignments › Agents › Select agents** で対象 Agent ID を 1 つ以上選ぶのが必須）。

**(b) アクセスパッケージ — リソースを付けない空パッケージ（権限を与えないので影響なし）**

1. [Microsoft Entra 管理センター](https://entra.microsoft.com/) › **ID ガバナンス › エンタイトルメント管理 › アクセス パッケージ › + 新しいアクセス パッケージ**
2. **基本**：名前（例 `Agent-Training-Package`）を入力
3. **リソース ロール**：勉強用は**何も追加しない**（権限付与ゼロ＝影響なし）
4. **要求**：要求できる相手として **エージェント ID／サービス プリンシパル** を許可（[Learn](https://learn.microsoft.com/entra/id-governance/entitlement-management-access-package-create#allow-users-service-principals-and-agent-identities-in-your-directory-to-request-the-access-package)）
5. 残りは既定のまま **作成**

**(c) カスタムセキュリティ属性 — ラベルを 1 つ付けるだけ（メタデータ付与のみで影響なし）**

1. [Microsoft Entra 管理センター](https://entra.microsoft.com/) › **Entra ID › カスタム セキュリティ属性 › 属性セットの追加**（例 `AgentGovernance`）※定義には **Attribute Definition Administrator** ロールが必要。**Global 管理者でも既定ではこの権限を持たない**（[Learn](https://learn.microsoft.com/entra/fundamentals/custom-security-attributes-add)）
2. 作った属性セットを開き **属性の追加**（例 名前 `Environment`／型 String）
3. **Entra ID › エンタープライズ アプリケーション › 対象のエージェント ID（サービス プリンシパル）› 管理 › カスタム セキュリティ属性 › 割り当ての追加** で `Environment = Training` を付与 ※割り当てには **Attribute Assignment Administrator** ロールが必要（[Learn](https://learn.microsoft.com/entra/identity/enterprise-apps/custom-security-attributes-apps)）

> CA の「すべてのエージェント ID」スコープは、[Microsoft 365 管理センター](https://admin.microsoft.com/) 側で自動選択され上書きできない。
> ⚠️ これらの Entra ポリシーは、エージェントが **Entra 認証で**リソースへアクセスする前提。Entra 認証でないエージェントには割り当てても実行時に強制されないことがある。


### 5-2. M365 管理センターでテンプレートを作る

1. [Microsoft 365 管理センター](https://admin.microsoft.com/) › **Agents › Settings › Templates › Add a New Template**
2. テンプレート名・説明を入力し、「自分のアクセスで動くエージェントに適用するか」を指定
3. **Next** → 追加したいカスタムポリシー（5-1 で作った CA / アクセスパッケージ / カスタムセキュリティ属性）を選ぶ
4. 内容を確認して **Save template**

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

---

← 戻る：**[第2部：Observe（観察する）](./part2-2-observe.md)** ｜ 次：**[第2部：Secure（保護）](./part2-4-secure.md)** ｜ [README（概要）](../README.MD)
