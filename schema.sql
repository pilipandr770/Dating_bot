
-- файл: schema.sql
-- Схема: dating_bot

CREATE SCHEMA IF NOT EXISTS dating_bot;

-- Користувачі
CREATE TABLE IF NOT EXISTS dating_bot.users (
    id SERIAL PRIMARY KEY,
    telegram_id TEXT UNIQUE NOT NULL,
    first_name TEXT NOT NULL,
    age INTEGER,
    gender TEXT,
    orientation TEXT,
    city TEXT,
    bio TEXT,
    is_verified BOOLEAN DEFAULT FALSE,
    token_balance INTEGER DEFAULT 0,
    is_premium BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Фото користувачів
CREATE TABLE IF NOT EXISTS dating_bot.user_photos (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES dating_bot.users(id) ON DELETE CASCADE,
    file_id TEXT NOT NULL
);

-- Питання анкети
CREATE TABLE IF NOT EXISTS dating_bot.questions (
    id SERIAL PRIMARY KEY,
    question_text TEXT NOT NULL,
    is_multiple_choice BOOLEAN DEFAULT FALSE
);

-- Відповіді користувачів
CREATE TABLE IF NOT EXISTS dating_bot.user_answers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES dating_bot.users(id) ON DELETE CASCADE,
    question_id INTEGER REFERENCES dating_bot.questions(id) ON DELETE CASCADE,
    answer_text TEXT
);

-- Свайпи
CREATE TABLE IF NOT EXISTS dating_bot.swipes (
    id SERIAL PRIMARY KEY,
    swiper_id INTEGER REFERENCES dating_bot.users(id) ON DELETE CASCADE,
    swiped_id INTEGER REFERENCES dating_bot.users(id) ON DELETE CASCADE,
    is_like BOOLEAN NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Метчі
CREATE TABLE IF NOT EXISTS dating_bot.matches (
    id SERIAL PRIMARY KEY,
    user_1_id INTEGER REFERENCES dating_bot.users(id) ON DELETE CASCADE,
    user_2_id INTEGER REFERENCES dating_bot.users(id) ON DELETE CASCADE,
    thread_id TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Повідомлення в чаті
CREATE TABLE IF NOT EXISTS dating_bot.messages (
    id SERIAL PRIMARY KEY,
    thread_id TEXT NOT NULL,
    sender_id INTEGER REFERENCES dating_bot.users(id) ON DELETE CASCADE,
    message_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Місця для побачень
CREATE TABLE IF NOT EXISTS dating_bot.places (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    city TEXT,
    type TEXT,
    link TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    is_partner BOOLEAN DEFAULT FALSE
);

-- Бронювання
CREATE TABLE IF NOT EXISTS dating_bot.reservations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES dating_bot.users(id) ON DELETE CASCADE,
    place_id INTEGER REFERENCES dating_bot.places(id) ON DELETE CASCADE,
    reservation_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Платежі
CREATE TABLE IF NOT EXISTS dating_bot.payments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES dating_bot.users(id) ON DELETE CASCADE,
    type TEXT,
    amount FLOAT,
    currency TEXT DEFAULT 'eur',
    token_amount INTEGER,
    status TEXT,
    stripe_session_id TEXT,
    tariff TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Запити на виведення токенів
CREATE TABLE IF NOT EXISTS dating_bot.token_withdrawals (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES dating_bot.users(id) ON DELETE CASCADE,
    token_amount INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Логи для адміністратора
CREATE TABLE IF NOT EXISTS dating_bot.admin_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES dating_bot.users(id) ON DELETE SET NULL,
    log_type TEXT,
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Скарги на профілі
CREATE TABLE IF NOT EXISTS dating_bot.reports (
    id SERIAL PRIMARY KEY,
    reporter_id INTEGER REFERENCES dating_bot.users(id) ON DELETE CASCADE,
    reported_id INTEGER REFERENCES dating_bot.users(id) ON DELETE CASCADE,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
