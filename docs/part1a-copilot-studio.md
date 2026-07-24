# 第1部 A：Copilot Studio で AI エージェントを作る（開発者）

ノーコード／ローコードの **Microsoft Copilot Studio** でエージェントを作り、Teams / Microsoft 365 Copilot チャネルに公開して、組織のカタログに**申請**するまで。


> ⚠️ ⚠️ Microsoft Agent 365 は Preview を多く含む。コマンド・API は変わり得るので、Microsoft Learn で最新情報を確認すること。

**目次**

- [0. 前提を確認する](#0-前提を確認する)
- [1. Copilot Studio でエージェントを作る](#1-copilot-studio-でエージェントを作る)
- [2. 指示・知識・ツールを設定する](#2-指示知識ツールを設定する)
- [3. 公開して組織に申請する](#3-公開して組織に申請する)

## 1. Copilot Studio でエージェントを作る

1. [Copilot Studio](https://copilotstudio.microsoft.com/) にサインイン（画面上部の **Environment**（環境）セレクターで対象環境を確認）
2. **Home（ホーム）** ページの入力ボックスに、作りたいことを**自然言語で説明**して送る（AI が名前・説明・指示・知識・ツールの候補を生成する）。あるいは次のどちらか：
   - **Home** ページの **Start building from scratch（ゼロから作成）** → **Create an agent（エージェントを作成）**
   - 左ペインの **Agents** → **Create blank agent（空のエージェントを作成）**
3. プロビジョニング（数十秒）の後、エージェントの **Overview（概要）** ページが開く（Details / Instructions / Model / Starter prompts / Knowledge の各セクションが並ぶ）
4. 名前・説明を整え、**Save**。**Test / Preview** ペインでその場で会話して動作を確認できる

出典: [Create and delete agents](https://learn.microsoft.com/microsoft-copilot-studio/authoring-first-bot) ｜ [Quickstart: Create and deploy an agent](https://learn.microsoft.com/microsoft-copilot-studio/fundamentals-get-started)

> ここで作るのは Copilot Studio 製のエージェント。第2部で組織に公開すると、Microsoft 365 管理センター（Copilot Control System）の**エージェントレジストリに載り、Agent 365 のガバナンス対象**になる。

## 2. 指示・知識・ツールを設定する

エージェントの中身を作り込む（すべて任意。最小限なら指示だけでよい）。上部タブは **Overview / Knowledge / Tools / Agents / Topics / Activity / Analytics / Channels**。

- **Instructions（指示）** — **Overview** ページの Instructions セクションに、役割・口調・してよいこと／いけないことを自然言語で書く（最大 8,000 文字）
- **Model（モデル）** — Overview で使う AI モデルを選ぶ
- **Knowledge（知識）** — 上部タブ **Knowledge** から SharePoint / 公開 Web / ファイルを知識源として追加
- **Tools（ツール）** — 上部タブ **Tools** から **+ Add tool** でコネクターや **MCP サーバー**を追加（第1部 B の自作 MCP のような「道具」を、ここではローコードで足す）
- **Topics（トピック）** — 上部タブ **Topics** で決まった会話フローを定義（必要な場合のみ）

変更したら **Save** し、**Test** ペインで都度確認する。

> 道具（ツール）を組織へ展開するには、エージェント本体とは別に管理者の承認が要ることがある（第2部で扱う）。

## 3. 公開して組織に申請する

作っただけでは他のユーザーは使えない。**公開（Publish）してチャネルに接続し、組織カタログへ申請**する。

1. 右上の **Publish** でエージェントを公開する
2. **Channels（チャネル）** ページ → **Teams and Microsoft 365 Copilot**（Microsoft 365 と Microsoft Teams）を開く
3. **Turn on Microsoft 365** の「Make agent available in Microsoft 365 Copilot」を有効にすると、Teams と Microsoft 365 Copilot の両方で使えるようになる（Teams だけにするなら無効のまま）
4. **Add channel** でチャネルを追加
5. **Show to the organization（組織に表示）** を選び、**組織カタログへの掲載を申請**する（この操作で管理者承認へ回る）

出典: [Connect and configure an agent for Teams and Microsoft 365](https://learn.microsoft.com/microsoft-copilot-studio/publication-add-bot-to-microsoft-teams) ｜ [Manage requested agents](https://learn.microsoft.com/microsoft-365/copilot/agent-essentials/agent-lifecycle/agent-copilot-studio-requested)

> 組織への申請を出すと、エージェントは Microsoft 365 管理センター（Copilot Control System）の **Requests（申請）** に現れ、管理者の承認待ちになる。テスト段階では **Built with Power Platform** セクション（共有）に出す方法もあり、管理者承認なしで自分だけ試せる。

---

→ 次：**[第2部 A：承認と観測データ作成](./part2-1a-copilotstudio.md)** ｜ [README（概要）](../README.MD)
