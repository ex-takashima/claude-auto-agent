# Claude Auto Agent

GitHub Actions + Claude Code Action を使った自動リサーチ・通知エージェント

定期的にWebサイトをクロールし、新着情報を要約してDiscord/LINEに通知します。

## 特徴

- **追加費用なし**: Claude Pro/Max Planのサブスク範囲内 + GitHub Actions無料枠で運用可能
- **自動実行**: 毎日定時に自動でリサーチ
- **差分検出**: 新着記事のみを通知（重複なし）
- **Issue経由操作**: GitHubのIssueからソース追加・削除が可能
- **マルチ通知**: Discord / LINE に対応

## セットアップ

### 1. リポジトリをフォーク

このリポジトリをフォークしてください。

### 2. GitHub Secretsを設定

リポジトリの Settings → Secrets and variables → Actions → New repository secret で以下を設定:

| Secret名 | 用途 | 必須 |
|----------|------|------|
| `CLAUDE_CODE_OAUTH_TOKEN` | Claude Code Action認証 | 必須 |
| `DISCORD_WEBHOOK_URL` | Discord通知 | 任意 |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE通知 | 任意 |
| `LINE_USER_ID` | LINE通知先 | 任意 |

#### CLAUDE_CODE_OAUTH_TOKEN の取得方法

1. [Claude Code CLI](https://github.com/anthropics/claude-code) をインストール
2. `claude` コマンドでOAuth認証を実行
3. 認証後に表示されるトークンをSecretに設定

#### Discord Webhook URLの取得方法

1. Discordサーバーで通知したいチャンネルを開く
2. チャンネル設定 → 連携サービス → ウェブフック
3. 新しいウェブフックを作成し、URLをコピー

#### LINE認証情報の取得方法

1. [LINE Developers](https://developers.line.biz/) にログイン
2. プロバイダーを作成し、Messaging APIチャネルを作成
3. チャネルアクセストークンを発行
4. 基本設定からあなたのユーザーIDをコピー

### 3. ソースをカスタマイズ

`config/sources.json` を編集して、クロール対象のサイトを追加・変更できます。

## 使い方

### 定時実行

毎日 JST 07:00 に自動実行されます。手動で実行する場合は:

Actions → Scheduled Task → Run workflow

### Issue経由でソース管理

#### ソース追加

1. 新しいIssueを作成
2. タイトル: `add source`
3. 本文:
   ```
   url: https://example.com/blog
   name: Example Blog
   categories: tech-blog
   ```
4. ラベル `command` を追加

#### ソース削除

- タイトル: `remove source`
- 本文: `id: example-blog`

#### ソース一覧表示

- タイトル: `list sources`
- 本文: (空)

#### 有効/無効切り替え

- タイトル: `enable source` または `disable source`
- 本文: `id: anthropic`

#### カテゴリ追加

- タイトル: `add category`
- 本文:
  ```
  id: new-category
  name: 新しいカテゴリ
  description: カテゴリの説明
  ```

#### 即時実行

- タイトル: `run now`
- 本文: `category: ai-news` (任意、指定しなければ全カテゴリ)

## ファイル構成

```
claude-auto-agent/
├── .github/workflows/
│   ├── scheduled-task.yml    # 定時実行
│   └── issue-command.yml     # Issueコマンド処理
├── config/
│   └── sources.json          # ソース設定
├── data/
│   ├── reports/              # リサーチレポート
│   └── latest.json           # 差分検出用
├── scripts/
│   ├── notify-discord.sh     # Discord通知
│   └── notify-line.sh        # LINE通知
├── CLAUDE.md                 # Claude Code Action指示書
└── README.md
```

## 設定ファイル

### sources.json

```json
{
  "sources": [
    {
      "id": "anthropic",
      "name": "Anthropic公式",
      "url": "https://www.anthropic.com/news",
      "categories": ["ai-news"],
      "enabled": true
    }
  ],
  "categories": {
    "ai-news": {
      "name": "AI最新ニュース",
      "description": "AI企業の公式発表",
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

### 設定項目

| 項目 | 説明 |
|------|------|
| `language` | 出力言語 (ja/en) |
| `max_items_per_source` | 各ソースから取得する最大件数 |
| `summary_length` | 要約の長さ (short/medium/long) |

## 利用要件

- **Claude Pro または Max Plan**: サブスクリプション契約が必要（OAuth認証で利用）
- **GitHub Actions**: 無料枠内で運用可能（月2,000分）
- **追加のAPI費用**: なし（サブスクリプションの範囲内）

## セキュリティ注意事項

### Publicリポジトリで運用する場合

- **GitHub Secrets**: UIやログからは見えないため、漏洩リスクは低い
- **Issue Commandワークフロー**: ラベル付与はオーナー・コラボレーターのみ可能なため、第三者が勝手にトリガーすることはできない

### 推奨事項

- フォーク後は**Privateリポジトリ**での運用を推奨
- コラボレーターの追加は**信頼できる人のみ**に限定
- Issueコマンド機能が不要な場合は `issue-command.yml` を削除しても可

### 対応サイトについて

- 認証不要のニュースサイト・ブログが対象
- X（旧Twitter）等の認証必須サイトには非対応

## ライセンス

MIT License
