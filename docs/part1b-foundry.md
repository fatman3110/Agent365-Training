# 第1部 B：Azure AI Foundry で AI エージェントを作る（開発者）

**ノーコード**で **Microsoft Foundry ポータル**（[ai.azure.com](https://ai.azure.com/)）の **Agent Builder** を使い、**Prompt agent**（プロンプトとツール構成だけで宣言的に定義するエージェント。コードは書かない）を作って、**Microsoft Sentinel MCP** と **Bing Grounding** を道具として追加し、**Agent 365 に Autopilot として公開申請**するまで。今回は具体例として、Microsoft のセキュリティ製品に関する質問に、Web 検索と Sentinel のインシデント情報の両方から答える「**セキュリティ Learn ヘルパー**」を作る。

> ⚠️ Microsoft Agent 365 / Foundry Agent Service は Preview を多く含む。UI 名やメニュー位置は変わり得るので、詰まったら Microsoft Learn で最新を確認すること。
>
> ⚠️ **本節の「5. Agent 365 へ Autopilot として公開する」の画面手順は、公式 Learn 上に Prompt agent 専用の詳細な how-to がまだ無く、一部を対応表（[Foundry と Agent 365 の統合](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-365-integration)）からの推定で記載している。実際のポータル画面で操作しながら確認・修正すること。**

**目次**

- [1. 前提の確認](#1-前提の確認)
- [2. Foundry プロジェクトを準備する](#2-foundry-プロジェクトを準備する)
- [3. Agent Builder で Prompt agent を作る](#3-agent-builder-で-prompt-agent-を作る)
- [4. ツールを追加する（Bing Grounding / Microsoft Sentinel MCP）](#4-ツールを追加するbing-grounding--microsoft-sentinel-mcp)
- [5. Agent 365 へ Autopilot として公開する](#5-agent-365-へ-autopilot-として公開する)

## 1. 前提の確認

Prompt agent は Foundry ポータルだけで作れるが、**Agent 365 への Autopilot 公開**には次の前提がテナント側に必要（詳細は [README の前提条件](../README.MD#前提条件)を参照）：

- テナントが **Frontier Preview Program** に登録済みであること（公式 Learn に「Foundry→Agent 365 のデータ連携の前提条件」と明記）
- 最低 1 名が **Microsoft 365 Copilot** など Agent 365 の対象ライセンスを保有していること
- Global Administrator が [Microsoft 365 管理センター](https://admin.microsoft.com/) で Agent 365 を有効化し、利用規約に同意済みであること
- 自分自身は Foundry プロジェクトスコープの **Foundry User** または **Foundry Project Manager** ロールを持っていること

## 2. Foundry プロジェクトを準備する

Prompt agent を作るには、モデルをデプロイ済みの **Microsoft Foundry プロジェクト**が要る。既存のプロジェクトがあればそれを使ってよい。

1. [Foundry ポータル](https://ai.azure.com/) にサインイン
2. プロジェクトが無ければ新規作成（モデル：テスト用途なので `gpt-4.1` や `gpt-5-mini` など軽量なものでよい）
3. 左ペインの **エージェント（Agents）** セクションを開く

## 3. Agent Builder で Prompt agent を作る

| ![Foundry Agent Builder 画面](../assets/part1b-01-agent-builder.png) |
|:-:|

1. **エージェント › + 新規作成（New agent）** を選ぶ
2. 種類は **Prompt agent**（プロンプトとツールだけで作る、コード不要のタイプ）を選ぶ
3. 名前に **`Security Learn Helper`** と入力
4. **モデル** に、手順 2 でデプロイしたモデルを選択
5. **指示（Instructions）** に、下記のようなプロンプトを入力して保存

   ```text
   あなたは Microsoft のセキュリティ製品（Microsoft Sentinel / Defender / Entra 等）に関する質問に答えるアシスタントです。
   一般的な製品仕様や手順の質問には Web 検索（Bing Grounding）で最新の公式情報を調べて答えてください。
   自組織のインシデントや発生している脅威に関する質問には、Microsoft Sentinel の MCP ツールでインシデント情報を取得して答えてください。
   ```

## 4. ツールを追加する（Bing Grounding / Microsoft Sentinel MCP）

Prompt agent はポータルの **ツールを追加（Add tool）** から道具を足せる。今回は 2 つ追加する。

### 4-1. Bing Grounding（Web 検索）

1. エージェント編集画面の **ツール › + ツールを追加** を開く
2. **Grounding with Bing Search** を選ぶ（Microsoft 提供の組み込みツール。GA）
3. 案内に従って Bing Search リソースとの接続を作成（無ければ新規作成）し、エージェントに追加する

### 4-2. Microsoft Sentinel MCP（インシデント参照）

> 前提：対象テナントで Microsoft Sentinel／Defender XDR が有効化されており、自分が対象ワークスペースに **Security Reader** 以上のロールを持っていること。

1. 同じく **+ ツールを追加** から、検索欄に `Sentinel` と入力
2. **Microsoft Sentinel** の MCP ツールコレクションを選ぶ
3. 用途に応じたコレクション（例：**triage** — `ListIncidents` / `GetIncidentById` / `ListAlerts` / `GetAlertByID` を含む）を選択して **接続（Connect）**
4. 案内される認可（サインイン／同意）を完了する

## 5. Agent 365 へ Autopilot として公開する

> ⚠️ 以下は [Foundry と Agent 365 の統合](https://learn.microsoft.com/azure/foundry/agents/concepts/agent-365-integration) の対応表（Prompt agent は Registry sync / Autopilot publishing ともに ✅）に基づく想定手順。**Hosted Agent 向けの [Publish an autopilot in Microsoft Agent 365](https://learn.microsoft.com/azure/foundry/agents/how-to/agent-365) は公式 how-to があるが、Prompt agent 専用の詳細な画面操作手順は Learn 上でまだ見つかっていない**。実際にポータルを操作し、以下を出発点に確認すること。

1. **プレイグラウンド（Playground）** で一度チャットし、Bing Grounding / Sentinel MCP それぞれを使う質問（例：「Microsoft Sentinel の Analytics ルールとは？」「直近のインシデントを教えて」）で応答を確認する
2. エージェント詳細画面で **公開（Publish）** に類する操作を探し、**Microsoft Teams / Microsoft 365** または **Agent 365** 向けの公開（Autopilot 化）を選ぶ
3. 公開処理により、Agent 365 側に **Blueprint**（承認待ちのエージェント登録要求）が作成される
4. ここまで済めば、[第2部 B：承認と観測データ作成（Foundry）](./part2-1b-foundry.md) で AI 管理者が承認する

---

← 戻る：[README（概要）](../README.MD) ｜ 次：**[第2部 B：承認と観測データ作成（Foundry）](./part2-1b-foundry.md)**
