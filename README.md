# opencode-llm-wiki

AI-скилл для Obsidian vault — теги, граф связей, TF-IDF-семантика, MOC-хабы, исследования, линтинг. Реализует Karpathy-style LLM Wiki поверх Zettelkasten+Dataview vault. Русский язык.

## Требования

- Python 3.8+ (только stdlib)
- Obsidian vault со структурой `atoms/` + `daily notes/`
- [opencode](https://opencode.ai) CLI

## Установка (автоматическая, рекомендуется)

```bash
git clone https://github.com/boris-chernysh/opencode-llm-wiki.git /tmp/opencode-llm-wiki
/tmp/opencode-llm-wiki/setup.sh /путь/к/vault
```

Всё. `setup.sh` копирует `wiki/`, `SKILL.md`, устанавливает команды из `commands/` в `<vault>/.opencode/commands/`, проверяет `index-tags.py`.

## Установка (ручная)

```bash
git clone https://github.com/boris-chernysh/opencode-llm-wiki.git /tmp/opencode-llm-wiki
cp -r /tmp/opencode-llm-wiki/wiki/ /путь/к/vault/
mkdir -p /путь/к/vault/.opencode/skills/llm-wiki/
cp /tmp/opencode-llm-wiki/SKILL.md /путь/к/vault/.opencode/skills/llm-wiki/SKILL.md
mkdir -p /путь/к/vault/.opencode/commands/
cp /tmp/opencode-llm-wiki/commands/wiki-*.md /путь/к/vault/.opencode/commands/
cd /путь/к/vault && python3 wiki/scripts/index-tags.py
```

## Установка через submodule (для git-отслеживаемых vault)

```bash
cd /путь/к/vault
git submodule add https://github.com/boris-chernysh/opencode-llm-wiki.git .skills/opencode-llm-wiki
.skills/opencode-llm-wiki/setup.sh .
```

## Windows

Симлинки не поддерживаются без Developer Mode. Используйте:

```bash
./setup.sh /путь/к/vault --copy
```

Для обновления:

```bash
./setup.sh /путь/к/vault --copy
```

## Обновление с v0.2.0

Если у вас установлен v0.2.0 с командами, встроенными в `opencode.json` (`command:` блок), мигрируйте:

```bash
cd /path/to/opencode-llm-wiki
git pull
./migrate-commands.sh /путь/к/vault
```

Подробности: [`MIGRATION_COMMANDS.md`](MIGRATION_COMMANDS.md). Поведение команд не меняется.

## Команды

| Команда | Описание |
|---|---|
| `wiki-reindex` | Полная переиндексация vault: теги, граф, анализ, MOC, даты |
| `wiki-research` | Исследование темы по vault с компиляцией находок |
| `wiki-analyze` | Поиск новых Zettelkasten-связей с preview перед применением |
| `wiki-lint` | Read-only проверка здоровья vault и артефактов |
| `wiki-ingest` | Импорт и разметка входящих заметок |

Команды лежат в `commands/wiki-*.md` (по одному файлу на команду) и устанавливаются в `<vault>/.opencode/commands/`. Opencode загружает их нативно. Детали каждой команды — в `SKILL.md` → Command Index.

## Структура vault

Ожидаемая структура Obsidian vault:

```
vault/
├── atoms/                  # атомарные Zettelkasten-заметки
├── daily notes/            # ежедневные заметки
├── templates/              # шаблоны (исключаются из индексации)
├── ASSets/                 # вложения
├── wiki/                  # артефакты скилла (tags/, data/, research/)
└── .opencode/
    ├── commands/           # команды opencode (wiki-*.md)
    └── skills/
        └── llm-wiki/
            └── SKILL.md
```

Frontmatter-конвенции: `tags`, `created`, `links`, `статус` (для задач/проектов).

## Лицензия

MIT
