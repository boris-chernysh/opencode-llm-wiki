import os
import subprocess
import sys

#!/usr/bin/env python3
"""Test generate-tags-index.py: entries count, descriptions."""

TEST_VAULT = sys.argv[1]
INDEX_SCRIPT = os.path.join(TEST_VAULT, 'wiki', 'scripts', 'index-tags.py')
GEN_SCRIPT = os.path.join(TEST_VAULT, 'wiki', 'scripts', 'generate-tags-index.py')
INDEX_PATH = os.path.join(TEST_VAULT, 'wiki', 'tags-index.md')

result = subprocess.run(['python3', INDEX_SCRIPT], cwd=TEST_VAULT, capture_output=True, text=True)
assert result.returncode == 0, f"index-tags.py failed: {result.stderr}"

# Add description to a tag so it appears in tags-index
tags_dir = os.path.join(TEST_VAULT, 'wiki', 'tags')
for tag_file in sorted(os.listdir(tags_dir)):
    if tag_file == 'здоровье.md':
        tag_path = os.path.join(tags_dir, tag_file)
        with open(tag_path) as f:
            content = f.read()
        if not content.startswith('---'):
            new_content = '---\ndescription: Всё о здоровье: питание, спорт, медитация, ЗОЖ.\n---\n\n' + content
            with open(tag_path, 'w') as f:
                f.write(new_content)
        break

result2 = subprocess.run(['python3', GEN_SCRIPT], cwd=TEST_VAULT, capture_output=True, text=True)
assert result2.returncode == 0, f"generate-tags-index.py failed: {result2.stderr}"

with open(INDEX_PATH) as f:
    content = f.read()

lines = [line for line in content.split('\n') if line.startswith('- #')]
assert len(lines) > 0, "tags-index.md should have entries"

assert 'здоровье' in content, f"Expected здоровье in tags-index.md: {content[:500]}"

print(f"PASS: test_tags_index — {len(lines)} entries in tags-index.md")
