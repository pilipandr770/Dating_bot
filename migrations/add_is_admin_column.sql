-- Добавляем столбец is_admin в таблицу users
ALTER TABLE dating_bot.users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE;

-- Устанавливаем флаг is_admin=true для администраторов из ADMIN_IDS
-- Для Telegram ID 7444992311
UPDATE dating_bot.users SET is_admin = TRUE WHERE telegram_id = '7444992311';
