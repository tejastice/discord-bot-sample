-- Discord ポイントシステムBot用 PostgreSQLテーブル作成スクリプト
-- sample11_point_system.py 用データベーススキーマ

-- ユーザーポイントテーブル（メインテーブル）
CREATE TABLE IF NOT EXISTS user_points (
    user_id BIGINT PRIMARY KEY,
    points INT DEFAULT 0 NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ポイント付与履歴テーブル（重複防止用）
CREATE TABLE IF NOT EXISTS point_grants (
    message_id BIGINT,
    giver_user_id BIGINT,
    receiver_user_id BIGINT,
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (message_id, giver_user_id)
);

-- インデックス作成（パフォーマンス向上のため）
CREATE INDEX IF NOT EXISTS idx_user_points_points ON user_points(points DESC);
CREATE INDEX IF NOT EXISTS idx_point_grants_receiver ON point_grants(receiver_user_id);
CREATE INDEX IF NOT EXISTS idx_point_grants_granted_at ON point_grants(granted_at);

-- 初期データ確認用ビュー（オプション）
CREATE OR REPLACE VIEW point_ranking AS
SELECT 
    user_id,
    points,
    created_at,
    updated_at
FROM user_points 
WHERE points > 0 
ORDER BY points DESC, updated_at ASC;

-- テーブル作成完了メッセージ
DO $$
BEGIN
    RAISE NOTICE 'Discord ポイントシステムBot用テーブルが正常に作成されました';
    RAISE NOTICE 'テーブル: user_points, point_grants';
    RAISE NOTICE 'ビュー: point_ranking';
END $$;