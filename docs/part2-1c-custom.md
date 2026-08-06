# 第2部 C：Teams と Copilot Studio A2A から実行する｜AI 管理者・開発者

[第1部 C](./part1c-custom-agent.md) で作成・申請した **Teams + A2A 対応の独自エージェント（S2S）** と **Copilot Studio の A2A 呼び出し元エージェント**を管理者が承認し、Teams と Copilot Studio の2つの経路から実行する。観測データを作ることで、この後の **[Observe](./part2-2-observe.md) → [Govern](./part2-3-govern.md) → [Secure](./part2-4-secure.md)** を確認できる。

> ℹ️ Copilot Studio で作った場合は **[第2部 A](./part2-1a-copilotstudio.md)** を参照。Observe / Govern / Secure は A・B・C 共通。

> ⚠️ Microsoft Agent 365 は Preview を多く含む。コマンド・API は変わり得るので、Microsoft Learn で最新情報を確認すること。

**目次**

- [第2部 C：Teams と Copilot Studio A2A から実行する｜AI 管理者・開発者](#第2部-cteams-と-copilot-studio-a2a-から実行するai-管理者開発者)
  - [1. 公開申請を承認して「管理下」に置く](#1-公開申請を承認して管理下に置く)
    - [1-1. Teams App の公開申請を管理者が承認する](#1-1-teams-app-の公開申請を管理者が承認する)
    - [1-2. A2A 呼び出し元エージェントの申請を管理者が承認する](#1-2-a2a-呼び出し元エージェントの申請を管理者が承認する)
  - [2. Teams から独自エージェントを動かす](#2-teams-から独自エージェントを動かす)
  - [3. Copilot Studio から A2A 呼び出しを実行する](#3-copilot-studio-から-a2a-呼び出しを実行する)
  - [4. 両経路の観測データを作る](#4-両経路の観測データを作る)

## 1. 公開申請を承認して「管理下」に置く

### 1-1. Teams App の公開申請を管理者が承認する

[第1部 C 6 節](./part1c-custom-agent.md#6-teams-app-packagemanifestjson--m365agentsymlを作る) で公開（`publish` コマンドの実行）まで済ませた Teams App Package を、管理者が承認して組織で使える状態にする。

1. [Microsoft 365 管理センター](https://admin.microsoft.com/) を開く › 左ナビ **設定 › 統合アプリ** を選択。
2. **要求されたアプリ** タブを開くと、対象アプリ（例: `agent365-xxxx` / ホスト製品 `Teams`）が **状態: 公開保留中** で一覧に出ている。
3. アプリ名をクリックして開き、内容を確認のうえ承認（公開）する。
4. 承認後、組織のユーザーが Teams の「アプリ」からこのエージェントを追加できるようになる（反映まで時間がかかる場合あり）。

### 1-2. A2A 呼び出し元エージェントの申請を管理者が承認する

[第1部 C 7-4 節](./part1c-custom-agent.md#7-4-公開して組織に申請する) で Copilot Studio から組織カタログへ申請した `A2A Caller Agent` を、管理者が承認して組織で使える状態にする。

1. [Microsoft 365 管理センター](https://admin.microsoft.com/) にサインインする
2. **Agents > All agents > Requests**を開き、申請された `A2A Caller Agent` を選ぶ
3. 詳細と要求されるアクセス許可を確認し、**ストアに公開**を選ぶ
4. 公開ウィザードで利用対象ユーザーとポリシーテンプレートを選び、必要なアクセス許可へ同意して **公開**する
5. 承認後、対象ユーザーが Teams または Microsoft 365 Copilot から呼び出し元エージェントを追加できることを確認する

> Copilot Studio のテストペインだけで開発者テストを行う場合は、組織カタログでの承認を待たずに確認できる。第2部では、組織ユーザーが利用できる管理下の状態にするため承認を実施する。

## 2. Teams から独自エージェントを動かす

**この節が [Observe](./part2-2-observe.md) 以降の前提**。Observe 以降の画面は、エージェントを一度も動かしていないと**何も表示されない**。まずクラウド上のエージェントを実際に呼び出し、観測データ（Run）を作る。

| ![Teams でエージェントから応答が返っている画面](../assets/part2-1c-04-chat.png) |
|:-:|

[1-1 節](#1-1-teams-app-の公開申請を管理者が承認する) で公開・承認した Teams App を通じてエージェントに、**Teams のチャットで話しかける**。

1. Teams › **Apps** で追加した自分のエージェントを開く
2. `こんにちは` や `今日はいい天気ですね` など、適当な会話を送る
3. 応答が返れば、**受信（Teams→エージェント）と送信（エージェント→Teams）の両方**が通っている

## 3. Copilot Studio から A2A 呼び出しを実行する

第1部 C で作成・接続し、[1-2 節](#1-2-a2a-呼び出し元エージェントの申請を管理者が承認する) で承認した `A2A Caller Agent` を使って、独自エージェントへの委譲を実行する。

1. Copilot Studio のテストペイン、Teams、または Microsoft 365 Copilot で `A2A Caller Agent` を開く
2. 次のように、第1部 C 7-1 節で指定した委譲条件に一致する質問を送る

   ```text
  Agent 365 Training Assistantを使って、Agent 365のS2Sとは何か一文で説明して。
   ```

3. 応答が返ることを確認する。Copilot Studio のテストペインでは、アクティビティマップで `Agent 365 Training Assistant` への委譲も確認する

## 4. 両経路の観測データを作る

Teams直呼びとCopilot Studio経由のA2A呼び出しをそれぞれ複数回実行する。Teams入口のトランスポート認証にはBot Appを使うが、実行・観測はどちらの経路も同じAgent 365 Agent Identityへ結び付く。計装のチャネル名はTeams系と`a2a`で分かれる。

[Observe](./part2-2-observe.md) の画面を見栄えよくするために、少し多めに動かしておく：

- **複数回**実行する → Activity / Map の件数が増える。S2S/APIキー経路では人間ユーザーのUserノードが常に生成されるとは限らない
- Teams直呼びとA2A呼び出しを混ぜる → 同じエージェントへの複数経路を確認できる

---

← 戻る：**[第1部 C：Teams + A2A 対応の独自エージェント（S2S）](./part1c-custom-agent.md)** ｜ 次：**[第2部：Observe（観察する）](./part2-2-observe.md)** ｜ [README（概要）](../README.MD)
