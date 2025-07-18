# Discord ポイントシステムBot 要件定義書

## 1. プロジェクト概要

### 1.1 プロジェクト名
Discord ポイントシステムBot (sample11_point_system.py)

### 1.2 目的
Discordサーバー内でメンバー間のコミュニケーションを促進するシンプルなポイント付与・確認システムを構築する

### 1.3 スコープ
- リアクション👍でポイント付与（投稿者に1ポイント）
- リアクション❤️で自分のポイント確認
- シンプルなポイント管理システム

## 2. システム要件

### 2.1 対象環境
- **対象ギルドID**: `1394139562028306644`
- **Python**: 3.11+
- **Discord.py**: 2.3.2
- **データベース**: Supabase PostgreSQL
- **DB接続**: psycopg2-binary

### 2.2 権限要件
- **全ユーザー**: リアクションによるポイント付与・ポイント確認

## 3. 機能要件

### 3.1 リアクションベース機能

#### 3.1.1 ポイント付与（👍リアクション）
- **トリガー**: 任意のメッセージに👍リアクション
- **動作**: 
  - メッセージ投稿者に1ポイント付与
  - リアクションした人は付与されない（投稿者のみ）
  - 同じメッセージに複数回👍しても1回のみ有効
- **出力**: 「{投稿者}さんに1ポイント付与しました！」の確認メッセージ

#### 3.1.2 ポイント確認（❤️リアクション）
- **トリガー**: 任意のメッセージに❤️リアクション
- **動作**: 
  - リアクションした人の現在ポイントを表示
  - 初回の場合は0ポイントから開始
- **出力**: 「{ユーザー}さんの現在ポイント: {X}pt」のメッセージ

## 4. データ設計

### 4.1 PostgreSQL テーブル設計

#### ポイントテーブル（最小構成）
```sql
CREATE TABLE IF NOT EXISTS user_points (
    user_id BIGINT PRIMARY KEY,
    points INT DEFAULT 0 NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### 4.2 データ構造
```python
UserPoints {
  user_id: bigint (Discord User ID)
  points: int (現在のポイント数)
  created_at: timestamp
  updated_at: timestamp
}
```

## 5. UI/UX設計

### 5.1 リアクションフロー
```
1. 👍リアクション → ポイント付与
   "👍 {投稿者}さんに1ポイント付与しました！現在: {合計}pt"

2. ❤️リアクション → ポイント確認
   "💎 {ユーザー}さんの現在ポイント: {X}pt"
```

### 5.2 Embed デザイン
- **ポイント付与**: 👍 + 青色
- **ポイント確認**: 💎 + 金色
- **ユーザー情報**: アバター画像表示

### 5.3 エラーハンドリング
- Bot自身のメッセージは対象外
- 重複ポイント付与の防止
- データベース接続エラー時の処理

## 6. 非機能要件

### 6.1 パフォーマンス
- リアクション応答時間: 3秒以内
- データベース操作の最適化

### 6.2 セキュリティ
- 重複ポイント付与の防止
- 不正操作の防止

### 6.3 保守性
- シンプルなデータ構造
- 環境変数での設定管理
- エラーログの充実

## 7. 実装方針

### 7.1 開発フェーズ
1. **Phase 1**: 基本機能（👍ポイント付与・❤️ポイント確認）
2. **Phase 2**: エラーハンドリング・安定性向上

### 7.2 テスト方針
- リアクション機能の動作確認
- 重複付与防止の確認
- データベース連携の確認

## 8. 重複付与防止仕様

### 8.1 重複チェック方法
**選択肢1**: メッセージIDベース
- 同じメッセージに複数👍しても1回のみ有効
- シンプルだが、違うメッセージなら何度でも付与可能

**選択肢2**: 日時制限
- 同じユーザーペアに対して1日1回のみ
- より厳密だが実装が複雑

**採用方針**: 選択肢1（メッセージIDベース）でシンプルに実装

### 8.2 重複管理テーブル（オプション）
```sql
CREATE TABLE IF NOT EXISTS point_grants (
    message_id BIGINT,
    giver_user_id BIGINT,
    receiver_user_id BIGINT,
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (message_id, giver_user_id)
);
```

## 9. 環境変数設定

### 9.1 必要な環境変数
```env
# Discord Bot設定
DISCORD_TOKEN=your_bot_token

# Supabase PostgreSQL設定
SUPABASE_HOST=your-project.supabase.co
SUPABASE_DATABASE=postgres
SUPABASE_USER=postgres
SUPABASE_PASSWORD=your-password
SUPABASE_PORT=5432
```

---

## 確認・決定事項

**以下について確認してください:**

1. **重複付与防止**: メッセージIDベースで良いか？
2. **重複管理テーブル**: 必要か？不要か？
3. **ポイント表示**: 数値のみ？追加情報（ランキング等）は不要？
4. **エラーメッセージ**: どの程度詳細に表示するか？

**この要件定義書の内容で実装を開始してよろしいでしょうか？**