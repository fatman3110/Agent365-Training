# 第2部：Secure（保護）｜AI 管理者

Agent 365 の 3 本柱の 3 つ目。**Purview（情報保護 / DLP）・Defender（脅威防御）** でエージェントの機密データと脅威をエンドツーエンドに守る（）。

> ⚠️ Microsoft Agent 365 / Copilot Studio は Preview を多く含む。UI 名やメニュー位置は変わり得るので、詰まったら Microsoft Learn で最新を確認すること。

| 保護面 | 役割 | 本節 |
|--------|------|------|
| **Microsoft Purview** | 情報保護・DLP・リスクセーフガードで機密データ露出を防ぐ | [2 節](#2-purview--機密データの保護情報保護--dlp) |
| **Microsoft Defender ／ レジストリ** | AI アラートの確認（Defender ポータル）＋リスクのあるエージェントの把握（M365 管理センター レジストリ） | [3 節](#3-脅威とリスクを確認する) |

> リスクベースのアクセス制御（Entra 条件付きアクセス・Agent risk）は、テンプレートと併せて [Govern の 5-1 節](./part2-3-govern.md#5-1-entra-で-3-種のポリシーを作成) で扱う。

**目次**

- [第2部：Secure（保護）｜AI 管理者](#第2部secure保護ai-管理者)
  - [1. 全体像](#1-全体像)
  - [2. Purview — 機密データの保護（情報保護 / DLP）](#2-purview--機密データの保護情報保護--dlp)
  - [3. 脅威とリスクを確認する](#3-脅威とリスクを確認する)
    - [3-1. リスクのあるエージェントを把握する（M365 管理センター レジストリ）](#3-1-リスクのあるエージェントを把握するm365-管理センター-レジストリ)
    - [3-2. AI に関するアラートを確認する（Defender ポータル）](#3-2-ai-に関するアラートを確認するdefender-ポータル)

## 1. 全体像

[Observe](./part2-2-observe.md) が「見る」、[Govern](./part2-3-govern.md) が「ライフサイクルを止める／消す」なら、Secure は「**リスクに応じて自動で守る**」。

## 2. Purview — 機密データの保護（情報保護 / DLP）

[Observe の ラボ](./part2-2-observe.md) で Purview を**観察**（Prompt/Response を読む）に使ったが、Secure では**保護**に使う。エージェントが機密データを扱う／外部へ出す動きを、情報保護ラベル・DLP・リスクセーフガードで抑止する。

- [Microsoft Purview ポータル](https://purview.microsoft.com/) › **DSPM** で、エージェントの AI アクティビティに含まれる機密情報の種類・件数を把握
- DLP ポリシーで、機密ラベル付きデータのプロンプト送信やツール経由の持ち出しを制限

## 3. 脅威とリスクを確認する

### 3-1. リスクのあるエージェントを把握する（M365 管理センター レジストリ）

- [Microsoft 365 管理センター](https://admin.microsoft.com/) › **エージェント › 概要** の **Agents at risk（リスクのあるエージェント）** (または、すべてのエージェントのリスク列)で、セキュリティプラットフォームが検出した高リスクなエージェントを確認できる
- 対象エージェントの **Security** タブから [Microsoft Defender ポータル](https://security.microsoft.com/)（もしくは [Microsoft Purview ポータル](https://purview.microsoft.com/)）を開き、リスクの詳細と推奨対応を確認できる

### 3-2. AI に関するアラートを確認する（Defender ポータル）

Defender は Agent 365 管理下のエージェント活動を常時監視し、**jailbreak／プロンプトインジェクション（XPIA）／資格情報の漏えい／回避手法／不審なユーザーアクセス** などの疑わしい振る舞いを、**Defender ポータルの準リアルタイムのアラート**として上げる。アラートはインシデントに相関され、**インシデントとアラート** メニューから調査できる。

- [Defender ポータル](https://security.microsoft.com/) でエージェント関連のアラート／インシデントを確認

---

← 戻る：**[第2部：Govern（管理）](./part2-3-govern.md)** ｜ [README（概要）](../README.MD)
