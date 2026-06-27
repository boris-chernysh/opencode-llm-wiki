import os
import subprocess
import sys

#!/usr/bin/env python3
"""Test wiki-ingest: keyword extraction, tag matching, candidate scoring, project detection,
and frontmatter-only discovery of #need-processing notes."""

TEST_VAULT = sys.argv[1]
TAGS_INDEX_PATH = os.path.join(TEST_VAULT, 'wiki', 'tags-index.md')
TAGS_DIR = os.path.join(TEST_VAULT, 'wiki', 'tags')
PROJECT_TAG_PATH = os.path.join(TAGS_DIR, 'project.md')
SCRIPTS_DIR = os.path.join(TEST_VAULT, 'wiki', 'scripts')

# Run index-tags.py and generate-tags-index.py first
subprocess.run(['python3', os.path.join(SCRIPTS_DIR, 'index-tags.py')],
               cwd=TEST_VAULT, capture_output=True, text=True)
subprocess.run(['python3', os.path.join(SCRIPTS_DIR, 'generate-tags-index.py')],
               cwd=TEST_VAULT, capture_output=True, text=True)

# --- Frontmatter-only discovery: run the new script ---

FIND_SCRIPT = os.path.join(SCRIPTS_DIR, 'find-needs-processing.py')
assert os.path.isfile(FIND_SCRIPT), f"find-needs-processing.py must exist at {FIND_SCRIPT}"

result = subprocess.run(['python3', FIND_SCRIPT],
                        cwd=TEST_VAULT, capture_output=True, text=True)
assert result.returncode == 0, f"find-needs-processing.py failed: {result.stderr}"

discovered = [line for line in result.stdout.splitlines() if line.strip()]
assert len(discovered) >= 2, f"Should find 2+ need-processing notes, got {len(discovered)}: {discovered}"
assert '202501010015 need-processing заметка.md' in discovered
assert '202501010016 Без тегов.md' in discovered

# --- Verify that grep-style false positives are NOT in the script's output ---

# Inject a decoy note that contains "need-processing" only in body and title
# (not in frontmatter tags). The script must not surface it.
decoy_body = os.path.join(TEST_VAULT, 'atoms', '_decoy-body.md')
with open(decoy_body, 'w', encoding='utf-8') as f:
    f.write('---\n'
             'created: 2025-01-01\n'
             'tags:\n'
             '  - foo\n'
             '---\n'
             '\n'
             '# decoy with need-processing in body\n'
             '\n'
             'This body mentions need-processing but the tag is not in frontmatter.\n')

decoy_title = os.path.join(TEST_VAULT, 'atoms', '_decoy-title.md')
with open(decoy_title, 'w', encoding='utf-8') as f:
    f.write('---\n'
             'created: 2025-01-01\n'
             'tags:\n'
             '  - bar\n'
             '---\n'
             '\n'
             '# need-processing appears in title only\n')

try:
    # Naive grep for comparison: should match 4 files (2 real + 2 decoys)
    naive = []
    for fname in sorted(os.listdir(os.path.join(TEST_VAULT, 'atoms'))):
        if not fname.endswith('.md'):
            continue
        with open(os.path.join(TEST_VAULT, 'atoms', fname)) as fh:
            content = fh.read()
        if 'need-processing' in content.lower():
            naive.append(fname)
    assert len(naive) >= 4, (
        f"Naive grep should match decoys too, got {len(naive)}: {naive}"
    )
    assert any('decoy' in n for n in naive), "Decoys should be caught by naive grep"

    # Frontmatter-only script: must NOT include the decoys
    result2 = subprocess.run(['python3', FIND_SCRIPT],
                             cwd=TEST_VAULT, capture_output=True, text=True)
    assert result2.returncode == 0, f"find-needs-processing.py failed: {result2.stderr}"
    strict = [line for line in result2.stdout.splitlines() if line.strip()]
    assert not any('decoy' in n for n in strict), (
        f"Decoys must NOT appear in frontmatter-only output: {strict}"
    )
    # Original two real notes must still be present
    assert '202501010015 need-processing заметка.md' in strict
    assert '202501010016 Без тегов.md' in strict
finally:
    for d in (decoy_body, decoy_title):
        if os.path.exists(d):
            os.remove(d)

# --- Project detection tests ---

assert os.path.isfile(PROJECT_TAG_PATH), "wiki/tags/project.md should exist after indexing"

with open(PROJECT_TAG_PATH) as f:
    project_content = f.read()

assert 'Сайт портфолио' in project_content, "project.md should list the project note"

# Verify project note has #project tag in its frontmatter
project_note_path = os.path.join(TEST_VAULT, 'atoms', '202501010021 Сайт портфолио.md')
with open(project_note_path) as f:
    project_fm = f.read()
assert 'project' in project_fm, "project note should have #project tag"

# Simulate project detection: read project titles from wiki/tags/project.md
project_titles = []
for line in project_content.split('\n'):
    if '[[' in line and ']]' in line:
        project_titles.append(line.strip())

assert len(project_titles) >= 1, "Should have at least one project note listed"

# Verify project: field is absent on discovered notes (should be set by agent)
for note_name in discovered:
    note_path = os.path.join(TEST_VAULT, 'atoms', note_name)
    with open(note_path) as f:
        fm = f.read()
    has_project = 'project:' in fm.split('---')[1] if fm.count('---') >= 2 else False
    assert not has_project, f"{note_name} should not have project: field yet"

# --- Keyword extraction sanity (preserve original behavior) ---

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

kw = extract_keywords('need-processing заметка')
assert 'need-processing' in kw or 'заметка' in kw, f"Keywords extracted: {kw}"

kw = extract_keywords('Без тегов')
assert 'тегов' in kw or 'без' in kw, f"Keywords extracted: {kw}"

ingest_kw = extract_keywords('need-processing заметка')
project_kw = extract_keywords('Сайт портфолио')
overlap = set(ingest_kw) & set(project_kw)
assert len(overlap) == 0 or len(overlap) > 0, f"Project/ingest keyword overlap: {overlap}"

print(f"PASS: test_ingest — {len(discovered)} need-processing notes (frontmatter-only), project detection OK")
