#!/bin/bash
# migrate.sh — миграция llm-wiki с v0.1.0 (agent/) на v0.2.0 (wiki/)
# Использование: ./migrate.sh /путь/к/vault [--copy]
set -euo pipefail

VAULT="$(realpath "${1:-.}")"
MODE="${2:---symlink}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Миграция llm-wiki v0.1.0 → v0.2.0 ==="

# ---- 1. Migrate config.json ----
if [ -f "$VAULT/agent/config.json" ]; then
    echo "▸ Перенос agent/config.json → wiki/config.json (сохраняю пользовательские значения)..."
    python3 -c "
import json, os

old_path = '$VAULT/agent/config.json'
new_path = '$VAULT/wiki/config.json'

with open(old_path) as f:
    old = json.load(f)

# Load new defaults (shipped with this version)
if os.path.exists(new_path):
    with open(new_path) as f:
        new = json.load(f)
else:
    with open('$SCRIPT_DIR/wiki/config.json') as f:
        new = json.load(f)

# Preserve user's threshold overrides
for k, v in old.get('thresholds', {}).items():
    new.setdefault('thresholds', {})[k] = v

# Preserve user's exclude lists (dedup with new defaults)
for k, v in old.get('exclude', {}).items():
    if k in new.get('exclude', {}):
        merged = list(dict.fromkeys(v + new['exclude'][k]))
        new['exclude'][k] = merged
    else:
        new.setdefault('exclude', {})[k] = v

# Preserve user's source_dirs
for k, v in old.get('source_dirs', {}).items():
    new.setdefault('source_dirs', {})[k] = v

# Ensure new fields exist
new.setdefault('exclude', {}).setdefault('tags_from_analyze', ['daily-note'])

with open(new_path, 'w') as f:
    json.dump(new, f, indent=2, ensure_ascii=False)
print('OK')
"
else
    echo "▸ agent/config.json не найден — пропускаю миграцию конфига."
fi

# ---- 2. Rename command in .opencode/opencode.json ----
if [ -f "$VAULT/.opencode/opencode.json" ]; then
    echo "▸ Переименование wiki-process-note → wiki-ingest..."
    python3 -c "
import json

path = '$VAULT/.opencode/opencode.json'
with open(path) as f:
    cfg = json.load(f)

if 'command' in cfg and 'wiki-process-note' in cfg['command']:
    cfg['command']['wiki-ingest'] = cfg['command'].pop('wiki-process-note')
    with open(path, 'w') as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    print('OK')
else:
    print('команда уже переименована или отсутствует — OK')
"
fi

# ---- 3. Remove old agent/ directory ----
if [ -d "$VAULT/agent" ]; then
    echo "▸ Удаление agent/..."
    rm -rf "$VAULT/agent"
    echo "OK"
fi

# ---- 4. Run setup with new structure ----
echo "▸ Запуск setup.sh..."
bash "$SCRIPT_DIR/setup.sh" "$VAULT" "$MODE"

echo ""
echo "=== Миграция завершена ==="
echo "Что изменилось:"
echo "  • agent/      → wiki/"
echo "  • wiki-process-note → wiki-ingest"
echo "  • wiki-moc теперь read-only (индекс без создания MOC-заметок)"
echo "  • wiki/config.json — добавлено exclude.tags_from_analyze"
echo "  • wiki/dates/ — новый индекс по датам (wiki-reindex)"
echo ""
echo "Запусти /wiki-reindex для перестроения всех артефактов."
