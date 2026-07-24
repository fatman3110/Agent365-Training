# 第1部 A：Copilot Studio で AI エージェントを作る（開発者）

ノーコード／ローコードの **Microsoft Copilot Studio** でエージェントを作り、Teams / Microsoft 365 Copilot チャネルに公開して、組織のカタログに**申請**するまで。コードも Azure も要らず、最短で「Agent 365 に載る」エージェントを用意できる。

> 💡 自前ホストの LLM やコードでフル制御したいなら **[第1部 B：独自エージェント＋独自 MCP](./part1b-custom-agent.md)** を選ぶ。本ファイル（A）は最短ルート。
>
> ⚠️ Microsoft Agent 365 / Copilot Studio は Preview を多く含む。UI 名やメニュー位置は変わり得るので、詰まったら [Copilot Studio の公開ドキュメント](https://learn.microsoft.com/microsoft-copilot-studio/publication-add-bot-to-microsoft-teams) で最新を確認すること。

**目次**

- [0. 前提を確認する](#0-前提を確認する)
- [1. Copilot Studio でエージェントを作る](#1-copilot-studio-でエージェントを作る)
- [2. 指示・知識・ツールを設定する](#2-指示知識ツールを設定する)
- [3. 公開して組織に申請する](#3-公開して組織に申請する)

完了後は **[第2部 A：承認と観測データ作成](./part2-1a-copilotstudio.md)** で管理者承認と観測データ作成を行い、その後 Observe / Govern / Secure に進む。

## 0. 前提を確認する

| 項目 | 内容 |
|------|------|
| ライセンス | Copilot Studio を利用できるライセンス。**Microsoft 365 Copilot に含まれる**のが一般的（単体の Copilot Studio ライセンス・試用版でも可）。Agent 365 のガバナンス対象にするには Microsoft 365 E7 / Agent 365 が前提 |
| ロール | エージェント作成は各ユーザーで可。組織への公開（申請）の**承認**は AI Administrator / Global Administrator（→ 第2部） |
| アクセス先 | [Copilot Studio](https://copilotstudio.microsoft.com/) にサインインできること |

> このルートは**コード不要**。Azure リソース（App Service / Functions / ACR 等）も作らない。LLM は Copilot Studio 側がホストする。

## 1. Copilot Studio でエージェントを作る

1. [Copilot Studio](https://copilotstudio.microsoft.com/) にサインイン
2. 左ナビ **Create（作成）** → **New agent（新しいエージェント）**
3. 名前・説明・アイコンなどの基本情報を入力（自然言語で「何をするエージェントか」を書くと、雛形が生成される）
4. **Create** で作成。プレビュー画面（**Test（テスト）**）でその場で会話して動作を確認できる

> ここで作るのは Copilot Studio 製のエージェント。第2部で組織に公開すると、Microsoft 365 管理センター（Copilot Control System）の**エージェントレジストリに載り、Agent 365 のガバナンス対象**になる。

## 2. 指示・知識・ツールを設定する

エージェントの中身を作り込む（すべて任意。最小限なら指示だけでよい）。

- **Instructions（指示）** — 役割・口調・してよいこと／いけないことを自然言語で書く
- **Knowledge（知識）** — SharePoint / 公開 Web / ファイルなどを知識源として追加
- **Tools / Actions（ツール）** — コネクタや **MCP サーバー**を追加して外部データ・操作を扱わせる（第1部 B の自作 MCP のような「道具」を、ここではローコードで足す）
- **Topics（トピック）** — 決まった会話フローを定義（必要な場合のみ）

変更したら **Save** し、**Test** で都度確認する。

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
