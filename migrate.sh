#!/bin/bash
# migrate.sh — миграция llm-wiki с v0.1.0 (agent/) на v0.2.0 (wiki/)
# Использование: ./migrate.sh /путь/к/vault [--copy]
set -euo pipefail

VAULT="$(realpath "${1:-.}")"
MODE="${2:---symlink}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Миграция llm-wiki v0.1.0 → v0.2.0 ==="

# ---- 1. Save user config overrides (before setup.sh overwrites) ----
if [ -f "$VAULT/agent/config.json" ]; then
    echo "▸ Сохранение пользовательских настроек из agent/config.json..."
    python3 -c "
import json

with open('$VAULT/agent/config.json') as f:
    old = json.load(f)

# Keep only user-modifiable sections
saved = {}
if 'thresholds' in old:
    saved['thresholds'] = old['thresholds']
if 'exclude' in old:
    saved['exclude'] = old['exclude']
if 'source_dirs' in old:
    saved['source_dirs'] = old['source_dirs']

with open('/tmp/llm-wiki-migrate-config.json', 'w') as f:
    json.dump(saved, f, indent=2, ensure_ascii=False)
print('OK')
"
else
    echo "▸ agent/config.json не найден — пропускаю."
    echo '{}' > /tmp/llm-wiki-migrate-config.json
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

# ---- 3. Delete stale scripts (old code with 'agent' paths) ----
if [ -d "$VAULT/agent/scripts" ]; then
    echo "▸ Удаление старых скриптов agent/scripts/..."
    rm -rf "$VAULT/agent/scripts"
    echo "OK"
fi

# ---- 4. Rename agent/ → wiki/ (preserves tags/, data/, research/) ----
if [ -d "$VAULT/agent" ]; then
    echo "▸ Переименование agent/ → wiki/"
    mv "$VAULT/agent" "$VAULT/wiki"
    echo "OK"
fi

# ---- 5. Run setup with fresh scripts ----
echo "▸ Запуск setup.sh..."
bash "$SCRIPT_DIR/setup.sh" "$VAULT" "$MODE"

# ---- 6. Restore merged config (setup.sh overwrites config.json) ----
echo "▸ Восстановление пользовательских настроек..."
python3 -c "
import json, os

with open('/tmp/llm-wiki-migrate-config.json') as f:
    saved = json.load(f)

config_path = '$VAULT/wiki/config.json'
with open(config_path) as f:
    new = json.load(f)

# Apply saved user overrides
for k, v in saved.get('thresholds', {}).items():
    new.setdefault('thresholds', {})[k] = v

for k, v in saved.get('exclude', {}).items():
    if k in new.get('exclude', {}):
        merged = list(dict.fromkeys(v + new['exclude'][k]))
        new['exclude'][k] = merged
    else:
        new.setdefault('exclude', {})[k] = v

for k, v in saved.get('source_dirs', {}).items():
    new.setdefault('source_dirs', {})[k] = v

# Ensure new fields exist
new.setdefault('exclude', {}).setdefault('tags_from_analyze', ['daily-note'])

with open(config_path, 'w') as f:
    json.dump(new, f, indent=2, ensure_ascii=False)
print('OK')
"
rm -f /tmp/llm-wiki-migrate-config.json

echo ""
echo "=== Миграция завершена ==="
echo "Что изменилось:"
echo "  • agent/      → wiki/ (теги, данные, исследования сохранены)"
echo "  • wiki-process-note → wiki-ingest"
echo "  • wiki-moc теперь read-only (индекс без создания MOC-заметок)"
echo "  • wiki/config.json — добавлено exclude.tags_from_analyze"
echo "  • wiki/dates/ — новый индекс по датам (wiki-reindex)"
echo ""
echo "Запусти /wiki-reindex для перестроения всех артефактов."
