# 第2部 B：承認と観測データ作成（独自エージェント）｜AI 管理者

[第1部 B](./part1b-custom-agent.md) で作った**独自エージェント＋独自 MCP** を、管理者が承認して Teams に接続し、実際に動かして観測データを作るまで。ここまで済ませると、この後の **[Observe](./part2-2-observe.md) → [Govern](./part2-3-govern.md) → [Secure](./part2-4-secure.md)** の画面にデータが出るようになる。

> ℹ️ Copilot Studio で作った場合は **[第2部 A](./part2-1a-copilotstudio.md)** を参照。Observe / Govern / Secure は A・B 共通。
>
> ⚠️ Microsoft Agent 365 は Preview を多く含む。コマンド・API・UI は変わり得るので、詰まったら [Microsoft Learn](https://learn.microsoft.com/ja-jp/microsoft-agent-365/overview) で最新を確認すること。

**目次**

- [1. Teams に接続し、承認を得て「管理下」に置く](#1-teams-に接続し承認を得て管理下に置く)
- [2. エージェントを実際に動かす（観測データを作る）](#2-エージェントを実際に動かす観測データを作る)

## 1. Teams に接続し、承認を得て「管理下」に置く

### 1-1. 自作 MCP（道具）を承認する

第1部で登録申請した自作 MCP（`echo` / `now`）を、管理者が承認して初めてエージェントから呼べるようになる。

1. [Microsoft 365 管理センター](https://admin.microsoft.com/) › **Agents › Tools › Requests (preview)** を開く
2. 対象の MCP（[第1部 B](./part1b-custom-agent.md) の `$MCP` の表示名）を開く → **Approve**
3. 求められた管理者同意を付与する（`-A365Proxy` / `-BYO` / ランタイム用のアプリ登録に対する同意）
4. Status が **Available** に変われば承認完了（承認まではエージェントから呼び出せない）

| ![Tools › Requests で自作 MCP を承認する画面](../assets/part2-1b-02-tools.png) |
|:-:|


### 1-2. Teams App を公開して管理者承認を得る

[第1部 B §6-4／§7](./part1b-custom-agent.md#6-4-bot-app--bot-service-を作り-teams-チャネルを有効化する) で作った Teams App Package を、管理者の承認を得て組織で使える状態にする。

> ⚠️ このフローは Agent 365 ネイティブの "Request Instance"（インスタンス要求）フローとは別物。Blueprint App は Agentic Application 型で Bot Framework の Teams チャネル登録を通らないため、classic Bot App + 通常の Teams App 公開経路（下記）を使う（[第1部 B §6-4](./part1b-custom-agent.md#6-4-bot-app--bot-service-を作り-teams-チャネルを有効化する) 参照）。承認自体は同じ **Microsoft 365 管理センター** 上で行われるが、タブ名・導線が Agent 365 ネイティブの「Requests」と同一かどうかは**要確認・本教材執筆時点で未確定**（Microsoft Learn で最新の手順を確認すること）。

1. プロジェクトルート（`m365agents.yml` のある場所）で公開コマンドを実行:
   ```powershell
   npx --yes @microsoft/m365agentstoolkit-cli@latest publish --env dev --interactive false
   ```
2. **再公開する場合は必ず `appPackage/manifest.json` の `version` を上げる**（インクリメントしないと管理センター側が更新に失敗し「技術的なエラー」と表示されることがある）。
3. 管理者側の操作：[Microsoft 365 管理センター](https://admin.microsoft.com/) を開く › **Teams アプリ › アプリの管理**（環境によっては **Agents › Requests** に出る可能性もある。上記の通りどちらに出るかは要確認）で該当アプリを開く → 状態を `Submitted` → `Published` に変更して承認する。
4. 承認後、組織のユーザーが Teams の「アプリ」からこのエージェントを追加できるようになる（反映まで時間がかかる場合あり）。
5. 反映されない／古い版が見える場合は Teams クライアントのキャッシュが原因のことがある。Teams を終了し、`%APPDATA%\Microsoft\Teams` 配下の `Cache` / `GPUCache` / `Code Cache` を削除して再起動する。

> **ポリシーテンプレート／条件付きアクセスは「事前準備」が要ることがある**
> - ⚠️ 以下は Agent 365 ネイティブの "Request Instance" フロー向けの記述であり、今回の Teams App 公開フローに同様に適用されるかは**未検証**。適用有無を確認してから活用すること。
> - **カスタムテンプレート**を使うなら、**先に Entra でポリシーを作成**しておく必要がある（未作成だとテンプレート作成時に選べない）。CA・アクセスパッケージ・カスタムセキュリティ属性の**フル手順**は [Govern：カスタムポリシーテンプレートを作る](./part2-3-govern.md#5-カスタムポリシーテンプレートを作る) を参照。
> - すぐ進めたいなら、まず **既定テンプレート（全エージェント用）** を選べばよい（カスタムは後回しでも可）。
> - ⚠️ **テンプレートは「新規アクティブ化時のみ」適用**。**承認済みのエージェントには後付けできない**（[Learn FAQ](https://learn.microsoft.com/microsoft-agent-365/admin/policy-template#select-a-template)）。後から統制を足す／変える場合は、テンプレートではなく **Entra の 条件付きアクセス を直接更新**する（対象エージェント ID に動的に効く）。
> - 出典: [Learn: ポリシーテンプレート](https://learn.microsoft.com/microsoft-agent-365/admin/policy-template)

>
## 2. エージェントを実際に動かす（観測データを作る）

**この節が [Observe](./part2-2-observe.md) 以降の前提**。Observe 以降の画面は、エージェントを一度も動かしていないと**何も表示されない**。まずクラウド上のエージェントを実際に呼び出し、観測データ（Run）を作る。

### 2-1. エージェントに話しかける（Teams）

| ![Teams でエージェントに echo / now を送り、応答が返っている画面](../assets/part2-1b-04-chat.png) |
|:-:|

1-2 節 で公開・承認した Teams App を通じてエージェントに、**Teams のチャットで話しかける**（これが現実の利用チャネル）。

1. Teams › **Apps** で追加した自分のエージェントを開く
2. `echo こんにちは` や `今何時？`（`now`）などと送る
3. 応答が返れば、**受信（Teams→エージェント）と送信（エージェント→Teams）の両方**が通っている

### 2-2. 観測データを厚くするコツ

[Observe](./part2-2-observe.md) の画面を見栄えよくするために、少し多めに動かしておく：

- **複数回**会話する → Activity / Map に件数が積み上がる
- **複数ユーザー**で使う → User ノードが増える
- ツールを使う指示を混ぜる → Tool ノードが出る

---

← 戻る：**[第1部 B：独自エージェント＋独自 MCP](./part1b-custom-agent.md)** ｜ 次：**[第2部：Observe（観察する）](./part2-2-observe.md)** ｜ [README（概要）](../README.MD)
