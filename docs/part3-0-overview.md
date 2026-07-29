# 第3部（ボーナストラック）：AI Teammate と自作 MCP サーバー

第1〜2部で作った **S2S エージェント**とは別軸として、**独自の M365 ID を持つ AI Teammate** と、**自作の MCP サーバー（BYO MCP）** を作り、最後に両者を統合する。**第1〜2部の環境・リソースには一切変更を加えず、すべて新規追加**で進める。

> ⚠️ **新しい前提：AI Teammate は Frontier preview 限定**
> 第3部 は、 **[Microsoft Frontier preview プログラム](https://adoption.microsoft.com/copilot/frontier-program/) に登録済みのテナントでのみ**作成できる。

> ⚠️ Microsoft Agent 365 / Frontier / BYO MCP は Preview を多く含む。コマンド・API・提供リージョンは変わり得るので、Microsoft Learn で最新を確認すること。

---

## 第3部の構成

| 章 | 内容 | 主眼 |
|----|------|------|
| **3-A：AI Teammate を作る** → [part3-1-ai-teammate.md](./part3-1-ai-teammate.md) | 独自 M365 ID（を持つエージェントを作る。頭脳は **Microsoft Foundry のクラウドモデル** | 「エージェントが"人"としてふるまう」identity モデルの体験 |
| **3-B：自作 MCP サーバー（BYO MCP）** → [part3-2-byo-mcp.md](./part3-2-byo-mcp.md) | 簡易なリモート MCP サーバーを実装・ホストし、`a365 develop-mcp` で A365 に登録・承認 | 「MCP は Gateway 経由で初めて A365 に載る」を実体験 |
| **3-C：統合** → [part3-3-integrate.md](./part3-3-integrate.md) | AI Teammate（A）から自作 MCP（B）をツールとして呼ぶ | 独自 ID エージェント × 自作ツールのエンドツーエンド |

---

## 認証モデルの整理：「自分の ID を持つか」×「どのトークンで下流を呼ぶか」

エージェントの認証は、独立した **2 つの軸**で決まる。ここを分けて考えると、AI Teammate／S2S／OBO の関係がすっきりする。

- **軸1：エージェント固有の ID（Entra Agent ID）を持つか** — blueprint から **Agent ID が発行された agentic** か、標準アプリ登録のみの **notAgentic（レガシー）** か。※Agent ID は **blueprint 経由で発行**され、標準アプリに自動付与はされない。ただし **Copilot Studio 製エージェントは Microsoft 所有 blueprint で自動的に agentic** になる。
- **軸2：処理に必要なリソースをどの権限で呼ぶか** — **OBO**（ユーザーの代理・`scp`・帰属が残る）か、**S2S**（自分の資格・`roles`・app-only 自律）か

この 2 軸で 4 象限になる（Learn の observability 認証 **4 シナリオ**と対応）。**今回の第1部 A/B/C と第3部 A がどこに入るか**も併記する。

| | **OBO**（ユーザーの代理・`scp`） | **S2S**（自分の資格・`roles`・app-only） |
|---|---|---|
| **agentic**（Entra Agent ID あり・**AI Teammate 含む**） | 自分の Agent ID を持ちつつ、リソースは**ユーザーの委任権限**で呼ぶ。<br>**使いどころ**：ユーザー操作に応答・過剰権限を避け操作の帰属をユーザーに紐づけたい。<br>**具体例**：**第1部A（Copilot Studio）**／**第3部A（AI Teammate ×OBO）** | 自分の Agent ID で **ユーザー不在でも自律的に権限を使う**（agentic identity chain）。<br>**使いどころ**：夜間・常駐・イベント駆動で、権限とガバナンスを ID 単位で効かせたいとき。**"AI Teammate らしさ"が最も出る象限**。<br>**具体例**：**第1部B（Foundry autopilot）**／**第1部C（独自 S2S）**／**第3部A（AI Teammate ×S2S）** |
| **notAgentic**（標準アプリ登録のみ・レガシー） | 標準アプリが Azure Bot OAuth 経由で**ユーザーの委任トークン**を取得。**従来型の delegated ボット**。<br>**使いどころ**：Agent ID 移行前の delegated ボット。<br>**具体例**：本ハンズオンでは不使用（比較用） | 標準アプリが client credentials で app-only トークン。**従来型のデーモン／システム自動化**（固有の agent ID 統制は無し）。<br>**使いどころ**：昔ながらの app-only バッチ。<br>**具体例**：本ハンズオンでは不使用（比較用） |

> **今回のハンズオンは 第1部A/B/C・第3部A すべて agentic（Entra Agent ID あり）＝上段**。下段の notAgentic は「Agent ID 以前の標準アプリ登録」で、[custom app registration の Agent ID 移行](https://learn.microsoft.com/entra/agent-id/migrate-custom-app-registrations-to-agent-id) が扱う対比用のレガシー像。
>
> **ただし 第1部A/B/C は agentic でも "AI Teammate ではない"**：これらは `agenticAppInstance`（"アプリ"としての ID・メールボックス無し・組織図に載らない）。**第3部A の AI Teammate だけが `agentIDuser`**（**独自の M365 ユーザーアカウント・メールボックス・Teams 在席・組織図掲載**）を持ち、**@mention・メール・会議招待の対象になる"デジタル同僚"**として扱える。これが AI Teammate の主眼。
> 出典（agentType 分類）: [Microsoft Entra Agent ID logs](https://learn.microsoft.com/entra/agent-id/sign-in-audit-logs-agents#audit-logs)

> **同じエージェントであっても、複数のパターンを両立可能である点に注意**。例：日中は OBO でユーザー依頼に応じ、夜間は S2S で自律サマリを回す

---

## 第1部C（S2S）との対比（学びのポイント）

| 観点 | 第1部C：独自エージェント | 第3部A：AI Teammate |
|---|---|---|
| 認証モデル | **S2S（サービスプリンシパル）** | **agentic-user（独自 M365 ID）** |
| `a365 setup all` フラグ | `--authmode s2s` | `--aiteammate --m365`（`--authmode` は使わない） |
| 呼び出しユーザーの権限 | 継承しない（**アプリ権限＝自分の SP** で動く） | 既定（agentic-user）は**自分のユーザー ID・権限**で動き、呼び出しユーザーの権限は引き継がない。下流の呼び方（OBO／S2S）は上の 4 象限を参照 |
| モデル | 自前 Qwen（Ollama sidecar） | Foundry クラウドモデル |

> 出典（AI Teammate は呼び出しユーザーの権限を継承しない）: [Get started with Agent 365 development](https://learn.microsoft.com/microsoft-agent-365/developer/get-started#adding-agent-365-capabilities-incrementally)

---

## 本編とのリソース分離

- **第１部 C パートで作成したをリソースを再利用**し、**別アプリ**として新規作成

```powershell
$RG        = "rg-agent365-training"                 # 既存 RG を再利用（変更しない）
$LOC       = "japaneast"
# --- 3-A：AI Teammate ---
$TMNAME    = "a365-teammate-xxxx"                    # AI Teammate の a365 --agent-name（20 文字以内）
# --- 3-B：自作 MCP ---
$MCPAPP    = "app-agent365-training-mcp-xxxx"        # 自作 MCP をホストする Web アプリ（世界で一意）
$MCPNAME   = "mcp-custom-xxxx"                       # BYO 登録時の server-name
```

---

## 前提・ライセンス

| 項目 | 要件 |
|---|---|
| AI Teammate（A） | E7/Agent 365、Teams |
| 自作 MCP（B） | Agent 365（BYO MCP は **preview**）、承認に **AI Administrator / Global Administrator**。提供地域は [Feature Geography レポート](https://aka.ms/FeatureGeographicAvailabilityReport) で要確認（App Service のホスト地域＝JapanEast 等とは別層） |
| 統合（C） | A・B の完了 |

---

← 戻る：[README（概要）](../README.MD) ｜ 次：**[3-A：AI Teammate を作る](./part3-1-ai-teammate.md)**
