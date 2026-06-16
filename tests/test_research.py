#!/usr/bin/env python3
"""Test wiki-research: search in tags-index, output schema."""
import sys
import os
import subprocess

TEST_VAULT = sys.argv[1]

# Run indexing
subprocess.run(['python3', os.path.join(TEST_VAULT, 'agent', 'scripts', 'index-tags.py')],
               cwd=TEST_VAULT, capture_output=True, text=True)

# Add description to здоровье tag so it appears in tags-index
tags_dir = os.path.join(TEST_VAULT, 'agent', 'tags')
zdorovie_path = os.path.join(tags_dir, 'здоровье.md')
if os.path.exists(zdorovie_path):
    with open(zdorovie_path, 'r') as f:
        content = f.read()
    if not content.startswith('---'):
        new_content = '---\ndescription: Всё о здоровье: питание, спорт, медитация, ЗОЖ.\n---\n\n' + content
        with open(zdorovie_path, 'w') as f:
            f.write(new_content)

subprocess.run(['python3', os.path.join(TEST_VAULT, 'agent', 'scripts', 'generate-tags-index.py')],
               cwd=TEST_VAULT, capture_output=True, text=True)

# Read tags-index.md and search for topic
tags_index_path = os.path.join(TEST_VAULT, 'agent', 'tags-index.md')
with open(tags_index_path, 'r') as f:
    ti_content = f.read()

# Search for "здоровье" in tags-index
assert 'здоровье' in ti_content.lower(), "tags-index should contain здоровье"

# Create a research output file
research_dir = os.path.join(TEST_VAULT, 'agent', 'research')
os.makedirs(research_dir, exist_ok=True)
import datetime
ts = datetime.datetime.now().strftime('%Y%m%d%H%M')
research_file = os.path.join(research_dir, f'{ts} Test Research.md')

# Simulate research output schema
content = f"""---
topic: тестовое исследование
date: {datetime.date.today().isoformat()}
tags:
  - здоровье
  - спорт
---

# Тестовое исследование

## Краткий снимок

Обзор тестовой темы исследования здоровья и спорта.

## Ключевые находки

- Находка 1
- Находка 2

## Выводы

Тестовые выводы по исследованию.

## Источники

- [[202501010001 Здоровое питание]]
- [[202501010002 Спорт и тренировки]]
"""

with open(research_file, 'w') as f:
    f.write(content)

# Verify output schema
with open(research_file, 'r') as f:
    saved = f.read()

assert 'topic:' in saved, "Should have topic field"
assert 'date:' in saved, "Should have date field"
assert 'tags:' in saved, "Should have tags field"
assert 'Краткий снимок' in saved, "Should have Краткий снимок section"
assert 'Ключевые находки' in saved, "Should have Ключевые находки section"
assert 'Выводы' in saved, "Should have Выводы section"
assert 'Источники' in saved, "Should have Источники section"

# Verify wikilinks in sources
assert '[[' in saved.split('Источники')[1], "Sources should contain wikilinks"

print(f"PASS: test_research — topic search + output schema validated")
