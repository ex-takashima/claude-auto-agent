# CLAUDE.md - Claude Code Action 指示書

このファイルは Claude Code Action への指示を記述しています。

## プロジェクト概要

定期的にWebサイトをクロールし、新着情報を要約してDiscord/LINEに通知する自動エージェントです。

## ファイル構成

```
config/sources.json     # ソース設定（クロール対象URL、カテゴリ）
data/latest.json        # 差分検出用（通知済みURL一覧）
data/reports/           # リサーチ結果（Markdown形式）
scripts/notify-*.sh     # 通知スクリプト
```

---

## タスク1: 定時リサーチ実行

### トリガー

- scheduled-task.yml から呼び出し
- `workflow_dispatch` での手動実行

### 処理手順

1. **設定読み込み**
   - `config/sources.json` を読み込む
   - `enabled: true` のソースのみ対象
   - カテゴリも `enabled: true` のもののみ

2. **差分検出**
   - `data/latest.json` を読み込む（なければ空として扱う）
   - `notified_urls` に含まれるURLは既に通知済み

3. **クロール実行**
   - 各ソースURLにアクセス
   - 記事一覧ページから最新記事のURLとタイトルを取得
   - `settings.max_items_per_source` 件まで取得

4. **新着判定**
   - `data/latest.json` の `notified_urls` にないURLが新着
   - 新着がなければ通知せず終了

5. **要約生成**
   - 新着記事の内容を取得
   - `settings.language` の言語で要約
   - `settings.summary_length` に応じた長さで要約
     - short: 1-2文
     - medium: 3-5文
     - long: 1段落

6. **レポート保存**
   - `data/reports/YYYY-MM-DD.md` に保存
   - 同日に複数回実行した場合は追記または上書き
   - フロントマター（YAML）に日付、カテゴリ、URL一覧を記録

7. **通知送信**
   - Discord: curlコマンドで直接Webhook URLにPOSTする（環境変数`$DISCORD_WEBHOOK_URL`を使用）
   - LINE: curlコマンドでLINE Messaging APIにPOSTする
   - 通知メッセージにはレポートへのGitHub URLを含める
   - 環境変数が設定されていない場合（空文字列の場合）はスキップ

8. **差分データ更新**
   - `data/latest.json` の `notified_urls` に新着URLを追加
   - `last_updated` を現在時刻に更新

### レポートのフォーマット

```markdown
---
date: YYYY-MM-DD
categories:
  - カテゴリID
sources_checked:
  - チェックしたURL
urls_found:
  - 発見した記事URL
---

# 📰 リサーチレポート (YYYY-MM-DD)

## カテゴリ名

### ソース名

- **記事タイトル**
  要約文...
  
  🔗 記事URL

---

⏰ 生成時刻: HH:MM JST
```

### Discord通知フォーマット

```
📰 カテゴリ名 (YYYY-MM-DD)
━━━━━━━━━━━━━━━━━━━━

🔹 ソース名
• 記事タイトル1
• 記事タイトル2

🔹 別のソース名
• 記事タイトル

━━━━━━━━━━━━━━━━━━━━
📄 レポート: [GitHubリンク]
```

**送信方法:**
```bash
curl -H "Content-Type: application/json" \
  -d '{"content":"メッセージ内容"}' \
  "$DISCORD_WEBHOOK_URL"
```

### LINE通知フォーマット

```
📰 カテゴリ名 (YYYY-MM-DD)

🔹 ソース名
• 記事タイトル1
• 記事タイトル2

📄 レポート: [GitHubリンク]
```

**送信方法:**
```bash
curl -X POST https://api.line.me/v2/bot/message/push \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $LINE_CHANNEL_ACCESS_TOKEN" \
  -d "{\"to\":\"$LINE_USER_ID\",\"messages\":[{\"type\":\"text\",\"text\":\"メッセージ内容\"}]}"
```

---

## タスク2: 通知メッセージ生成・送信

### トリガー

- scheduled-task.yml の notify ジョブから呼び出し
- レポートファイルが存在する場合のみ実行

### 処理手順

1. **レポート読み込み**
   - `data/reports/YYYY-MM-DD.md` を読み込む
   - 記事タイトルと要約を抽出

2. **通知メッセージ生成**
   - 記事タイトルを日本語に翻訳（英語の場合）
   - 各通知先に最適化したフォーマットで整形
   - 文字数制限を考慮（Discord: 2000文字、LINE: 5000文字）

3. **Discord通知送信**
   - 環境変数 `$DISCORD_WEBHOOK_URL` が設定されている場合のみ
   - curlコマンドでWebhook URLにPOST
   - JSONは適切にエスケープすること

4. **LINE通知送信**
   - 環境変数 `$LINE_CHANNEL_ACCESS_TOKEN` と `$LINE_USER_ID` が設定されている場合のみ
   - curlコマンドでLINE Messaging APIにPOST
   - JSONは適切にエスケープすること

### Discord通知フォーマット

```
📰 AI最新ニュース (YYYY-MM-DD)
━━━━━━━━━━━━━━━━━━━━

🔹 ソース名
• 記事タイトル（日本語）

🔹 別のソース名
• 記事タイトル（日本語）

━━━━━━━━━━━━━━━━━━━━
📄 詳細: [GitHubリンク]
```

**送信コマンド:**
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"content":"メッセージ内容"}' \
  "$DISCORD_WEBHOOK_URL"
```

### LINE通知フォーマット

LINEはシンプルで読みやすい形式にする。装飾は最小限に。

```
📰 AI最新ニュース
2026-01-08

■ Anthropic
・記事タイトル（日本語）

■ Google DeepMind
・記事タイトル（日本語）

詳細: https://github.com/...
```

**送信コマンド:**
```bash
curl -X POST https://api.line.me/v2/bot/message/push \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $LINE_CHANNEL_ACCESS_TOKEN" \
  -d '{"to":"$LINE_USER_ID","messages":[{"type":"text","text":"メッセージ内容"}]}'
```

### 重要な注意事項

- **改行**: シェルスクリプトではなくcurlで直接送信するため、JSONの改行は `\n` ではなく実際の改行文字を使用
- **JSONエスケープ**: ダブルクォート、バックスラッシュ、改行などは適切にエスケープ
- **文字化け防止**: UTF-8でエンコード

---

## タスク3: Issueコマンド処理

### トリガー

- issue-command.yml から呼び出し
- ラベル `command` が付与されたIssue

### Issueの解析

- **タイトル**: コマンド名
- **本文**: パラメータ（`key: value` 形式）

### 対応コマンド

#### `add source` - ソース追加

**パラメータ:**
- `url` (必須): クロール対象URL
- `name` (必須): 表示名
- `categories` (必須): カテゴリID（カンマ区切りで複数可）

**処理:**
1. `config/sources.json` を読み込む
2. URLから一意のIDを生成（ドメイン名ベース）
3. 重複チェック（同じURLが既にあればエラー）
4. `sources` 配列に追加
5. ファイルを保存
6. Issueにコメントで結果報告
7. Issueをクローズ

**成功時コメント:**
```
✅ ソースを追加しました

- **ID:** generated-id
- **名前:** ソース名
- **URL:** https://example.com
- **カテゴリ:** ai-news, tech-blog
```

#### `remove source` - ソース削除

**パラメータ:**
- `id` (必須): 削除するソースのID

**処理:**
1. `config/sources.json` を読み込む
2. 指定IDのソースを検索
3. 見つからなければエラー
4. `sources` 配列から削除
5. ファイルを保存
6. Issueにコメントで結果報告
7. Issueをクローズ

#### `list sources` - ソース一覧

**パラメータ:** なし

**処理:**
1. `config/sources.json` を読み込む
2. ソース一覧をMarkdown形式で整形
3. Issueにコメントで一覧を投稿
4. Issueをクローズ

**コメント形式:**
```
📋 登録済みソース一覧

| ID | 名前 | URL | カテゴリ | 状態 |
|----|------|-----|---------|------|
| anthropic | Anthropic公式 | https://... | ai-news, llm | ✅ 有効 |
| openai | OpenAI公式 | https://... | ai-news | ❌ 無効 |
```

#### `enable source` / `disable source` - 有効/無効切り替え

**パラメータ:**
- `id` (必須): ソースのID

**処理:**
1. `config/sources.json` を読み込む
2. 指定IDのソースを検索
3. `enabled` を `true` / `false` に変更
4. ファイルを保存
5. Issueにコメントで結果報告
6. Issueをクローズ

#### `add category` - カテゴリ追加

**パラメータ:**
- `id` (必須): カテゴリID（英数字、ハイフン）
- `name` (必須): 表示名
- `description` (任意): 説明

**処理:**
1. `config/sources.json` を読み込む
2. 重複チェック
3. `categories` オブジェクトに追加（`enabled: true`）
4. ファイルを保存
5. Issueにコメントで結果報告
6. Issueをクローズ

#### `remove category` - カテゴリ削除

**パラメータ:**
- `id` (必須): カテゴリID

**処理:**
1. `config/sources.json` を読み込む
2. 指定IDのカテゴリを検索
3. そのカテゴリを使用しているソースがあれば警告
4. `categories` から削除
5. ファイルを保存
6. Issueにコメントで結果報告
7. Issueをクローズ

#### `run now` - 即時実行

**パラメータ:**
- `category` (任意): 特定カテゴリのみ実行

**処理:**
1. タスク1（定時リサーチ実行）と同じ処理を実行
2. `category` 指定があればそのカテゴリのみ
3. Issueにコメントで結果報告
4. Issueをクローズ

### エラー処理

- パラメータ不足: 必要なパラメータを案内
- ID重複: 既存のIDを表示
- ID不明: 利用可能なIDを一覧表示
- その他エラー: エラー内容を報告

**エラー時コメント:**
```
❌ エラーが発生しました

**原因:** 指定されたID `xxx` が見つかりません

**利用可能なID:**
- anthropic
- openai
- deepmind
```

---

## 環境変数

以下の環境変数を使用します（GitHub Secretsから取得）:

| 変数名 | 用途 | 必須 |
|--------|------|------|
| `DISCORD_WEBHOOK_URL` | Discord通知 | 任意 |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE通知 | 任意 |
| `LINE_USER_ID` | LINE通知先 | 任意 |

---

## 注意事項

1. **JSONファイルの整形**: 保存時は2スペースインデントで整形する
2. **日本時間**: 日付・時刻は JST (UTC+9) で表示。GitHub Actionsでは以下のコマンドで取得すること:
   ```bash
   TZ=Asia/Tokyo date '+%Y-%m-%d %H:%M JST'
   ```
   または `date -u` でUTCを取得し、+9時間して計算する
3. **コミット**: 変更があればコミットする（コミットメッセージは処理内容を簡潔に）
4. **レート制限**: クロール時は各サイトに負荷をかけないよう適度な間隔を空ける
5. **エラーハンドリング**: サイトにアクセスできない場合はスキップし、他のソースの処理を継続
