#!/bin/bash
# setup.sh — установка llm-wiki скилла в Obsidian vault
# Использование: ./setup.sh /путь/к/vault [--copy] [--update]
set -euo pipefail

VAULT="$(realpath "${1:-.}")"
MODE="${2:---symlink}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 1. Копируем/линкуем agent/
if [ "$MODE" = "--copy" ]; then
  cp -r "$SCRIPT_DIR/agent/" "$VAULT/agent/"
else
  mkdir -p "$VAULT/agent/scripts"
  for script in "$SCRIPT_DIR/agent/scripts/"*.py; do
    ln -sf "$script" "$VAULT/agent/scripts/$(basename "$script")"
  done
  ln -sf "$SCRIPT_DIR/agent/scripts/.gitignore" "$VAULT/agent/scripts/.gitignore" 2>/dev/null || true
  ln -sf "$SCRIPT_DIR/agent/config.json" "$VAULT/agent/config.json"
fi

# 2. Копируем SKILL.md
mkdir -p "$VAULT/.opencode/skills/llm-wiki/"
cp "$SCRIPT_DIR/SKILL.md" "$VAULT/.opencode/skills/llm-wiki/SKILL.md"

# 3. Мержим команды
if [ -f "$SCRIPT_DIR/merge-commands.sh" ]; then
  bash "$SCRIPT_DIR/merge-commands.sh" "$VAULT"
else
  echo "⚠ merge-commands.sh не найден. Добавь команды вручную из opencode-commands.json"
fi

# 4. Проверка
echo "Проверка: запуск index-tags.py..."
cd "$VAULT" && python3 agent/scripts/index-tags.py && echo "✓ Установка завершена."
