# Discord Bot - 簡単な挨拶ボット

メッセージに対して「こんにちは」と返すシンプルなDiscordボットです。

## セットアップ

1. 必要なライブラリをインストール:
```bash
pip install -r requirements.txt
```

2. Discord Developer Portalでボットを作成し、トークンを取得

3. `.env.template`を`.env`にコピーして、トークンを設定:
```bash
cp .env.template .env
```

4. `.env`ファイルを編集してトークンを設定:
```
DISCORD_TOKEN=your_actual_bot_token_here
```

## 実行

```bash
python bot.py
```

## 機能

- どのメッセージに対しても「こんにちは」と返答します
- ボット自身のメッセージには反応しません

## ボットの権限設定

Discord Developer Portalで以下の権限を有効にしてください：
- Send Messages
- Read Message History