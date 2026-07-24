# 第1部：環境構築（開発者）

> このパートは **開発者**（VS Code / ターミナル）の作業。完了すると、エージェントが Agent 365 に登録され、**Azure（クラウド）**で動く状態になる。
> 概要と前提条件・権限・コストは [README](../README.MD) を参照。

## 1. ツールを導入する

```powershell
node --version      # 18+
az version
a365 --version      # 無ければ: dotnet tool install -g Microsoft.Agents.A365.DevTools.Cli
func --version      # Azure Functions Core Tools（BYO MCP をクラウドにデプロイするのに使う）
```

- 4 ツールすべてがバージョンを返す
- `az login --tenant <TENANT_DOMAIN>` 済み

## 2. Agent 365 Skills を導入する

Copilot / Claude Code に自然言語で指示すると、ホスティング層・観測配線・MCP 追加を自動生成してくれる。

```powershell
# GitHub Copilot CLI（gh skill 対応版）
gh skill add microsoft/agent365-skills

# gh skill 非対応版 / VS Code agent mode の場合
git clone https://github.com/microsoft/agent365-skills.git
node <clone>/scripts/install.js   # VS Code の chat.agentSkillsLocations に登録される
```

> 導入後、VS Code は **Reload Window** で反映。7 スキル（`a365-setup` / `make-a365-agent` / `instrument-observability` / `add-workiq-tools` / `test-local` / `make-ai-teammate` / `a365-code-validator`）が使える。

## 3. Blueprint と Agent ID を作る（非 AI Teammate / OBO）

> **なぜアプリ実装（§5）より先か**：この `a365 setup all` は **エージェントの ID（Blueprint / Agent ID）に加え、アプリの骨格（ホスティング層）と `.env`（接続情報）を生成**する。§5 はこの骨格に応答ロジックを実装する段階なので、**土台となる本節を先に実行する必要がある**（アプリ実装後には回せない）。

Copilot / Claude Code に次のトリガーフレーズを投げる。

```text
a365-setup を実行して。UPN を持たない Agent を OBO（委任）認可で作りたい。
Make this a non-AI-Teammate Agent using OBO (delegated / on-behalf-of).
```

内部で `a365 setup all`（**`--aiteammate` は付けない**）が実行され、以下が冪等に走る。

```text
要件チェック ─▶ Blueprint 作成 ─▶ 資格情報 ─▶ 委任権限の継承 ─▶ Agent Identity(UPN無し) ─▶ 登録 ─▶ .env スタンプ
```

途中で **2 回の承認**がある：
1. **アプリ権限（S2S）の付与** … `Assign this application permission now? [y/N]: y`
2. **委任権限の管理者同意** … ブラウザでサインイン → ダイアログで **Allow**

確認：

```powershell
a365 query-entra                                   # Entra 登録状態
Get-Content a365.generated.config.json | ConvertFrom-Json
```

| 確認項目 | 期待値 |
|---------|--------|
| `a365.config.json` の `aiTeammate` | `false` |
| `completed` | `True`（setup 完走の証拠） |
| `agentBlueprintId` | `.env` の clientId/agentId と整合 |
| `messagingEndpoint` | 後で App Service の URL を指す |
| `resourceConsents` | Graph / Tools / Messaging / Observability が `consentGranted=True` |

> ⚠️ `.env` と `a365.generated.config.json` は**必ず `.gitignore`**。シークレット（保護済みでも）を含む。

## 4. BYO MCP サーバーを建てる（＝通信先・実行内容。ガバナンスの中心）

> **なぜアプリ実装より先か**：Agent 365 の管理では「エージェントが**どこと通信し・何を実行するか**」の把握が必須で、その実体が **MCP（ツール）**。先に MCP を用意しておくと、次のアプリ実装や第2部の観測・ガバナンス（Registry の Data & tools / Single Agent Map / 承認）が「何を監視・制御しているか」を具体物で追える。

学習用に、Azure Functions（クラウド）に MCP サーバーを**デプロイ（作成）**する。コードは [src/function_app.py](../src/function_app.py)。

```powershell
# Azure Functions（クラウド）へデプロイ
func azure functionapp publish <FUNCTION_APP_NAME>
# → 公開 URL: https://<FUNCTION_APP_NAME>.azurewebsites.net/runtime/webhooks/mcp
```

> この節では**道具を作る（デプロイする）だけ**。**Agent 365 への登録は §6、承認（管理下に置く）は [第2部 §8](./part2-handson.md)** でエージェントとまとめて行う（手順が混ざらないよう分離）。

## 5. アプリを実装する（LLM / OBO / 観測）

§4 で用意した MCP ツールを、エージェントが呼び出せるように配線する。Skills が生成した骨格に、①LLM 呼び出し ②OBO トークン交換 ③観測配線 を差し込む。**コードの実体は [src/](../src/)** にまとめてある。要点のみ：

- **LLM** は遅延初期化（起動時にブロックすると warmup プローブ失敗 → 再起動ループ）
- **OBO** は `use_s2s_endpoint=False`。受け取ったユーザートークンを `jwt-bearer` で観測スコープへ交換
- **観測** は `InvokeAgentScope`（呼び出し全体）と `ExecuteToolScope`（ツール）を計装 → 後段の Single Agent Map の描画元になる

- `.env`：`ENABLE_A365_OBSERVABILITY=true` / `ENABLE_A365_OBSERVABILITY_EXPORTER=true`
- `A365_EXPORTER_LOG_LEVEL=DEBUG` で **scp 付きトークン**の 200 送信を確認

## 6. Azure にデプロイして「登録」する

エージェント本体をクラウドにデプロイし、**エージェントと道具（MCP）をまとめて Agent 365 に登録**する（承認＝管理下配置は [第2部 §8](./part2-handson.md)）。

```powershell
az group create -n <RESOURCE_GROUP> -l <REGION>
# App Service(Linux container)+ACR にデプロイ（Ollama を sidecar）
a365 setup all                  # 実 URL を messaging endpoint に再スタンプ（冪等）
a365 publish                    # ① エージェントを登録（manifest.zip 生成）

# ② 道具（MCP）を登録
a365 develop-mcp register-external-mcp-server `
  --server-name "<MCP_NAME>" `
  --server-url  "https://<FUNCTION_APP_NAME>.azurewebsites.net/runtime/webhooks/mcp" `
  --auth-type   "NoAuth" `
  --tools       "echo,now"
# → Entra アプリ2つ自動作成: <MCP_NAME>-A365Proxy / <MCP_NAME>-PublicClients
```

登録すると、**エージェントは Agents › Requests、道具（MCP）は Tools › Requests** に `Pending` として現れる。**ここから先が第2部**（管理者による承認＝管理下配置）。

---

→ 次：**[第2部：Agent 365 ハンズオン](./part2-handson.md)** ｜ [README（概要）](../README.MD)
