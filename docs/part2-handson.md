# 第2部：Agent 365 ハンズオン（AI 管理者）

> このパートは **AI 管理者**の作業。[Microsoft 365 管理センター](https://admin.microsoft.com/)（Copilot Control System）と [Microsoft Entra 管理センター](https://entra.microsoft.com/) で、[第1部](./part1-setup.md)で作った内容を確認し、ガバナンスを効かせる。
> 参考: [a365handson Step 4（登録・Entra Agent ID・Block）](https://github.com/ninjyanaka/a365handson/blob/main/04-register.md)

## 8. 管理者が承認する（Requests → Publish）

エージェントは承認されて初めて利用可能になる。

1. [Microsoft 365 管理センター](https://admin.microsoft.com/) にサインイン
2. **Agents › All agents › Requests** を開く（`Pending review` / `Pending activate` を確認）
3. 対象エージェントを開く（この時点では **Entra agent ID は「—」**）→ **Publish to store**（承認）
4. 「**Publish new agent**」ウィザードを進める：
   1. **Select users** — インストール可能なユーザー（All users / 特定）を選択
   2. **Apply template** — ポリシーテンプレート。条件付きアクセス（例「Block - High Risky Agent」）等を適用（→ §12）
   3. **Review permissions** — エージェントが要求する権限を確認し、必要なら管理者同意
   4. **Review and finish → Publish**

<!-- ![Requests タブ](../assets/08-requests.png) -->

> **BYO MCP の承認も同様**：**Agents › Tools › Requests (preview)** で `<MCP_NAME>` を開き **Approve** →（`-A365Proxy` / `-BYO` / ランタイムの）管理者同意 → Status が **Available**（承認まで利用不可）。

✅ 承認が完了するとエージェントは `Pending review` から外れ、利用可能になる。

## 9. Entra Agent ID を確認する

承認済みの blueprint を「使える実体」にすると（instance 化）、**Entra Agent ID が「—」から実値の GUID に変わる**。

1. 管理センター › **Agents** で対象 blueprint を開く → **`+ Add instance`**（または対象の登録を有効化）
2. 作成後、blueprint / instance の **Overview の Entra agent ID** が実値化することを確認
3. [Entra 管理センター](https://entra.microsoft.com/) › **Agent identities**（Enterprise apps）で同じ Agent ID が見えることを確認

<!-- ![Entra Agent ID 実値化](../assets/09-agentid.png) -->

> **本教材は非 AI Teammate** のため、**agent user（UPN）や Teams の `@mention` は作られない**（それは AI Teammate 専用）。本エージェントの呼び出しは Copilot Studio カスタムエンジン / REST（App Service の `/chat`）/ OBO クライアント経由で行う。
> この Entra agent ID の値が、そのまま Observability の `agentId` になる（Single Agent Map の突き合わせキー）。

## 10. Agent Registry をタブ別に確認する

管理センター › **Agents › All agents › Registry** で対象を開き、各タブで「登録内容」を確認する。

| タブ | 見るもの |
|------|---------|
| **Details** | Publisher type / Owner / Entra agent ID / Channel |
| **Users** | 利用ユーザー |
| **Data & tools** | Capabilities / Knowledge / **Tools（BYO MCP の echo・now がここに出る）** |
| **Security** | Microsoft Purview（活動監視・機密データ保護）＋ Microsoft Entra（ID 保護・Agent ID）。右上に **Block** |
| **Permissions** | 付与権限（Granted / Delegated） |
| **Activity** | Active users / Sessions / Exceptions と時系列グラフ |

<!-- ![Registry タブ](../assets/10-registry.png) -->

## 11. Single Agent Map で可視化する（Preview）

観測データが、エージェント ↔ ユーザー ↔ ツールの関係図として描かれる。**Map を点灯させるには、クラウド上のエージェントを実際に呼び出して活動を作る**必要がある。

### 11.0 Map 点灯用のアクティビティを作る（クラウドのエージェントを呼ぶ）

承認済み（§8）のエージェントを、クラウド経由で実際に使って観測データを溜める：

- `echo` / `now` を**複数回**呼ぶ → Map の **Tool ノード**が出る（呼ぶほど線が太い）
- **複数ユーザー**で叩く（OBO なので別ユーザーでサインイン）→ **User ノード**が増える
- （デモ映え）ツールを**一定確率で失敗**させ exception rate を **>1%** に → Map で**赤いハイライト線**
- 呼び出し方法：Copilot Studio カスタムエンジン / REST（App Service の `/chat`）/ OBO クライアント

**要件**：E7（Agent 365）＋ Global Administrator か AI Administrator。Usage/観測はテナント **< 4,000 ユーザー**で有効。

1. 管理センター › **Agents › All Agents › Map**
2. **観測データを持つ**自分のエージェントを選択 → サマリ（users / sessions / exceptions）を確認
3. **All connections** を選択 → **Single Agent Map** が開く

| ノード | 内容 |
|--------|------|
| Agent | 詳細・サマリ活動 |
| User（top 50） | クリックでユーザー詳細 |
| Tool（top 50） | tool calls・exception 数・last activity（**echo / now** が出る） |

- **線の太さ** = interaction volume、**exception >1% の線は赤**
- 空表示なら [第1部 §5](./part1-setup.md)（観測配線）と §11.0（アクティビティ生成）を見直す

<!-- ![Single Agent Map](../assets/11-single-agent-map.png) -->

> Single Agent Map は「1 エージェント ↔ ユーザー ↔ ツール」に限定で、**agent-to-agent の線は描かれない**。マルチエージェント化は**テナント全体の Agent Map（クラスタ表示）**を豊かにする用途。

## 12. ガバナンス — Block（Kill Switch）/ 条件付きアクセス / 削除

エージェントを止めるには「**無効化（Block）**」→「**削除（Delete）**」の 2 レベルがある。まず無効化、確証が取れてから削除、が安全な順序。

### 12.1 Block（Kill Switch）— 構成保持のまま即時停止

| 粒度 | 対象 | 効果 |
|------|------|------|
| **Blueprint 単位** | エージェント全体 | 組織全体で利用不可。全ユーザー・全 instance に波及 |
| **Instance 単位** | 個々の instance | その instance だけ停止。他は影響なし |

1. 管理センター › **Agents › All agents** で対象を開く（`Available`）→ 右上 **Block**
2. **Block agent** にチェック、任意で Reason を記入 → **Save**
3. ステータスが **Blocked** に。「removed from all users in your organization」。ボタンは **Unblock** に変化
4. 解除は **Unblock** → チェック → Save で `Available` に復帰

<!-- ![Block / Kill Switch](../assets/12-block.png) -->

### 12.2 条件付きアクセス（テナント全体）

さらに広く止めるなら Entra の条件付きアクセスで「**すべてのエージェント ID**」を対象にトークン発行をブロックできる（既存・新規の Agent ID をまとめて認証不可）。**本番適用前にレポート専用モードで影響を確認**する。

- 出典: [エージェント向け条件付きアクセス](https://learn.microsoft.com/entra/identity/conditional-access/agent-id)

### 12.3 削除（リタイア）と後片付け

| | Block（無効化） | Permanent delete（削除） |
|--|----------------|--------------------------|
| 何が起きる | 認証・トークン発行を止める。オブジェクトは残る | オブジェクトを消す（子も連鎖削除） |
| 構成・データ | 保持（Unblock で復帰） | 失われる（30 日は論理削除で復元可） |
| クォータ | 消費したまま | 完全削除まで消費（250 上限に注意） |

- 個別: instance 詳細 › **Permanent delete**
- 一括（自前ホスト）: 作業ディレクトリで `a365 cleanup`（**破壊的**。config の blueprint 配下を一括削除）
- orphan アプリ確認: `az ad app list --display-name "<blueprint名>" -o table` → `az ad app delete --id <appId>`

> ⚠️ **後片づけ必須**：学習が終わったら Block ではなく `a365 cleanup` で消し、Azure リソース（App Service / Functions）も削除する。連鎖クリーンアップは非同期で数時間〜数日かかることがある。

✅ **完了条件**：管理センターで Block → 実際に停止、Unblock → 復帰、を確認できる。Single Agent Map に自分の agent・Tool（echo/now）・User が描画される。

---

← 戻る：**[第1部：環境構築](./part1-setup.md)** ｜ [README（概要）](../README.MD)
