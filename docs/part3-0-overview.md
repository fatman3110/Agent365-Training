# 第3部（ボーナストラック）：AI Teammate と自作 MCP サーバー

第1〜2部で作った **S2S エージェント**とは別軸として、**独自の M365 ID を持つ AI Teammate** と、**自作の MCP サーバー（BYO MCP）** を作り、最後に両者を統合する。**第1〜2部の環境・リソースには一切変更を加えず、すべて新規追加**で進める。

> ⚠️ **新しい前提：AI Teammate は Frontier preview 限定**
> 第3部 は、 **[Microsoft Frontier preview プログラム](https://adoption.microsoft.com/copilot/frontier-program/) に登録済みのテナントでのみ**作成できる。

> ⚠️ Microsoft Agent 365 / Frontier / BYO MCP は Preview を多く含む。コマンド・API・提供リージョンは変わり得るので、Microsoft Learn で最新を確認すること。

---

## 第3部の構成

| 章 | 内容 | 主眼 |
|----|------|------|
| **3-A：AI Teammate を作る** → [part3-1-ai-teammate.md](./part3-1-ai-teammate.md) | 独自 M365 ID（UPN/メールボックス/Teams 在席）を持つエージェントを作る。頭脳は **Microsoft Foundry のクラウドモデル**（自前 Qwen 不要） | 「エージェントが"人"としてふるまう」identity モデルの体験 |
| **3-B：自作 MCP サーバー（BYO MCP）** → [part3-2-byo-mcp.md](./part3-2-byo-mcp.md) | 簡易なリモート MCP サーバーを実装・ホストし、`a365 develop-mcp` で A365 に登録・承認 | 「MCP は Gateway 経由で初めて A365 に載る」を実体験 |
| **3-C：統合** → [part3-3-integrate.md](./part3-3-integrate.md) | AI Teammate（A）から自作 MCP（B）をツールとして呼ぶ | 独自 ID エージェント × 自作ツールのエンドツーエンド |

---

## 用語の整理：「Foundry autopilot」と「AI Teammate」は別物

第1部 B で作った Foundry 公開（autopilot）と、第3部 A の AI Teammate は**アイデンティティのレイヤーが違う**。

| | 第1部B：Foundry autopilot | 第3部A：AI Teammate |
|---|---|---|
| ID | Entra **Agent ID**（サービス的） | **独自 M365 ユーザー ID（UPN）** |
| メールボックス / Teams 在席 | なし | **あり**（人のように @mention・会議招待・メール可） |
| 組織図 | 載らない | **マネージャー配下に載る** |
| 提供条件 | GA 相当 | **Frontier preview 限定** |
| 作り方 | Foundry で公開（autopilot） | AI ガイド付きセットアップ `a365 setup all --aiteammate --m365` |

> 第3部 A は「**identity レイヤー = AI Teammate（Frontier）**」＋「**頭脳 = Foundry モデル**」の組み合わせで作る。

---

## 第1部C（S2S）との対比（学びのポイント）

| 観点 | 第1部C：独自エージェント | 第3部A：AI Teammate |
|---|---|---|
| 認証モデル | **S2S（サービスプリンシパル）** | **agentic-user（独自 M365 ID）** |
| `a365 setup all` フラグ | `--authmode s2s` | `--aiteammate --m365`（`--authmode` は使わない） |
| 呼び出しユーザーの権限 | 継承しない（**アプリ権限＝自分の SP** で動く） | 継承しない（**自分のユーザー ID・権限**で動く。呼び出しユーザーの権限は引き継がない） |
| モデル | 自前 Qwen（Ollama sidecar） | Foundry クラウドモデル |

> 出典（AI Teammate は呼び出しユーザーの権限を継承しない）: [Get started with Agent 365 development](https://learn.microsoft.com/microsoft-agent-365/developer/get-started#adding-agent-365-capabilities-incrementally)

---

## 命名規則とリソース分離

- **`xxxx` は自分用のユニークな文字列**に置換して使う（第1部と同じ方式。テスト環境の `SGT31` 等は使わない）。
- **既存の `rg-agent365-training` を再利用**し、**別名**で新規作成（既存 `app-...-agent-xxxx` 等には触れない）。

```powershell
$RG        = "rg-agent365-training"                 # 既存 RG を再利用（変更しない）
$LOC       = "japaneast"
# --- 3-A：AI Teammate ---
$TMNAME    = "a365-teammate-xxxx"                    # AI Teammate の a365 --agent-name（20 文字以内）
# --- 3-B：自作 MCP ---
$MCPAPP    = "app-agent365-training-mcp-xxxx"        # 自作 MCP をホストする Web アプリ（世界で一意）
$MCPNAME   = "mcp-custom-xxxx"                       # BYO 登録時の server-name
```

- 新規コードは **`src/ai-teammate/`**（A）、**`src/mcp-server/`**（B）に配置（既存 `src/agent/` は変更しない）。

---

## 前提・ライセンス

| 項目 | 要件 |
|---|---|
| AI Teammate（A） | **Frontier preview 登録** ＋ E7/Agent 365、Teams |
| 自作 MCP（B） | Agent 365（BYO MCP は preview・リージョン依存）、承認に **AI Administrator / Global Administrator** |
| 統合（C） | A・B の完了 |

---

← 戻る：[README（概要）](../README.MD) ｜ 次：**[3-A：AI Teammate を作る](./part3-1-ai-teammate.md)**
