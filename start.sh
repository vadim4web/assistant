#!/usr/bin/env bash
set -euo pipefail

# Шлях до файлу сесії
SESSION_FILE="${SESSION_NAME:-assistant_session}.session"

# Якщо в ENV є SESSION_B64 — декодуємо в файл (safety: overwrite)
if [ -n "${SESSION_B64:-}" ]; then
  echo "Decoding session from SESSION_B64..."
  echo "$SESSION_B64" | base64 -d > "$SESSION_FILE"
  echo "Session written to $SESSION_FILE"
else
  echo "No SESSION_B64 provided — Telethon спробує залогінити заново (інтерактивно)."
fi

# Запустити скрипт
python assistant.py
