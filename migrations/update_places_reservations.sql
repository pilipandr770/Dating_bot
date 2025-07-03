-- Обновление таблиц для мест и бронирований
-- Добавление новых полей, соответствующих моделям SQLAlchemy

-- Обновляем таблицу places
ALTER TABLE IF EXISTS dating_bot.places
    ADD COLUMN IF NOT EXISTS partner_name TEXT,
    ADD COLUMN IF NOT EXISTS external_id TEXT,
    ADD COLUMN IF NOT EXISTS type TEXT,
    ADD COLUMN IF NOT EXISTS place_metadata JSONB,  -- Переименовано из metadata, т.к. это зарезервированное слово в SQLAlchemy
    ADD COLUMN IF NOT EXISTS is_promoted BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS image_url TEXT;

-- Создаем индекс для external_id
CREATE UNIQUE INDEX IF NOT EXISTS idx_places_external_id ON dating_bot.places(external_id) 
    WHERE external_id IS NOT NULL;

-- Обновляем таблицу reservations
ALTER TABLE IF EXISTS dating_bot.reservations
    ADD COLUMN IF NOT EXISTS match_id INTEGER REFERENCES dating_bot.matches(id),
    ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'pending',
    ADD COLUMN IF NOT EXISTS details JSONB,
    ADD COLUMN IF NOT EXISTS external_reference TEXT;
