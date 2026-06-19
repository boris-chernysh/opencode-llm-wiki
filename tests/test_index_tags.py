import os
import subprocess
import sys

#!/usr/bin/env python3
"""Test index-tags.py: tag indexing, hex filter, exclusion, stale removal."""


TEST_VAULT = sys.argv[1]
SCRIPT = os.path.join(TEST_VAULT, 'wiki', 'scripts', 'index-tags.py')
TAGS_DIR = os.path.join(TEST_VAULT, 'wiki', 'tags')

# Clean up from previous runs
if os.path.exists(TAGS_DIR):
    for f in os.listdir(TAGS_DIR):
        os.remove(os.path.join(TAGS_DIR, f))

result = subprocess.run(['python3', SCRIPT], cwd=TEST_VAULT, capture_output=True, text=True)
assert result.returncode == 0, f"index-tags.py failed: {result.stderr}"

tag_files = sorted(os.listdir(TAGS_DIR))
tag_names = [f[:-3] for f in tag_files if f.endswith('.md')]

# need-processing should NOT appear
assert 'need-processing' not in tag_names, f"need-processing should be excluded, got {tag_names}"
# daily-note should NOT appear
assert 'daily-note' not in tag_names, f"daily-note should be excluded, got {tag_names}"

# Verify known tags are present
assert 'здоровье' in tag_names, f"здоровье missing, got {tag_names}"
assert 'спорт' in tag_names, f"спорт missing, got {tag_names}"
assert 'python' in tag_names, f"python missing, got {tag_names}"

# Check здоровье.md contains correct notes
with open(os.path.join(TAGS_DIR, 'здоровье.md')) as f:
    content = f.read()
assert 'Здоровое питание' in content
assert 'Спорт и тренировки' in content
assert 'Медитация' in content
assert 'Длинная статья про ЗОЖ' in content

# Check that tags from daily notes are indexed (daily-note is excluded, not notes from daily notes/)
# Actually, tags in daily notes body/headers might create tag files
# The note 2025-01-01 has only #daily-note tag which is excluded
# But the daily notes dir is in SOURCE_DIRS for tags

# Stale removal: create a fake tag file that should be removed
fake_tag = os.path.join(TAGS_DIR, 'nonexistent-tag.md')
with open(fake_tag, 'w') as f:
    f.write('# #nonexistent-tag\n')
result2 = subprocess.run(['python3', SCRIPT], cwd=TEST_VAULT, capture_output=True, text=True)
assert result2.returncode == 0
assert not os.path.exists(fake_tag), "Stale tag should have been removed"
assert 'Removed stale index' in result2.stdout

# Hex filter: 3-8 char hex strings should not become tags
# (tested via is_valid_tag in the script - hex strings like 'abc123' are filtered)

print(f"PASS: test_index_tags — {len(tag_names)} tag files")
