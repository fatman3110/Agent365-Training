# 第1部 B：Azure AI Foundry で AI エージェントを作る（開発者）

**ノーコード**で **Microsoft Foundry ポータル**（[ai.azure.com](https://ai.azure.com/)）の「**エージェントの構築**」（コードを書かずに指示・ツール・ナレッジを構成するタイプ。 **Prompt agent** と呼ばれる）を使い、**Microsoft Sentinel MCP** と **Bing Grounding（Web 検索）** を道具として追加し、**Agent 365 に公開申請**するまで。Microsoft のセキュリティ製品に関する質問に、Web 検索と Sentinel のインシデント情報の両方から答える「**セキュリティ Learn ヘルパー**」を作る。

> ⚠️ Microsoft Agent 365 / Foundry は Preview を多く含む。コマンド・API は変わり得るので、Microsoft Learn で最新情報を確認すること。

**目次**

- [第1部 B：Azure AI Foundry で AI エージェントを作る（開発者）](#第1部-bazure-ai-foundry-で-ai-エージェントを作る開発者)
  - [1. Foundry プロジェクトを準備する](#1-foundry-プロジェクトを準備する)
  - [2. ノーコードでエージェントを作る](#2-ノーコードでエージェントを作る)
  - [3. ツールを追加する（Bing Grounding / Microsoft Sentinel MCP）](#3-ツールを追加するbing-grounding--microsoft-sentinel-mcp)
    - [3-1. Bing Grounding（Web 検索）](#3-1-bing-groundingweb-検索)
    - [3-2. Microsoft Sentinel MCP（インシデント参照）](#3-2-microsoft-sentinel-mcpインシデント参照)
  - [4. Agent 365 へ Autopilot として公開する](#4-agent-365-へ-autopilot-として公開する)

## 1. Foundry プロジェクトを準備する

エージェントを作るには、モデルをデプロイ済みの **Microsoft Foundry プロジェクト**が要る。既存のプロジェクトがあればそれを使ってよい。

1. [Foundry ポータル](https://ai.azure.com/) にサインイン
2. プロジェクトが無ければ新規作成

## 2. ノーコードでエージェントを作る

| ![Foundry プロジェクトのホーム画面](../assets/part1b-01-agent-builder.png) |
|:-:|

1. プロジェクトを開くとホーム画面が表示される。右側の **エージェントの構築**（カードの **構築の開始** を選ぶ
2. **エージェントの作成** ダイアログで **エージェント名** を入力する。**英数字で開始・終了し、途中にはハイフンのみ使用可（スペース不可）**。例：`Security-Learn-Helper`
3. **作成** を押すと、そのままエージェントの編集画面（プレイグラウンド）が開く
4. 画面上部の **モデル** ドロップダウンで使うモデルを任意に確認・選択する（テスト用途なのでのままでもよい）
5. **手順** 欄に、下記のようなプロンプトを入力する

   ```text
   あなたは Microsoft のセキュリティ製品（Microsoft Sentinel / Defender / Entra 等）に関する質問に答えるアシスタントです。
   一般的な製品仕様や手順の質問には Web 検索（Bing Grounding）で最新の公式情報を調べて答えてください。
   自組織のインシデントや発生している脅威に関する質問には、Microsoft Sentinel の MCP ツールでインシデント情報を取得して答えてください。
   ```

6. 右上の **保存** を押す

## 3. ツールを追加する（Bing Grounding / Microsoft Sentinel MCP）

エージェント編集画面の **手順** の下に **ツール** セクションがあり、ここでエージェントに使わせる道具を管理する。

### 3-1. Bing Grounding（Web 検索）

新規作成した時点で、**ツール** セクションに既定で **Web検索**（Bing Grounding を使った Web 検索）が追加されている。画面には「追加のコストが発生する」「顧客データは Azure コンプライアンス境界の外に送信される」という注記が出るので内容を確認する。今回はこれをそのまま使う（不要なら項目右の **×** で外せる）。

### 3-2. Microsoft Sentinel MCP（インシデント参照）

> 前提：対象テナントで Microsoft Sentinel／Defender XDR が有効化されており、自分が対象ワークスペースに **Security Reader** 以上のロールを持っていること。

1. **ツール** セクションの **追加** ▾ ボタンを開く（「大人気」「最近使用したもの」のクイックリストが出る）
2. 一覧に無ければ、メニュー下部の **ツールの追加** を選ぶと **ツールの選択** ダイアログが開く
3. **構成済み** タブのまま、検索欄に `Sentinel` と入力する
4. 候補として **MicrosoftSentinelData**（データ探索コレクション。Sentinel のデータ／インシデントに問い合わせる用途）、**MicrosoftSentinelGraph** / **MicrosoftSentinelGraph2**（グラフベースでエンティティ関係を自然言語分析する用途）が表示されるので、目的に合うもの（インシデント関連の質問に答えたいので今回は **MicrosoftSentinelData**）を選ぶ
5. **ツールを追加** を押す
6. 今回の環境ではすでに **構成済み** タブに表示されており追加の認可なく選べたが、初めて接続するテナントではサインイン・同意などの認可（Connection 作成）を求められる場合がある

## 4. Agent 365 へ Autopilot として公開する


1. **プレイグラウンド（Playground）** で一度チャットし、Bing Grounding / Sentinel MCP それぞれを使う質問（例：「Microsoft Sentinel の Analytics ルールとは？」「直近のインシデントを教えて」）で応答を確認する
2. エージェント詳細画面で **公開（Publish）** に類する操作を探し、**Microsoft Teams / Microsoft 365** を選ぶ
3. 公開処理により、Agent 365 側に **Blueprint**（承認待ちのエージェント登録要求）が作成される
4. [第2部 B：承認と観測データ作成（Foundry）](./part2-1b-foundry.md) で AI 管理者が承認する

---

← 戻る：[README（概要）](../README.MD) ｜ 次：**[第2部 B：承認と観測データ作成（Foundry）](./part2-1b-foundry.md)**
