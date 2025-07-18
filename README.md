# Discord Bot サンプルコード集

このリポジトリは、Python の discord.py ライブラリを使用した Discord Bot の様々な機能を学習できるサンプルコード集です。

## 📚 サンプル一覧

### 基本機能
- **`bot.py`** - メインBot（スラッシュコマンド、定期投稿、リアクション処理）
- **`sample01_get_room_contents.py`** - チャンネルのメッセージ履歴をエクスポート
- **`sample02_get_room_log.py`** - リアルタイムメッセージログ記録
- **`sample03_get_guild_members.py`** - サーバーメンバー一覧をCSVエクスポート
- **`sample04_grant_role.py`** - ロール管理Bot

### AI機能連携
- **`sample05_chatgpt.py`** - ChatGPTテキスト応答Bot
- **`sample06_chatgpt_voice.py`** - 音声メッセージのChatGPT応答Bot
- **`sample07_chatgpt_image.py`** - 画像解析ChatGPTBot
- **`sample08_meeting_log.py`** - 会議ログ生成Bot

### 実用アプリケーション
- **`sample09_memo.py`** - メッセージコピー・メモBot
- **`sample10_task.py`** - タスク管理Bot（データベース連携）
- **`sample11_point_system.py`** - ポイントシステムBot（データベース連携）

## 🚀 クイックスタート

### 1. 環境セットアップ

```bash
# リポジトリをクローン
git clone <このリポジトリのURL>
cd discord-bot-sample

# 依存関係をインストール
pip install -r requirements.txt

# 環境変数ファイルを作成
cp .env.template .env
```

### 2. Discord Bot作成

1. [Discord Developer Portal](https://discord.com/developers/applications) でアプリケーションを作成
2. Botページでトークンを取得
3. Bot権限を設定（下記参照）
4. サーバーにBotを招待

### 3. 環境変数設定

`.env` ファイルを編集：

```env
# Discord Bot設定（全サンプル共通）
DISCORD_TOKEN=your_discord_bot_token_here

# OpenAI API設定（sample05-08で使用）
OPENAI_API_KEY=your_openai_api_key_here

# Supabase PostgreSQL設定（sample10-11で使用）
SUPABASE_HOST=your-project.supabase.co
SUPABASE_DATABASE=postgres
SUPABASE_USER=postgres
SUPABASE_PASSWORD=your-supabase-password
SUPABASE_PORT=5432
```

### 4. サンプル実行

```bash
# 基本的なBot
python bot.py

# メッセージ履歴エクスポート
python sample01_get_room_contents.py

# ChatGPT連携Bot
python sample05_chatgpt.py

# タスク管理Bot（要データベース設定）
python sample10_task.py
```

## 🛠️ 詳細セットアップ

### Discord Bot 権限設定

Discord Developer Portal の Bot ページで以下を設定：

**Bot Permissions:**
- Send Messages
- Read Message History
- Use Slash Commands
- Add Reactions
- Attach Files
- Embed Links

**Privileged Gateway Intents:**
- Message Content Intent（必須）
- Server Members Intent（sample03のみ）

### データベース設定（sample10, sample11）

[Supabase](https://supabase.com/) でプロジェクトを作成後、SQL Editor で各スキーマファイルを実行：

- `sample10_task_schema.sql` - タスク管理用テーブル作成
- `sample11_point_system_schema.sql` - ポイントシステム用テーブル作成

## 📖 サンプル詳細説明

### sample01: メッセージ履歴エクスポート
- **機能**: 👍リアクションでチャンネルの過去メッセージ（最大2000件）をテキストファイルとしてエクスポート
- **学習要素**: メッセージ履歴の取得、ファイル生成、Discord添付ファイル送信

### sample02: リアルタイムログ記録
- **機能**: 特定チャンネルの全メッセージをローカルファイルに記録
- **学習要素**: ファイル追記処理、永続化、UTF-8エンコーディング

### sample03: メンバー情報エクスポート
- **機能**: 👍リアクションでサーバーメンバー一覧をCSV形式でエクスポート
- **学習要素**: Guild メンバー取得、CSV生成、特権インテント使用

### sample05-07: ChatGPT連携
- **機能**: OpenAI API を使用したテキスト/音声/画像のAI応答
- **学習要素**: 外部API連携、非同期処理、エラーハンドリング

### sample10: タスク管理システム
- **機能**: リアクションベースのタスク作成・管理（PostgreSQL連携）
- **学習要素**: データベース操作、CRUD処理、Embedメッセージ

### sample11: ポイントシステム
- **機能**: ユーザー間のポイント付与・確認システム（PostgreSQL連携）
- **学習要素**: 重複防止、トランザクション処理、メンバー情報取得

## 🎯 学習のポイント

### 1. 基本パターンの理解
すべてのサンプルは以下の共通パターンを使用：
- `discord.py` の非同期処理
- 環境変数での設定管理
- エラーハンドリングの実装

### 2. リアクションベースUI
多くのサンプルで採用している直感的なインターフェース：
- 👍: アクション実行
- ❤️: 情報表示/確認
- ✅: 完了/トグル

### 3. 日本語テキスト処理
ファイル操作時の `encoding='utf-8'` 指定が重要：
```python
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(japanese_text)
```

### 4. データベース設計
sample10, sample11 では以下を学習：
- 接続管理クラスの実装
- UPSERT パターン
- トランザクション処理

## 🔧 カスタマイズ

各サンプルは独立しているため、以下が簡単に変更可能：

- **対象サーバー/チャンネル**: 各ファイルの `TARGET_GUILD_ID`, `TARGET_CHANNEL_ID`
- **リアクション絵文字**: emoji の文字列を変更
- **データベーススキーマ**: schema.sql ファイルを編集

## 📝 注意事項

1. **環境変数**: 本番環境では `.env` ファイルをバージョン管理に含めない
2. **レート制限**: Discord API のレート制限に注意（特に大量メッセージ処理）
3. **権限**: 各サンプルに必要な Bot 権限を確実に設定
4. **データベース**: 本番環境では適切なインデックスとバックアップを設定

## 🤝 貢献

- バグ報告: Issues でお知らせください
- 機能追加: Pull Request をお送りください
- 質問: Discussions でお気軽にどうぞ

## 📄 ライセンス

このプロジェクトは学習目的のサンプルコード集です。自由にご利用ください。