#!/bin/bash
# setup.sh — установка llm-wiki скилла в Obsidian vault
# Использование: ./setup.sh /путь/к/vault [--copy] [--update]
set -euo pipefail

VAULT="$(realpath "${1:-.}")"
MODE="${2:---symlink}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 1. Копируем/линкуем wiki/
if [ "$MODE" = "--copy" ]; then
  cp -r "$SCRIPT_DIR/wiki/" "$VAULT/wiki/"
else
  mkdir -p "$VAULT/wiki/scripts"
  for script in "$SCRIPT_DIR/wiki/scripts/"*.py; do
    ln -sf "$script" "$VAULT/wiki/scripts/$(basename "$script")"
  done
  ln -sf "$SCRIPT_DIR/wiki/scripts/.gitignore" "$VAULT/wiki/scripts/.gitignore" 2>/dev/null || true
  ln -sf "$SCRIPT_DIR/wiki/config.json" "$VAULT/wiki/config.json"
fi

# 2. Копируем SKILL.md
mkdir -p "$VAULT/.opencode/skills/llm-wiki/"
cp "$SCRIPT_DIR/SKILL.md" "$VAULT/.opencode/skills/llm-wiki/SKILL.md"

# 3. Устанавливаем команды в .opencode/commands/
mkdir -p "$VAULT/.opencode/commands"
for cmd in reindex research analyze lint ingest; do
  src="$SCRIPT_DIR/commands/wiki-$cmd.md"
  dst="$VAULT/.opencode/commands/wiki-$cmd.md"
  if [ ! -f "$src" ]; then
    echo "⚠ Пропуск: $src не найден"
    continue
  fi
  if [ "$MODE" = "--copy" ]; then
    cp "$src" "$dst"
  else
    ln -sf "$src" "$dst"
  fi
done

# 4. Очистка устаревшего command: блока в opencode.json (если есть)
if [ -f "$VAULT/.opencode/opencode.json" ]; then
  python3 -c "
import json
p='$VAULT/.opencode/opencode.json'
d=json.load(open(p))
if 'command' in d:
    d.pop('command')
    json.dump(d, open(p,'w'), indent=2, ensure_ascii=False)
    print('Удалён устаревший command: блок из opencode.json')
" 2>/dev/null || true
fi

# 5. Проверка
echo "Проверка: запуск index-tags.py..."
cd "$VAULT" && python3 wiki/scripts/index-tags.py && echo "✓ Установка завершена."
