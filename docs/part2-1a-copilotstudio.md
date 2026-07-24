# 第2部 A：承認と観測データ作成（Copilot Studio）｜AI 管理者

[第1部 A](./part1a-copilot-studio.md) で Copilot Studio から**組織に申請**したエージェントを、管理者が承認して Teams / Microsoft 365 Copilot で使えるようにし、実際に動かして観測データを作るまで。ここまで済ませると、この後の **[Observe](./part2-2-observe.md) → [Govern](./part2-3-govern.md) → [Secure](./part2-4-secure.md)** の画面にデータが出るようになる。

> ℹ️ 独自エージェント（フルコード）で作った場合は **[第2部 B](./part2-1b-custom.md)** を参照。Observe / Govern / Secure は A・B 共通。
>
> ⚠️ Microsoft Agent 365 / Copilot Studio は Preview を多く含む。UI 名や配置は変わり得るので、詰まったら [Microsoft Learn](https://learn.microsoft.com/microsoft-365/copilot/agent-essentials/agent-lifecycle/agent-copilot-studio-requested) で最新を確認すること。

**目次**

- [1. 承認して「管理下」に置く](#1-承認して管理下に置く)
- [2. エージェントを実際に動かす（観測データを作る）](#2-エージェントを実際に動かす観測データを作る)

## 1. 承認して「管理下」に置く

Copilot Studio から「組織に表示」を申請したエージェントは、Microsoft 365 管理センター（Copilot Control System）の **Requests（申請）** に現れる。管理者が承認して初めて、組織のユーザーが使える。

### 1-1. 申請されたエージェントを承認する（Requests → Publish）

1. [Microsoft 365 管理センター](https://admin.microsoft.com/) にサインイン
2. **Agents › All agents › Requests** を開き、Copilot Studio から申請されたエージェントを確認
3. 対象を開き、Capabilities / Data sources / Security・Permissions / Custom actions を確認 → **Publish to store**（承認）
4. 「**Publish new agent**」ウィザードを進める：
   1. **Select users** — インストール可能なユーザー（All users / 特定）を選択
   2. **Apply template** — ポリシーテンプレート（既定 / カスタム）を選ぶ（下の注記参照）
   3. **Review permissions** — エージェントが要求する権限を確認し、必要なら管理者同意
   4. **Review and finish → Publish**

出典: [Manage agent requests](https://learn.microsoft.com/microsoft-365/admin/manage/agent-requests) ｜ [Manage Copilot Studio requested agents](https://learn.microsoft.com/microsoft-365/copilot/agent-essentials/agent-lifecycle/agent-copilot-studio-requested)

<!-- ![Requests タブ](../assets/08-requests.png) -->

> **ポリシーテンプレート／条件付きアクセスは「事前準備」が要る（重要）**
> - **カスタムテンプレート**を使うなら、**先に Entra で CA 等のポリシーを作成**しておく必要がある。CA の作り方は [Secure の条件付きアクセス](./part2-4-secure.md)。
> - すぐ進めたいなら、まず **既定テンプレート（全エージェント用）** を選べばよい。
> - ⚠️ **テンプレートは「新規アクティブ化時のみ」適用**。**承認済みには後付けできない**（[Learn FAQ](https://learn.microsoft.com/microsoft-agent-365/admin/policy-template#select-a-template)）。後から統制を変えるなら **Entra の CA を直接更新**する。
> - 出典: [Learn: ポリシーテンプレート](https://learn.microsoft.com/microsoft-agent-365/admin/policy-template)

> **ツール（MCP / コネクタ）を使っている場合**：第1部 A でエージェントにツールを足していると、ツールにも管理者の同意・承認が必要なことがある。**Agents › Tools › Requests (preview)** で対象を **Approve** する。

✅ 承認が完了するとエージェントは組織カタログに載り、利用可能になる。

### 1-2. Teams / Copilot で使えるようにする

承認後、エージェントは Teams アプリストアの **Built for your org**（組織で作成）に現れる。Copilot Studio 側でチャネル接続済みのため、**第2部 B のような Teams 開発者ポータルの手動設定は不要**。

1. Teams › **Apps** でエージェント名を検索
2. **Add / インストール**（管理者が特定ユーザーへ事前インストールすることも可能）
3. Microsoft 365 Copilot でも使う設定にしていれば、Copilot のサイドバーからも呼び出せる

出典: [Connect and configure an agent for Teams and Microsoft 365](https://learn.microsoft.com/microsoft-copilot-studio/publication-add-bot-to-microsoft-teams)

> エージェント作成の反映は非同期。承認・インストール後、Teams 検索に出るまで数分〜数時間かかることがある。

## 2. エージェントを実際に動かす（観測データを作る）

**この節が [Observe](./part2-2-observe.md) 以降の前提**。Observe 以降の画面は、エージェントを一度も動かしていないと**何も表示されない**。

### 2-1. Teams / Copilot で話しかける

1. Teams（または Microsoft 365 Copilot）で、追加したエージェントを開く
2. エージェントの機能に応じた質問を送る（例：「今日の予定を教えて」など、ツールを使う質問だと後段の観測が見やすい）
3. 応答が返れば、受信・送信の両方が通っている

> Copilot Studio エージェントは、公開すると **Observability のテレメトリ送信が自動的に有効**になる（開発者側の SDK 配線は不要）。この 1 回の会話が、Observe で追う「Run」になる。

### 2-2. 観測データを厚くするコツ

[Observe](./part2-2-observe.md) の画面を見栄えよくするために、少し多めに動かしておく：

- **複数回**会話する → Activity / Map に件数が積み上がる
- **複数ユーザー**で使う → User ノードが増える
- ツールを使う質問を混ぜる → Tool ノードが出る

> **要件**：E7（Agent 365）＋ Global Administrator か AI Administrator。Usage / 観測はテナント **< 4,000 ユーザー**で有効。反映には数分〜十数分のタイムラグがある。

---

← 戻る：**[第1部 A：Copilot Studio で作る](./part1a-copilot-studio.md)** ｜ 次：**[第2部：Observe（観察する）](./part2-2-observe.md)** ｜ [README（概要）](../README.MD)
