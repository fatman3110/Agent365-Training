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

- **軸1：エージェントが通常社員かのように ID を持つか** — **AI Teammate（Agent 365 対応・agentic identity あり）** か、**通常アプリ（custom engine／標準アプリ登録）** か
- **軸2：処理に必要なリソースをどの権限で呼ぶか** — **OBO**（ユーザーの代理・`scp`・帰属が残る）か、**S2S**（自分の資格・`roles`・app-only 自律）か

この 2 軸で 4 象限になる（Learn の observability 認証 **4 シナリオ**と対応）。**今回の第1部 A/B/C と第3部 A がどこに入るか**も併記する。

| | **OBO**（ユーザーの代理・`scp`） | **S2S**（自分の資格・`roles`・app-only） |
|---|---|---|
| **独自 ID を持つ**（agentic・**AI Teammate 含む**） | 自分の ID を持ちつつ、下流は**ユーザーの委任権限**で呼ぶ。帰属を残しつつ**範囲はその人の権限内**に収める。<br>**使いどころ**：過剰権限を避けたい・操作の帰属をユーザーに紐づけたい自律エージェント。<br>→ **第3部A（AI Teammate ×OBO・reactive 既定寄り）** | 自分の agentic ID で **app-only トークン**（agentic identity chain）。**ユーザー不在でも自律**。<br>**使いどころ**：夜間・常駐・イベント駆動で、権限とガバナンスを ID 単位で効かせたいとき。**"らしさ"が最も出る象限**。<br>→ **第1部B（Foundry autopilot）**／**第1部C（独自 S2S）**／**第3部A（AI Teammate ×S2S）** |
| **通常アプリ**（custom engine／標準アプリ登録） | 標準アプリが Azure Bot OAuth 経由で**ユーザーの委任トークン**を取得。**従来型の delegated ボット**。<br>**使いどころ**：ユーザー操作に応答してその人の権限で動く Copilot 拡張／ボット。<br>→ **第1部A（Copilot Studio）**※ | 標準アプリが client credentials で **app-only トークン**。**従来型のデーモン／システム連携**（固有の agent ID 統制は無し）。<br>**使いどころ**：昔ながらの app-only バッチ。手軽だが ID 単位の統制はできない。<br>→ 今回の題材には無し（比較用） |

> ※ **第1部A（Copilot Studio）** は SaaS 管理のノーコード reactive エージェントで、ユーザー文脈に応答する点でこの象限が最も近い（独自コードや厳密な OBO/S2S の選択は持たない）。
>
> **agentic の中の 2 段階（上段の読み分け）**：**第1部B・C は agentic な"アプリ"ID**（blueprint・メールボックス無し）。**第3部A の AI Teammate はさらに agentic な"ユーザー"ID**（M365 UPN・メールボックス・Teams 在席・組織図掲載）を持つ**最上位形**。同じ上段でも「アプリ ID 止まり」か「ユーザー ID まで」かが決定的に違う。

> **同じエージェントが両方の flow に参加できる**。例：日中は OBO でユーザー依頼に応じ、夜間は S2S で自律サマリを回す AI Teammate。

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
