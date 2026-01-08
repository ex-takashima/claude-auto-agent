# claude-auto-agent 設計書

## 1. プロジェクト概要

### 1.1 コンセプト

GitHub Actions + Claude Code Action を使った汎用的な定時実行・自動通知エージェント。

ユーザーが設定したテーマ・URLを定期的にクロールし、要約してDiscord/LINEに通知する。

### 1.2 ターゲット

- 「サブスク貧乏になりたくない」層
- Manus等の有料AIエージェントの代替を求める人
- 自分好みにカスタマイズしたい技術者

### 1.3 特徴

| 項目 | 内容 |
|------|------|
| 実行環境 | GitHub-Hosted Runner（無料枠内） |
| コスト | GitHub無料枠 + Claude API従量課金のみ |
| 対話方式 | GitHub Issues 経由 |
| 通知先 | Discord / LINE |
| カスタマイズ | JSON設定ファイルで自由に |

---

## 2. リポジトリ構成

```
claude-auto-agent/
├── .github/
│   └── workflows/
│       ├── scheduled-task.yml      # 定時実行（cron）
│       └── issue-command.yml       # Issue経由のコマンド処理
├── config/
│   └── sources.json                # ソース設定ファイル
├── data/
│   ├── reports/                    # リサーチ結果（Markdown）
│   │   ├── 2026-01-08.md
│   │   ├── 2026-01-09.md
│   │   └── ...
│   └── latest.json                 # 差分検出用（通知済みURL一覧）
├── scripts/
│   ├── notify-discord.sh           # Discord通知スクリプト
│   └── notify-line.sh              # LINE通知スクリプト
├── CLAUDE.md                       # Claude Code Action用の指示
├── DESIGN.md                       # 設計書（本ファイル）
├── README.md                       # 使い方・セットアップ手順
└── LICENSE
```

---

## 3. 設定ファイル構造

### 3.1 sources.json

ソースに複数カテゴリをタグ付けする方式を採用。
Discord/LINEからの操作（将来拡張）を見据え、フラットな構造で管理しやすくする。

```json
{
  "sources": [
    {
      "id": "anthropic",
      "name": "Anthropic公式",
      "url": "https://www.anthropic.com/news",
      "categories": ["ai-news", "llm"],
      "enabled": true
    },
    {
      "id": "openai",
      "name": "OpenAI公式",
      "url": "https://openai.com/news/",
      "categories": ["ai-news", "llm"],
      "enabled": true
    },
    {
      "id": "deepmind",
      "name": "Google DeepMind",
      "url": "https://deepmind.google/blog/",
      "categories": ["ai-news", "llm"],
      "enabled": true
    },
    {
      "id": "github-blog",
      "name": "GitHub Blog",
      "url": "https://github.blog/",
      "categories": ["tech-blog"],
      "enabled": true
    }
  ],
  "categories": {
    "ai-news": {
      "name": "AI最新ニュース",
      "description": "AI企業の公式発表・ニュース",
      "enabled": true
    },
    "llm": {
      "name": "LLM関連",
      "description": "大規模言語モデル関連の情報",
      "enabled": true
    },
    "tech-blog": {
      "name": "技術ブログ",
      "description": "技術系企業の公式ブログ",
      "enabled": true
    }
  },
  "settings": {
    "language": "ja",
    "max_items_per_source": 5,
    "summary_length": "medium"
  }
}
```

### 3.2 設定項目の説明

#### sources（配列）

| フィールド | 型 | 説明 |
|-----------|-----|------|
| id | string | 一意の識別子（操作時に使用） |
| name | string | 表示名 |
| url | string | クロール対象URL |
| categories | string[] | 所属カテゴリのID配列 |
| enabled | boolean | 有効/無効フラグ |

#### categories（オブジェクト）

| フィールド | 型 | 説明 |
|-----------|-----|------|
| name | string | カテゴリ表示名 |
| description | string | カテゴリの説明 |
| enabled | boolean | カテゴリ全体の有効/無効 |

#### settings

| フィールド | 型 | 説明 |
|-----------|-----|------|
| language | string | 出力言語（ja / en） |
| max_items_per_source | number | 各ソースから取得する最大件数 |
| summary_length | string | 要約の長さ（short / medium / long） |

---

## 4. データ保存設計

### 4.1 保存方針

- **形式:** Markdown（GitHub上で直接閲覧可能）
- **保存期間:** ユーザーが削除するまで永続保存
- **差分検出:** latest.json で通知済みURLを管理し、重複通知を防止

### 4.2 レポートファイル（data/reports/YYYY-MM-DD.md）

```markdown
---
date: 2026-01-08
categories:
  - ai-news
sources_checked:
  - https://www.anthropic.com/news
  - https://openai.com/news/
urls_found:
  - https://www.anthropic.com/news/claude-4-5-update
  - https://openai.com/news/gpt-5-2-release
---

# 📰 リサーチレポート (2026-01-08)

## AI最新ニュース

### Anthropic公式

- **Claude 4.5の新機能発表**
  エージェント機能が強化され、長時間の自律動作が可能に...
  
  🔗 https://www.anthropic.com/news/claude-4-5-update

### OpenAI公式

- **GPT-5.2リリース**
  新しい推論モードが追加...
  
  🔗 https://openai.com/news/gpt-5-2-release

---

⏰ 生成時刻: 07:00 JST
```

### 4.3 差分検出用ファイル（data/latest.json）

```json
{
  "last_updated": "2026-01-08T07:00:00+09:00",
  "notified_urls": [
    "https://www.anthropic.com/news/claude-4-5-update",
    "https://openai.com/news/gpt-5-2-release",
    "https://deepmind.google/blog/gemini-3-announcement"
  ]
}
```

### 4.4 差分検出フロー

```
1. data/latest.json を読み込み（通知済みURL一覧）
2. config/sources.json の有効なソースをクロール
3. 新しいURLを抽出（latest.json にないもの）
4. 新着があれば:
   ├─→ 要約を生成
   ├─→ Discord/LINEに通知
   ├─→ data/reports/YYYY-MM-DD.md に保存
   └─→ data/latest.json を更新
5. 新着がなければ:
   └─→ 通知せず終了（ログのみ）
```

---

## 5. GitHub Issues 対話フロー

### 5.1 フロー図

```
[ユーザー]
    │
    ▼ Issue作成（ラベル: command）
┌─────────────────────────────────────┐
│ タイトル: add source                │
│ 本文:                               │
│   url: https://ledge.ai/            │
│   name: Ledge.ai                    │
│   categories: ai-news               │
└─────────────────────────────────────┘
    │
    ▼ GitHub Actions トリガー
    │   (on: issues - labeled)
    │
    ▼ Claude Code Action 実行
    │
    ├─→ Issue内容を解析
    ├─→ sources.json を編集
    ├─→ 変更をコミット & プッシュ
    └─→ Issueにコメント返信 & クローズ
```

### 5.2 対応コマンド一覧

| コマンド（Issueタイトル） | 本文パラメータ | 動作 |
|--------------------------|---------------|------|
| `add source` | url, name, categories | ソース追加 |
| `remove source` | id | ソース削除 |
| `list sources` | (なし) | ソース一覧をコメントで返信 |
| `enable source` | id | ソースを有効化 |
| `disable source` | id | ソースを無効化 |
| `add category` | id, name, description | カテゴリ追加 |
| `remove category` | id | カテゴリ削除 |
| `run now` | category (任意) | 即時実行 |

### 5.3 Issue本文フォーマット例

#### ソース追加

```
url: https://ledge.ai/
name: Ledge.ai
categories: ai-news, tech-blog
```

#### ソース削除

```
id: anthropic
```

#### 即時実行

```
category: ai-news
```

---

## 6. ワークフロー設計

### 6.1 scheduled-task.yml（定時実行）

```yaml
name: Scheduled Task

on:
  schedule:
    - cron: '0 22 * * *'  # UTC 22:00 = JST 07:00
  workflow_dispatch:       # 手動実行用

jobs:
  collect-and-notify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Claude Code Action
        uses: anthropics/claude-code-action@beta
        with:
          claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
          prompt: |
            config/sources.json を読み込み、有効なソースをクロールして要約し、
            Discord/LINEに通知してください。
            結果は data/reports/YYYY-MM-DD.md に保存してください。
            
      - name: Commit changes (if any)
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add -A
          git diff --staged --quiet || git commit -m "Update crawled data"
          git push
```

### 6.2 issue-command.yml（Issue経由コマンド）

```yaml
name: Issue Command

on:
  issues:
    types: [labeled]

jobs:
  process-command:
    if: github.event.label.name == 'command'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Claude Code Action
        uses: anthropics/claude-code-action@beta
        with:
          claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
          prompt: |
            Issue #${{ github.event.issue.number }} の内容を解析し、
            コマンドに応じて config/sources.json を更新してください。
            完了後、Issueにコメントで結果を報告してください。
            
      - name: Commit changes
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add -A
          git diff --staged --quiet || git commit -m "Update config via Issue #${{ github.event.issue.number }}"
          git push
```

---

## 7. 通知設計

### 7.1 Discord通知

Webhookを使用（Bot不要、設定簡単）

**必要なSecret:**

- `DISCORD_WEBHOOK_URL`

**通知フォーマット例:**

```
📰 AI最新ニュース (2026-01-08)
━━━━━━━━━━━━━━━━━━━━

🔹 Anthropic公式
• Claude 4.5の新機能発表
• エージェント機能の強化

🔹 OpenAI公式  
• GPT-5.2の詳細発表
• 新しいAPI機能

━━━━━━━━━━━━━━━━━━━━
📄 レポート: https://github.com/xxx/claude-auto-agent/blob/main/data/reports/2026-01-08.md
⏰ 次回更新: 明日 07:00
```

### 7.2 LINE通知

LINE Messaging API を使用

**必要なSecret:**

- `LINE_CHANNEL_ACCESS_TOKEN`
- `LINE_USER_ID`（通知先のユーザーID）

**注意:**

- LINE Notify は2025年3月末で終了済み
- Messaging API の無料枠: 月200メッセージ

---

## 8. GitHub Secrets

すべての機密情報は GitHub Secrets で管理する（.envファイルは使用しない）。

**設定場所:** リポジトリ → Settings → Secrets and variables → Actions → New repository secret

### 必須

| Secret名 | 用途 | 取得方法 |
|----------|------|----------|
| `CLAUDE_CODE_OAUTH_TOKEN` | Claude Code Action認証 | Claude Code CLIでOAuth認証 |

### 任意（通知機能を使う場合）

| Secret名 | 用途 | 取得方法 |
|----------|------|----------|
| `DISCORD_WEBHOOK_URL` | Discord通知 | Discordチャンネル設定 → 連携サービス → ウェブフック |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE通知 | LINE Developers → Messaging API設定 |
| `LINE_USER_ID` | LINE通知先 | LINE Developers → あなたのユーザーID |

---

## 9. 今後の拡張予定（オプション）

以下は将来の記事ネタとして保留:

| 機能 | 概要 | 必要なもの |
|------|------|-----------|
| Discord Bot対話 | チャットから直接コマンド | VPS + Bot常駐 |
| LINE Bot対話 | LINEから直接コマンド | VPS + Webhook受信 |
| Web UI | ブラウザから設定管理 | ホスティング |
| RSS対応 | RSSフィードの自動検出 | - |

---

## 10. 参考リンク

- [Claude Code Action](https://github.com/anthropics/claude-code-action)
- [GitHub Actions - スケジュール実行](https://docs.github.com/ja/actions/using-workflows/events-that-trigger-workflows#schedule)
- [Discord Webhook](https://discord.com/developers/docs/resources/webhook)
- [LINE Messaging API](https://developers.line.biz/ja/docs/messaging-api/)

---

## 更新履歴

| 日付 | 内容 |
|------|------|
| 2026-01-08 | 初版作成 |
| 2026-01-08 | 認証方式を CLAUDE_CODE_OAUTH_TOKEN に変更、.env.example を削除 |
| 2026-01-08 | データ保存設計を追加（Markdown形式、差分検出） |
