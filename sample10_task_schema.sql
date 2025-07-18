-- Discord タスク管理Bot用データベーススキーマ (Supabase/PostgreSQL版)
-- このファイルをSupabaseのSQL Editorで実行してください

-- タスク管理テーブル（最小構成）
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    completed BOOLEAN DEFAULT FALSE
);

-- コメントの追加
COMMENT ON TABLE tasks IS 'Discord タスク管理Bot用タスクテーブル（最小構成）';
COMMENT ON COLUMN tasks.id IS 'タスクID（自動連番）';
COMMENT ON COLUMN tasks.title IS 'タスクタイトル（元メッセージの内容）';
COMMENT ON COLUMN tasks.completed IS '完了状態（false=未完了, true=完了）';

-- インデックスの作成（パフォーマンス向上）
CREATE INDEX IF NOT EXISTS idx_tasks_completed ON tasks(completed);

-- サンプルデータ（テスト用、必要に応じて削除）
INSERT INTO tasks (title, completed) VALUES 
('📝 Discord Bot開発', false),
('✅ データベース設計', true),
('📝 テスト実行', false)
ON CONFLICT DO NOTHING;

-- スキーマ作成完了の確認
SELECT 
    'Task Management Schema Created Successfully!' as status,
    CURRENT_DATABASE() as current_database,
    CURRENT_USER as current_user,
    NOW() as created_at;