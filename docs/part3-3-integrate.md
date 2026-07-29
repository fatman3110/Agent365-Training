# 第3部 C：AI Teammate から自作 MCP を呼ぶ（統合）

[3-A](./part3-1-ai-teammate.md) の **AI Teammate** に、[3-B](./part3-2-byo-mcp.md) で登録・承認した **自作 MCP（`mcp-custom-xxxx`）** を**ツールとして持たせ**、独自 ID エージェント × 自作ツールのエンドツーエンドを体験する。

> ⚠️ **Preview の注意（要検証）**：BYO MCP の公式な呼び出し対応面は **Copilot Studio / VS Code / Claude Code / GitHub Copilot CLI**。自作 SDK エージェント（AI Teammate）へ BYO MCP を結線できるかは、**承認済み MCP が `a365 develop list-available`（統制カタログ）に現れるか**に依存する。現れない場合は Preview 制約として、下記「代替」を用いる。
> 出典: [Use an approved MCP server（対応クライアント面）](https://learn.microsoft.com/microsoft-365/admin/manage/manage-tools-for-agent#use-an-approved-mcp-server)

**目次**

- [第3部 C：AI Teammate から自作 MCP を呼ぶ（統合）](#第3部-cai-teammate-から自作-mcp-を呼ぶ統合)
  - [前提](#前提)
  - [1. 自作 MCP がカタログに載っているか確認する](#1-自作-mcp-がカタログに載っているか確認する)
  - [2. AI Teammate に自作 MCP を結線する](#2-ai-teammate-に自作-mcp-を結線する)
  - [3. 権限の同意（管理者）](#3-権限の同意管理者)
  - [4. 動作確認](#4-動作確認)
  - [代替：カタログに出ない場合](#代替カタログに出ない場合)

## 前提

- [3-A](./part3-1-ai-teammate.md) 完了（AI Teammate が instance 作成まで済み、Teams で動く）
- [3-B](./part3-2-byo-mcp.md) 完了（`mcp-custom-xxxx` が **承認・Available**、Entra 同意済み）

## 1. 自作 MCP がカタログに載っているか確認する

AI Teammate（`src/ai-teammate`）のディレクトリで、統制カタログに自作 MCP が現れるか確認する：

```powershell
a365 develop list-available
```

- 一覧に `mcp-custom-xxxx`（または宣言ツール `search_faq`）が出れば、SDK エージェントへ結線可能 → 手順 2 へ。
- 出ない場合は Preview 制約の可能性 → [代替](#代替カタログに出ない場合) へ。

## 2. AI Teammate に自作 MCP を結線する

第1部・3-A と同じ **スキル駆動**で結線する。`src/ai-teammate` を開いた状態で、**AI チャット（Agent モード）** に指示：

```text
この AI Teammate に、承認済みの自作 MCP サーバー（mcp-custom-xxxx / ツール search_faq）をツールとして追加して。
```

スキル（`add-workiq-tools`）が起動し、内部で次を行う：

1. `a365 develop list-available` でカタログ表示
2. `a365 develop add-mcp-servers` で選択した MCP を `ToolingManifest.json` に追加
3. エージェントコードに **MCP ツール登録**（フレームワークに応じた結線）を追記

> `add-workiq-tools` は Work IQ MCP と同じ枠組みで動く。自作 MCP がカタログに載っていれば同様に扱える。

## 3. 権限の同意（管理者）

MCP は Agent 365 アプリ上の **permission** として表現される。結線後、**Global Administrator** が同意を付与する：

```powershell
a365 setup permissions mcp
```

（GA でない場合は、CLI が出力する同意用スクリプトを GA に渡す。）

## 4. 動作確認

Teams で AI Teammate に **@mention** し、自作ツールを使う質問を投げる：

- 例：「（AI Teammate へ）社内 FAQ で"経費精算の締め日"を調べて」
- AI Teammate が `search_faq`（自作 MCP）を呼び、結果を返せば統合成功。
- **Defender 高度なハンティング**で、その AI Teammate による `mcp-custom-xxxx` 呼び出しが記録されることを確認（Gateway 経由の observability）。

## 代替：カタログに出ない場合

Preview 制約で自作 MCP を SDK エージェント（AI Teammate）へ結線できない場合でも、**BYO MCP 自体の価値（統制・観測）は確認できる**：

- **Copilot Studio 側**で自作 MCP を使うエージェントを作り（[3-B の 5 節](./part3-2-byo-mcp.md#5-クライアントから呼んで確認する)）、AI Teammate とは別に「承認済み BYO MCP がクライアントで動く」ことを確認する。
- 統合（AI Teammate から直接呼ぶ）は、対応面が拡大するまで「設計として理解」に留める。

> 対応クライアント面・カタログ挙動は Preview で変わり得る。最新は [Manage tools for agents](https://learn.microsoft.com/microsoft-365/admin/manage/manage-tools-for-agent) を確認する。

---

← 戻る：[3-B：自作 MCP](./part3-2-byo-mcp.md) ｜ [第3部 概要](./part3-0-overview.md) ｜ [README（概要）](../README.MD)
