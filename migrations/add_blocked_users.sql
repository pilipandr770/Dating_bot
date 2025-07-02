-- файл: migrations/add_blocked_users.sql

-- Таблица для блокированных пользователей
CREATE TABLE IF NOT EXISTS dating_bot.blocked_users (
    id SERIAL PRIMARY KEY,
    blocker_id INTEGER REFERENCES dating_bot.users(id) ON DELETE CASCADE,
    blocked_id INTEGER REFERENCES dating_bot.users(id) ON DELETE CASCADE,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(blocker_id, blocked_id)
);

-- Индекс для быстрого поиска блокировок
CREATE INDEX IF NOT EXISTS idx_blocked_users_blocker_id ON dating_bot.blocked_users(blocker_id);
CREATE INDEX IF NOT EXISTS idx_blocked_users_blocked_id ON dating_bot.blocked_users(blocked_id);

-- Добавляем язык в таблицу пользователей, если его еще нет
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_schema = 'dating_bot' 
                   AND table_name = 'users' 
                   AND column_name = 'language') THEN
        ALTER TABLE dating_bot.users ADD COLUMN language TEXT DEFAULT 'ua';
    END IF;
END $$;
