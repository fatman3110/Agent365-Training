# 第2部 A：承認と観測データ作成（Copilot Studio）｜AI 管理者

[第1部 A](./part1a-copilot-studio.md) で Copilot Studio から**組織に申請**したエージェントを、管理者が承認して Teams / Microsoft 365 Copilot で使えるようにし、実際に動かして観測データを作るまで。ここまで済ませると、この後の **[Observe](./part2-2-observe.md) → [Govern](./part2-3-govern.md) → [Secure](./part2-4-secure.md)** の画面にデータが出るようになる。


> ⚠️ Microsoft Agent 365 / Copilot Studio は Preview を多く含む。UI 名やメニュー位置は変わり得るので、詰まったら Microsoft Learn で最新を確認すること。

**目次**

- [1. 承認して「管理下」に置く](#1-承認して管理下に置く)
- [2. エージェントを実際に動かす（観測データを作る）](#2-エージェントを実際に動かす観測データを作る)

## 1. 承認して「管理下」に置く

Copilot Studio から「組織に表示」を申請したエージェントは、Microsoft 365 管理センター（Copilot Control System）の **Requests（申請）** に現れる。管理者が承認して初めて、組織のユーザーが使える。

### 1-1. 申請されたエージェントを承認する（Requests → Publish）

1. [Microsoft 365 管理センター](https://admin.microsoft.com/) にサインイン
2. **Agents › All agents › Requests** を開き、Copilot Studio から申請されたエージェントを確認
3. 対象を開き、詳細を確認したうえで **ストアに公開** 
4. ウィザードを進める：
   1. **ユーザを選択する** — インストール可能なユーザー（All users / 特定）を選択
   2. **テンプレートの適用** — ポリシーテンプレート（既定 / カスタム）を選ぶ（下の注記参照）
   3. **アクセス許可を承諾する** — エージェントが要求する権限を確認し、必要なら管理者同意。このエージェントでは不要。
   4. **公開**

> **テンプレートの適用の設定には「事前準備」が必要（重要）**
> - **カスタムテンプレート**を使うなら**事前準備**が要る。アクセスパッケージ・カスタムセキュリティ属性も束ねられる。**フル手順**は [Secure：カスタムポリシーテンプレートを作る](./part2-4-secure.md#5-カスタムポリシーテンプレートを作る) を参照。
> - すぐ進めたいなら、まず **既定テンプレート（全エージェント用）** を選ぶ。
> - ⚠️ **テンプレートは「新規アクティブ化時のみ」適用**。**承認済みには後付けできない**（[Learn FAQ](https://learn.microsoft.com/microsoft-agent-365/admin/policy-template#select-a-template)）

承認が完了するとエージェントは組織カタログに載り、利用可能になる。

### 1-2. Teams / Copilot で使えるようにする

承認後、エージェントは Teams アプリストアの **Built for your org**（組織で作成）に現れる。Copilot Studio 側でチャネル接続済みのため、**第2部 B のような Teams 開発者ポータルの手動設定は不要**。

1. [Teams](https://teams.cloud.microsoft/) › **アプリ** で作成したエージェント名を検索
2. **Add / インストール**（管理者が特定ユーザーへ事前インストールすることも可能）
3. Microsoft 365 Copilot でも使う設定にしていれば、Copilot のサイドバーからも呼び出せる

出典: [Connect and configure an agent for Teams and Microsoft 365](https://learn.microsoft.com/microsoft-copilot-studio/publication-add-bot-to-microsoft-teams)

> エージェント作成の反映は非同期。承認・インストール後、Teams 検索に出るまで数分〜数時間かかることがある。

> **「組織向けに開発（Built for your org）」に検索しても出ない場合の切り分け**
> Microsoft 365 管理センターの **エージェント一覧で「使用可能」** と表示されても、それは **Agent 365 レジストリ上の状態**であり、**Teams アプリストアの「組織向けに開発」への掲載＝管理者承認済み**とは別物。以下を上から順に確認する。
> 1. **管理者承認が未完了／伝播待ち** — 「組織向けに開発」は**管理者が承認したアプリだけ**が並ぶ。承認は Teams 管理センターの **[アプリを管理（Manage apps）](https://learn.microsoft.com/microsoftteams/submit-approve-custom-apps#validate)** 側で行い、Copilot Studio 側の **公開ページ → 承認状態が「承認済み（Approved）」** になっているかを確認する（[Learn](https://learn.microsoft.com/microsoft-copilot-studio/publication-add-bot-to-microsoft-teams#show-an-agent-in-the-teams-app-store-or-in-the-microsoft-365-agent-store)）。承認直後は反映に数分〜数時間かかる。
> 2. **公開後に公開範囲を狭めた** — 管理者承認へ**送信した後にアクセス範囲を「組織全員」未満に変えると、ユーザーはインストールしても使えず、検索にも出ない**（[Learn 注記](https://learn.microsoft.com/microsoft-copilot-studio/publication-add-bot-to-microsoft-teams#show-an-agent-in-the-teams-app-store-or-in-the-microsoft-365-agent-store)）。範囲を「組織内のすべてのユーザー」に戻す。
> 3. **検索したユーザーのライセンス／アプリポリシー** — 検索している本人が **Teams ライセンス＋Microsoft 365 Copilot ライセンス**を持ち、Teams のアプリ許可／セットアップポリシーでブロックされていないか。承認済みでも、アプリポリシーで対象外にされたユーザーには表示されない。
> 4. **Power Platform アプリの Teams 追加が無効** — 「Built with Power Platform」セクション経由で探す場合は、テナントで Power Platform アプリの Teams 追加が許可されている必要がある（[Manage Power Platform apps](https://learn.microsoft.com/microsoftteams/manage-power-platform-apps)）。

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
