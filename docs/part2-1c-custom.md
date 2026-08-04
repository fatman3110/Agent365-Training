# 第2部 C：Teams と Copilot Studio A2A から実行する｜AI 管理者・開発者

[第1部 C](./part1c-custom-agent.md) で作った **Teams + A2A 対応の独自エージェント（S2S）** を管理者が承認し、Teamsから直接実行する。続いて、Copilot Studioに呼び出し元エージェントを作成し、外部Agent2Agentとして接続して実行する。2つの経路から観測データを作ることで、この後の **[Observe](./part2-2-observe.md) → [Govern](./part2-3-govern.md) → [Secure](./part2-4-secure.md)** を確認できる。

> ℹ️ Copilot Studio で作った場合は **[第2部 A](./part2-1a-copilotstudio.md)** を参照。Observe / Govern / Secure は A・B・C 共通。

> ⚠️ Microsoft Agent 365 は Preview を多く含む。コマンド・API は変わり得るので、Microsoft Learn で最新情報を確認すること。

**目次**

- [第2部 C：Teams と Copilot Studio A2A から実行する｜AI 管理者・開発者](#第2部-cteams-と-copilot-studio-a2a-から実行するai-管理者開発者)
  - [1. Teams に接続し、承認を得て「管理下」に置く](#1-teams-に接続し承認を得て管理下に置く)
    - [1-1. Teams App の公開申請を管理者が承認する](#1-1-teams-app-の公開申請を管理者が承認する)
  - [2. Teams から独自エージェントを動かす](#2-teams-から独自エージェントを動かす)
  - [3. Copilot Studio に A2A 呼び出し元エージェントを作る](#3-copilot-studio-に-a2a-呼び出し元エージェントを作る)
    - [3-1. 呼び出し元エージェントを作る](#3-1-呼び出し元エージェントを作る)
    - [3-2. 独自エージェントを Agent2Agent で接続する](#3-2-独自エージェントを-agent2agent-で接続する)
    - [3-3. A2A 委譲をテストする](#3-3-a2a-委譲をテストする)
  - [4. 両経路の観測データを作る](#4-両経路の観測データを作る)

## 1. Teams に接続し、承認を得て「管理下」に置く

### 1-1. Teams App の公開申請を管理者が承認する

[第1部 C 6 節](./part1c-custom-agent.md#6-teams-app-packagemanifestjson--m365agentsymlを作る) で公開（`publish` コマンドの実行）まで済ませた Teams App Package を、管理者が承認して組織で使える状態にする。


1. [Microsoft 365 管理センター](https://admin.microsoft.com/) を開く › 左ナビ **設定 › 統合アプリ** を選択。
2. **要求されたアプリ** タブを開くと、対象アプリ（例: `agent365-xxxx` / ホスト製品 `Teams`）が **状態: 公開保留中** で一覧に出ている。
3. アプリ名をクリックして開き、内容を確認のうえ承認（公開）する。
4. 承認後、組織のユーザーが Teams の「アプリ」からこのエージェントを追加できるようになる（反映まで時間がかかる場合あり）。

## 2. Teams から独自エージェントを動かす

**この節が [Observe](./part2-2-observe.md) 以降の前提**。Observe 以降の画面は、エージェントを一度も動かしていないと**何も表示されない**。まずクラウド上のエージェントを実際に呼び出し、観測データ（Run）を作る。

| ![Teams でエージェントから応答が返っている画面](../assets/part2-1c-04-chat.png) |
|:-:|

[1-1 節](#1-1-teams-app-の公開申請を管理者が承認する) で公開・承認した Teams App を通じてエージェントに、**Teams のチャットで話しかける**。

1. Teams › **Apps** で追加した自分のエージェントを開く
2. `こんにちは` や `今日はいい天気ですね` など、適当な会話を送る
3. 応答が返れば、**受信（Teams→エージェント）と送信（エージェント→Teams）の両方**が通っている

## 3. Copilot Studio に A2A 呼び出し元エージェントを作る

この節は **Copilot Studioでエージェントを作成・編集できる開発者**が実施する。第1部Cの独自エージェントを作り直すのではなく、呼び出しを委譲する親エージェントを新しく作る。

### 3-1. 呼び出し元エージェントを作る

1. [Copilot Studio](https://copilotstudio.microsoft.com/) を開き、画面上部で対象環境を確認する
2. 左ペイン **エージェント**から **空のエージェントを作成**を選ぶ
3. 名前を `A2A Caller Agent` とする
4. 説明へ次を入力して保存する

  ```text
  Agent 365トレーニング用の独自S2Sエージェントへ、A2Aで処理を委譲するエージェント
  ```

5. 指示へ次を入力して保存する

  ```text
  Agent 365、S2S、独自エージェント、A2A に関する質問は、
  必ず A365 Training Agent に委譲すること。委譲先の回答をそのまま利用者へ返すこと。
  ```

### 3-2. 独自エージェントを Agent2Agent で接続する

1. 呼び出し元エージェントの **エージェント**ページで **エージェントを追加**を選ぶ
2. **外部エージェントに接続 > Agent2Agent**を選ぶ
3. 次の値を設定する

  | 項目 | 設定値 |
  |---|---|
  | エージェント エンドポイント URL | `https://<APP>.azurewebsites.net/a2a` |
  | 名前 | `Training Child Agent` |
  | 説明 | `Agent 365のトレーニングに関する質問へ日本語で回答するS2Sエージェント` |
  | 認証 | **API キー** |
  | タイプ | **ヘッダー** |
  | ヘッダー名 | `X-A2A-API-Key` |

4. **作成**を選ぶ。この画面ではAPIキーの値を入力しない
5. 次の接続選択画面で **新しい接続を作成**を選び、APIキー値を貼り付けて接続を作成する
6. 作成した接続を選択し、**追加して構成**を選ぶ

APIキー値は、第1部Cを実施した開発者がApp Serviceから直接クリップボードへ取得する。画面、チャット、ファイルへ平文表示しない。

```powershell
$settings = az webapp config appsettings list -n $APP -g $RG -o json | ConvertFrom-Json
$a2aKey = ($settings | Where-Object name -eq "A2A_API_KEY" | Select-Object -First 1).value
Set-Clipboard -Value $a2aKey
```

### 3-3. A2A 委譲をテストする

1. Copilot Studioのテストペインを開く
2. 次のように、3-1で指定した委譲条件に一致する質問を送る

  ```text
  A365 Training Agentを使って、Agent 365のS2Sとは何か一文で説明して。
  ```

3. アクティビティマップで`A365 Training Agent`への委譲が発生したことを確認する

## 4. 両経路の観測データを作る

Teams直呼びとCopilot Studio経由のA2A呼び出しをそれぞれ複数回実行する。Teams入口のトランスポート認証にはBot Appを使うが、実行・観測はどちらの経路も同じAgent 365 Agent Identityへ結び付く。計装のチャネル名はTeams系と`a2a`で分かれる。

[Observe](./part2-2-observe.md) の画面を見栄えよくするために、少し多めに動かしておく：

- **複数回**実行する → Activity / Map の件数が増える。S2S/APIキー経路では人間ユーザーのUserノードが常に生成されるとは限らない
- Teams直呼びとA2A呼び出しを混ぜる → 同じエージェントへの複数経路を確認できる

---

← 戻る：**[第1部 C：Teams + A2A 対応の独自エージェント（S2S）](./part1c-custom-agent.md)** ｜ 次：**[第2部：Observe（観察する）](./part2-2-observe.md)** ｜ [README（概要）](../README.MD)
