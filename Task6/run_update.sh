#!/usr/bin/env bash
# Обёртка для запуска update_index.py из cron (Задание 6).
# Логика повторов: при ошибке скрипт пробует запуск ещё раз,
# итоговый успех/неудача фиксируются также внутри update_index.py
# (logs/update.log, logs/update_log.jsonl).
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON_BIN="$SCRIPT_DIR/../.venv/bin/python3"
MAX_RETRIES=2
ATTEMPT=1

while [ "$ATTEMPT" -le "$MAX_RETRIES" ]; do
    if "$PYTHON_BIN" update_index.py; then
        exit 0
    fi
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) попытка $ATTEMPT из $MAX_RETRIES завершилась ошибкой, повтор..." >&2
    ATTEMPT=$((ATTEMPT + 1))
done

exit 1
