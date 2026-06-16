#!/bin/bash
# merge-commands.sh — добавляет блоки wiki-* команд в .opencode/opencode.json
# Использование: ./merge-commands.sh /путь/к/vault
VAULT="$1"
if [ ! -f "$VAULT/.opencode/opencode.json" ]; then
  echo "Ошибка: $VAULT/.opencode/opencode.json не найден"
  exit 1
fi
python3 -c "
import json, sys
with open('$VAULT/.opencode/opencode.json') as f: cfg = json.load(f)
with open('opencode-commands.json') as f: cmds = json.load(f)
cfg.setdefault('command', {}).update(cmds)
with open('$VAULT/.opencode/opencode.json', 'w') as f: json.dump(cfg, f, indent=2, ensure_ascii=False)
print('Команды добавлены.')
"
