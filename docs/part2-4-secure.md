# 第2部：Secure（保護）｜AI 管理者

Agent 365 の 3 本柱の 3 つ目。Learn の Secure は、**Purview（情報保護 / DLP）・Defender（脅威防御）** でエージェントの機密データと脅威をエンドツーエンドに守る（リスクベースのアクセス制御＝条件付きアクセスは [Govern](./part2-3-govern.md) でテンプレートと併せて扱う）。

> ⚠️ Microsoft Agent 365 / Copilot Studio は Preview を多く含む。UI 名やメニュー位置は変わり得るので、詰まったら Microsoft Learn で最新を確認すること。

| 保護面 | 役割 | 本節 |
|--------|------|------|
| **Microsoft Purview** | 情報保護・DLP・リスクセーフガードで機密データ露出を防ぐ | [2 節](#2-purview--機密データの保護情報保護--dlp) |
| **Microsoft Defender** | エージェント活動の脅威検出・調査・対応（Advanced Hunting） | [3 節](#3-defender--脅威検出と調査advanced-hunting) |

> リスクベースのアクセス制御（Entra 条件付きアクセス・Agent risk）は、テンプレートと併せて [Govern の 6 節](./part2-3-govern.md#6-条件付きアクセス--agent-risk--high-を-blockreport-only--on) で扱う。

**目次**

- [第2部：Secure（保護）｜AI 管理者](#第2部secure保護ai-管理者)
  - [1. 全体像](#1-全体像)
  - [2. Purview — 機密データの保護（情報保護 / DLP）](#2-purview--機密データの保護情報保護--dlp)
  - [3. Defender — 脅威検出と調査（Advanced Hunting）](#3-defender--脅威検出と調査advanced-hunting)

## 1. 全体像

[Observe](./part2-2-observe.md) が「見る」、[Govern](./part2-3-govern.md) が「ライフサイクルを止める／消す」なら、Secure は「**リスクに応じて自動で守る**」。

## 2. Purview — 機密データの保護（情報保護 / DLP）

[Observe の ラボ](./part2-2-observe.md) で Purview を**観察**（Prompt/Response を読む）に使ったが、Secure では**保護**に使う。エージェントが機密データを扱う／外部へ出す動きを、情報保護ラベル・DLP・リスクセーフガードで抑止する。

- [Purview](https://purview.microsoft.com/) › **DSPM** で、エージェントの AI アクティビティに含まれる機密情報の種類・件数を把握
- DLP ポリシーで、機密ラベル付きデータのプロンプト送信やツール経由の持ち出しを制限

## 3. Defender — 脅威検出と調査（Advanced Hunting）

Defender はエージェント活動を**脅威防御**の観点で監視する。




---

← 戻る：**[第2部：Govern（管理）](./part2-3-govern.md)** ｜ [README（概要）](../README.MD)
