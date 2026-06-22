#!/bin/bash
# migrate-commands.sh — миграция v0.2.0 → v0.3.0: перенос команд в .opencode/commands/*.md
# Использование: ./migrate-commands.sh /путь/к/vault [--copy]
set -euo pipefail

VAULT="$(realpath "${1:-.}")"
MODE="${2:---symlink}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Миграция llm-wiki v0.2.0 → v0.3.0 (commands as .md) ==="

OC_JSON="$VAULT/.opencode/opencode.json"
OC_CMDS="$VAULT/.opencode/commands"

# 0. Sanity checks
[ -d "$VAULT" ] || { echo "Ошибка: $VAULT не существует"; exit 1; }

# 1. Backup opencode.json (if it has the old command: block)
if [ -f "$OC_JSON" ] && python3 -c "import json,sys; d=json.load(open('$OC_JSON')); sys.exit(0 if 'command' in d else 1)" 2>/dev/null; then
  echo "▸ Бэкап opencode.json → opencode.json.bak-v0.2.0"
  cp "$OC_JSON" "$OC_JSON.bak-v0.2.0"
fi

# 2. Strip command: block
if [ -f "$OC_JSON" ]; then
  echo "▸ Удаление command: блока из opencode.json..."
  python3 -c "
import json
p='$OC_JSON'
with open(p) as f:
    d = json.load(f)
if 'command' in d:
    n = len(d['command'])
    d.pop('command')
    with open(p, 'w') as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
    print(f'  удалено {n} команд')
else:
    print('  command: блок отсутствует — OK')
"
fi

# 3. Install commands/ as md files (symlinks by default, --copy for Windows)
echo "▸ Установка команд в $OC_CMDS..."
mkdir -p "$OC_CMDS"
for cmd in reindex research analyze lint ingest; do
  src="$SCRIPT_DIR/commands/wiki-$cmd.md"
  dst="$OC_CMDS/wiki-$cmd.md"
  if [ ! -f "$src" ]; then
    echo "  ⚠ Пропуск: $src не найден"
    continue
  fi
  # Remove existing symlink/file to refresh
  rm -f "$dst"
  if [ "$MODE" = "--copy" ]; then
    cp "$src" "$dst"
  else
    ln -sf "$src" "$dst"
  fi
  echo "  ✓ wiki-$cmd.md"
done

echo ""
echo "=== Миграция завершена ==="
echo "Что изменилось:"
echo "  • 5 команд перенесены в $OC_CMDS/*.md (opencode загружает их нативно)"
echo "  • command: блок удалён из opencode.json (бэкап: opencode.json.bak-v0.2.0)"
echo "  • opencode-commands.json + merge-commands.sh больше не нужны"
echo ""
echo "Smoke test:"
echo "  opencode run --command wiki-reindex --dir $VAULT"
