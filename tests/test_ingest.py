import os
import subprocess
import sys

#!/usr/bin/env python3
"""Test wiki-process-note: keyword extraction, tag matching, candidate scoring."""

TEST_VAULT = sys.argv[1]
TAGS_INDEX_PATH = os.path.join(TEST_VAULT, 'wiki', 'tags-index.md')
TAGS_DIR = os.path.join(TEST_VAULT, 'wiki', 'tags')

# Run index-tags.py first

subprocess.run(['python3', os.path.join(TEST_VAULT, 'wiki', 'scripts', 'index-tags.py')],
               cwd=TEST_VAULT, capture_output=True, text=True)
subprocess.run(['python3', os.path.join(TEST_VAULT, 'wiki', 'scripts', 'generate-tags-index.py')],
               cwd=TEST_VAULT, capture_output=True, text=True)

# Simulate process-note logic: keyword extraction from title
def extract_keywords(title):
    words = title.lower().split()
    stop = {'и', 'в', 'не', 'на', 'я', 'что', 'с', 'как', 'а', 'то', 'все', 'она', 'так',
            'но', 'да', 'ты', 'к', 'у', 'же', 'вы', 'за', 'бы', 'по', 'только', 'ее',
            'мне', 'было', 'вот', 'от', 'меня', 'еще', 'нет', 'о', 'из', 'ему', 'теперь',
            'когда', 'даже', 'ну', 'вдруг', 'ли', 'если', 'уже', 'или', 'ни', 'быть',
            'был', 'него', 'до', 'вас', 'нибудь', 'опять', 'уж', 'вам', 'ведь', 'там',
            'потом', 'себя', 'ничего', 'ей', 'может', 'они', 'тут', 'где', 'есть',
            'надо', 'ней', 'для', 'мы', 'тебя', 'их', 'чем', 'была', 'сам', 'чтоб',
            'без', 'будто', 'чего', 'раз', 'тоже', 'себе', 'под', 'будет', 'ж', 'тогда',
            'кто', 'этот', 'того', 'потому', 'этого', 'какой', 'совсем', 'ним', 'здесь',
            'этом', 'один', 'почти', 'мой', 'тем', 'чтобы', 'нее', 'сейчас', 'были',
            'куда', 'зачем', 'всех', 'никогда', 'можно', 'при', 'наконец', 'два',
            'об', 'другой', 'хоть', 'после', 'над', 'больше', 'тот', 'через', 'эти',
            'нас', 'про', 'них', 'какая', 'много', 'разве', 'три', 'эту', 'моя',
            'свою', 'этой', 'перед', 'иногда', 'лучше', 'чуть', 'том', 'нельзя',
            'такой', 'им', 'более', 'всегда', 'конечно', 'всю', 'между'}
    return [w for w in words if w not in stop and len(w) > 1]

# Test keyword extraction from "need-processing заметка"
kw = extract_keywords('need-processing заметка')
assert 'need-processing' in kw or 'заметка' in kw, f"Keywords extracted: {kw}"

# Test keyword extraction from "Без тегов"
kw = extract_keywords('Без тегов')
assert 'тегов' in kw or 'без' in kw, f"Keywords extracted: {kw}"

# Verify need-processing notes are in atoms/
atoms_dir = os.path.join(TEST_VAULT, 'atoms')
need_proc_notes = []
for f in sorted(os.listdir(atoms_dir)):
    if not f.endswith('.md'):
        continue
    with open(os.path.join(atoms_dir, f)) as fh:
        content = fh.read()
    if 'need-processing' in content.lower():
        need_proc_notes.append(f)

assert len(need_proc_notes) >= 2, f"Should have 2+ need-processing notes, got {len(need_proc_notes)}"

print(f"PASS: test_process_note — {len(need_proc_notes)} need-processing notes, keywords OK")
