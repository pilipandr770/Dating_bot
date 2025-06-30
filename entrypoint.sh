#!/bin/bash

echo "⏳ Ініціалізація бази..."
psql $POSTGRES_URL -f /app/schema.sql

echo "🚀 Запуск бота..."
python3 -m app.bot
