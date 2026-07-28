# 第1部 B：Microsoft Foundry で AI エージェントを作る（開発者）

**ノーコード**で **Microsoft Foundry ポータル**（[ai.azure.com](https://ai.azure.com/)）の「**エージェントの構築**」（コードを書かずに指示・ツール・ナレッジを構成するタイプ。 **Prompt agent** と呼ばれる）を使い、**Microsoft Sentinel MCP** と **Bing Grounding（Web 検索）** を道具として追加し、**Agent 365 に公開申請**するまで。Microsoft のセキュリティ製品に関する質問に、Web 検索と Sentinel のインシデント情報の両方から答える「**セキュリティ Learn ヘルパー**」を作る。

> ⚠️ Microsoft Agent 365 / Foundry は Preview を多く含む。コマンド・API は変わり得るので、Microsoft Learn で最新情報を確認すること。

**目次**

- [第1部 B：Microsoft Foundry で AI エージェントを作る（開発者）](#第1部-bmicrosoft-foundry-で-ai-エージェントを作る開発者)
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

1. プロジェクトを開くとホーム画面が表示される。右側の **エージェントの構築** カードの **構築の開始** を押す
2. **エージェントの作成** ダイアログで **エージェント名** を入力する。**英数字で開始・終了し、途中にはハイフンのみ使用可（スペース不可）**。例：`Security-Learn-Helper`
3. **作成** を押すと、そのままエージェントの編集画面（プレイグラウンド）が開く
4. 画面上部の **モデル** ドロップダウンで使うモデルを確認し、必要なら選ぶ（テスト用途なのでそのままでもよい）
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

新規作成した時点で、**ツール** セクションに既定で **Web検索**（Bing Grounding を使った Web 検索）が追加されている。

### 3-2. Microsoft Sentinel MCP（インシデント参照）


1. **ツール** セクションの **追加** ボタンを開く
2. メニュー下部の **ツールの追加** を選ぶと **ツールの選択** ダイアログが開く
3. **構成済み** タブのまま、検索欄に `Sentinel` と入力する
4. **MicrosoftSentinelData**　を選択
5. **ツールを追加** を押す

## 4. Agent 365 へ Autopilot として公開する


1. **プレイグラウンド（Playground）** で一度チャットし、Bing Grounding / Sentinel MCP それぞれを使う質問で応答を確認する
   - Bing Grounding を狙う質問例：「Agent 365 ってどのような仕組みですか？」
   - Sentinel MCP を狙う質問例：「直近のインシデントを教えて」
2. エージェント詳細画面右上の **発行する** を開き、**Teams と Microsoft 365 Copilot** を選ぶ
3. **「Teams と Microsoft 365 に対して発行する」** ダイアログが開くので、必須項目を入力する
   - **エージェント名**：既定でエージェント名（例：`Security-Learn-Helper`）が入っている
   - **発行バージョン**：`1.0.0` のように x.y.z 形式で指定
   - **短い説明**：一覧表示用の短い説明文。例：`Microsoft セキュリティ製品に関する質問に Web 検索とSentinel のインシデント情報で答えるヘルパーです。`
   - **説明**：エージェントの機能と使いどころの説明。例：`Microsoft Sentinel / Defender / Entra などのセキュリティ製品に関する質問に答えます。製品仕様や手順は Web 検索（Bing Grounding）で、自組織のインシデントや脅威に関する質問は Microsoft Sentinel の MCP ツールで調べて回答します。`
   - **作成者 › 開発者**：開発者名を入力
   - 入力後 **次へ：発行オプション** を押す
4. **直接発行** タブで、**このエージェントを使用できるユーザー** で **組織内のユーザー** を選び、 **発行** を押す
5. これにより、Agent 365 側に承認待ちのエージェント登録要求が作成される
6. [第2部 B：承認と観測データ作成（Foundry）](./part2-1b-foundry.md) で AI 管理者が承認する

---

← 戻る：[README（概要）](../README.MD) ｜ 次：**[第2部 B：承認と観測データ作成（Foundry）](./part2-1b-foundry.md)**
