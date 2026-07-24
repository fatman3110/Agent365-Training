# 第2部 B：承認と観測データ作成（独自エージェント）｜AI 管理者

[第1部 B](./part1b-custom-agent.md) で作った**独自エージェント＋独自 MCP** を、管理者が承認して Teams に接続し、実際に動かして観測データを作るまで。ここまで済ませると、この後の **[Observe](./part2-2-observe.md) → [Govern](./part2-3-govern.md) → [Secure](./part2-4-secure.md)** の画面にデータが出るようになる。

> ℹ️ Copilot Studio で作った場合は **[第2部 A](./part2-1a-copilotstudio.md)** を参照。Observe / Govern / Secure は A・B 共通。
>
> ⚠️ Microsoft Agent 365 は Preview を多く含む。コマンド・API・UI は変わり得るので、詰まったら [Microsoft Learn](https://learn.microsoft.com/ja-jp/microsoft-agent-365/overview) で最新を確認すること。

**目次**

- [1. 承認して「管理下」に置く](#1-承認して管理下に置く)
- [2. エージェントを実際に動かす（観測データを作る）](#2-エージェントを実際に動かす観測データを作る)

## 1. 承認して「管理下」に置く

エージェントは**承認されて初めて**利用可能になり、Agent ID が実体化して観察・統制・保護の対象になる。

### 1-1. エージェントを承認する（Requests → Publish）

1. [Microsoft 365 管理センター](https://admin.microsoft.com/) にサインイン
2. **Agents › All agents › Requests** を開く（`Pending review` / `Pending activate` を確認）
3. 対象エージェントを開く（この時点では **Entra agent ID は「—」**）→ **Publish to store**（承認）
4. 「**Publish new agent**」ウィザードを進める：
   1. **Select users** — インストール可能なユーザー（All users / 特定）を選択
   2. **Apply template** — ポリシーテンプレート（既定 / カスタム）を選ぶ（下の注記参照）
   3. **Review permissions** — エージェントが要求する権限を確認し、必要なら管理者同意
   4. **Review and finish → Publish**

<!-- ![Requests タブ](../assets/08-requests.png) -->

> **ポリシーテンプレート／条件付きアクセスは「事前準備」が要る（重要）**
> - **カスタムテンプレート**を使うなら、**先に Entra でポリシーを作成**しておく必要がある（未作成だとテンプレート作成時に選べない）。CA・アクセスパッケージ・カスタムセキュリティ属性の**フル手順**は [Govern：カスタムポリシーテンプレートを作る](./part2-3-govern.md#5-カスタムポリシーテンプレートを作る) を参照。作成後、テンプレートに束ねてこのウィザードで選ぶ。
> - すぐ進めたいなら、まず **既定テンプレート（全エージェント用）** を選べばよい（カスタムは後回しでも可）。
> - ⚠️ **テンプレートは「新規アクティブ化時のみ」適用**。**承認済みのエージェントには後付けできない**（[Learn FAQ](https://learn.microsoft.com/microsoft-agent-365/admin/policy-template#select-a-template)）。後から統制を足す／変える場合は、テンプレートではなく **Entra の CA を直接更新**する（対象エージェント ID に動的に効く）。テンプレートを当て直すにはエージェントの作り直しになる。
> - 出典: [Learn: ポリシーテンプレート](https://learn.microsoft.com/microsoft-agent-365/admin/policy-template)

✅ 承認が完了するとエージェントは `Pending review` から外れ、利用可能になる。

### 1-2. 自作 MCP（道具）を承認する

エージェント本体（1-1 節）とは**別の承認**が必要。第1部で登録申請した自作 MCP（`echo` / `now`）を、管理者が承認して初めてエージェントから呼べるようになる。

1. [Microsoft 365 管理センター](https://admin.microsoft.com/) › **Agents › Tools › Requests (preview)** を開く
2. 対象の MCP（[第1部 B](./part1b-custom-agent.md) の `$MCP` の表示名）を開く → **Approve**
3. 求められた管理者同意を付与する（`-A365Proxy` / `-BYO` / ランタイム用のアプリ登録に対する同意）
4. Status が **Available** に変われば承認完了（承認まではエージェントから呼び出せない）

<!-- ![Tools Requests](../assets/08b-tools-requests.png) -->

> **エージェント（1-1 節）と MCP（1-2 節）は別々に承認する**。両方を Approve して初めて、エージェントが道具を呼べる状態になる。

### 1-3. Teams / Copilot チャネルに接続する

承認しただけでは、まだ Teams からメッセージは届かない。**Teams 開発者ポータルで「宛先（Notification URL）」を設定**して、エージェントを Microsoft 365 のメッセージ基盤に繋ぐ。

1. [第1部 B](./part1b-custom-agent.md) で生成された `a365.generated.config.json` の `agentBlueprintId` をコピー
2. ブラウザで開く：`https://dev.teams.microsoft.com/tools/agent-blueprint/<agentBlueprintId>/configuration`
3. **Agent Type = API Based**、**Notification URL = messagingEndpoint**（`a365.generated.config.json` の値）を設定 → **Save**
4. Teams › **Apps** でエージェント名を検索 → **Request Instance / Add**。要求はテナント管理者の承認に回る（[管理センター Requested Agents](https://admin.cloud.microsoft/#/agents/all/requested)）
5. 承認後、Teams でエージェントとチャットできるようになる（→ 2 節 で実際に動かす）

出典: [Learn: エージェントインスタンスの作成](https://learn.microsoft.com/microsoft-agent-365/developer/create-instance)

<!-- ![Teams Developer Portal 設定](../assets/09-devportal.png) -->

> **AI Teammate との違い**：`@mention`・専用メールボックス・組織図掲載まで行う「AI Teammate」は **Frontier Preview 限定**（[Learn](https://learn.microsoft.com/microsoft-agent-365/developer/get-started#types-of-agents)）。本教材の非 AI Teammate エージェントは **API ベースの bot として Teams で会話**できるところまで。
> この blueprint の Entra agent ID（`agentBlueprintId`）が、そのまま Observability の `agentId` になる（Single Agent Map の突き合わせキー）。

## 2. エージェントを実際に動かす（観測データを作る）

**この節が [Observe](./part2-2-observe.md) 以降の前提**。Observe 以降の画面は、エージェントを一度も動かしていないと**何も表示されない**。まずクラウド上のエージェントを実際に呼び出し、観測データ（Run）を作る。

### 2-1. エージェントに話しかける（Teams）

1-3 節 で Teams に接続したエージェントに、**Teams のチャットで話しかける**（これが現実の利用チャネル）。

1. Teams › **Apps** で追加した自分のエージェントを開く
2. `echo こんにちは` や `今何時？`（`now`）などと送る
3. 応答が返れば、**受信（Teams→エージェント）と送信（エージェント→Teams）の両方**が通っている

> OBO（委任）なので、エージェントは**話しかけたユーザーの代理**として動く。監査ログにも「誰の代理か」が残る。
> 開発中のローカル確認だけなら、App Service の `/chat` に直接 REST してもよい：`curl -X POST "https://$APP.azurewebsites.net/chat" -H "Content-Type: application/json" -d '{"message":"echo hi"}'`（ただし Teams 経由と違い、観測のユーザー属性は付かない場合がある）。

### 2-2. 観測データを厚くするコツ

[Observe](./part2-2-observe.md) の画面を見栄えよくするために、少し多めに動かしておく：

- `echo` / `now` を**複数回**呼ぶ → Map の **Tool ノード**が出る（呼ぶほど線が太い）
- **複数ユーザー**で叩く（OBO なので別ユーザーでサインイン）→ **User ノード**が増える
- （デモ映え）ツールを**一定確率で失敗**させ exception rate を **>1%** に → Map で**赤いハイライト線**

> **要件**：E7（Agent 365）＋ Global Administrator か AI Administrator。Usage / 観測はテナント **< 4,000 ユーザー**で有効。反映には数分〜十数分のタイムラグがある。

---

← 戻る：**[第1部 B：独自エージェント＋独自 MCP](./part1b-custom-agent.md)** ｜ 次：**[第2部：Observe（観察する）](./part2-2-observe.md)** ｜ [README（概要）](../README.MD)
