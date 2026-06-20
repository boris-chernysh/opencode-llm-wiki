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

Всё. `setup.sh` копирует `wiki/`, `SKILL.md`, мержит команды, проверяет `index-tags.py`.

## Установка (ручная)

```bash
git clone https://github.com/boris-chernysh/opencode-llm-wiki.git /tmp/opencode-llm-wiki
cp -r /tmp/opencode-llm-wiki/wiki/ /путь/к/vault/
mkdir -p /путь/к/vault/.opencode/skills/llm-wiki/
cp /tmp/opencode-llm-wiki/SKILL.md /путь/к/vault/.opencode/skills/llm-wiki/SKILL.md
./merge-commands.sh /путь/к/vault
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
./setup.sh /путь/к/vault --copy --update
```

## Команды

| Команда | Описание |
|---|---|
| `wiki-reindex` | Полная переиндексация vault: теги, граф, анализ, MOC, даты |
| `wiki-research` | Исследование темы по vault с компиляцией находок |
| `wiki-analyze` | Поиск новых Zettelkasten-связей с preview перед применением |
| `wiki-lint` | Read-only проверка здоровья vault и артефактов |
| `wiki-ingest` | Импорт и разметка входящих заметок |

Команды добавляются в `.opencode/opencode.json` через `merge-commands.sh`.

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
    └── skills/
        └── llm-wiki/
            └── SKILL.md
```

Frontmatter-конвенции: `tags`, `created`, `links`, `статус` (для задач/проектов).

## Лицензия

MIT
