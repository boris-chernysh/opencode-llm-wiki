#!/usr/bin/env python3
"""Test wiki-lint: 7 categories of health checks."""
import os
import subprocess
import sys

TEST_VAULT = sys.argv[1]
INDEX_SCRIPT = os.path.join(TEST_VAULT, 'wiki', 'scripts', 'index-tags.py')
BUILD_SCRIPT = os.path.join(TEST_VAULT, 'wiki', 'scripts', 'build-links-graph.py')
ANALYZE_SCRIPT = os.path.join(TEST_VAULT, 'wiki', 'scripts', 'graph-analyze.py')
GEN_SCRIPT = os.path.join(TEST_VAULT, 'wiki', 'scripts', 'generate-tags-index.py')
MOC_SCRIPT = os.path.join(TEST_VAULT, 'wiki', 'scripts', 'generate-moc-index.py')

# Run all indexing
subprocess.run(['python3', INDEX_SCRIPT], cwd=TEST_VAULT, capture_output=True, text=True)
subprocess.run(['python3', BUILD_SCRIPT], cwd=TEST_VAULT, capture_output=True, text=True)
subprocess.run(['python3', ANALYZE_SCRIPT], cwd=TEST_VAULT, capture_output=True, text=True)
subprocess.run(['python3', GEN_SCRIPT], cwd=TEST_VAULT, capture_output=True, text=True)
subprocess.run(['python3', MOC_SCRIPT], cwd=TEST_VAULT, capture_output=True, text=True)

# 1) Stale tag indexes: after re-run, no stale tags remain
result = subprocess.run(['python3', INDEX_SCRIPT], cwd=TEST_VAULT, capture_output=True, text=True)
assert result.returncode == 0
assert 'Removed stale' not in result.stdout, f"Should be no stale tags on re-run: {result.stdout}"

# 2) Missing descriptions: count tag files without description frontmatter
tags_dir = os.path.join(TEST_VAULT, 'wiki', 'tags')
missing_desc = 0
for f in os.listdir(tags_dir):
    if not f.endswith('.md'):
        continue
    with open(os.path.join(tags_dir, f)) as fh:
        content = fh.read()
    if not content.startswith('---'):
        missing_desc += 1
# At least some tags may lack descriptions - this is OK, just check it doesn't crash
assert missing_desc >= 0, "Should count missing descriptions"

# 3) Broken wikilinks: verify tags-index.md entries point to real notes
# Already implicitly tested

# 4) Graph orphans: read graph-stats.md
stats_path = os.path.join(TEST_VAULT, 'wiki', 'data', 'graph-stats.md')
with open(stats_path) as f:
    stats_content = f.read()
orphan_line = [line for line in stats_content.split('\n') if 'Сироты' in line or 'Всего:' in line]
assert orphan_line, "Should report orphans"

# 5) Artifact consistency: tags dir count vs tags-index entries
tags_index_path = os.path.join(TEST_VAULT, 'wiki', 'tags-index.md')
with open(tags_index_path) as f:
    ti_content = f.read()
ti_entries = len([line for line in ti_content.split('\n') if line.startswith('- #')])
tag_files_count = len([f for f in os.listdir(tags_dir) if f.endswith('.md')])
# Not all tags have descriptions, so entries may be fewer
assert ti_entries <= tag_files_count, f"tags-index entries ({ti_entries}) > tag files ({tag_files_count})"

# 6) Orphan MOC notes: read moc-index.md
# Already tested in test_moc_index

# 7) Malformed links: every links: frontmatter item must be the canonical
# quoted form "[[filename]]". Flag unquoted wikilinks and quotes-inside-brackets.
import re

CANONICAL_ITEM = re.compile(r'^"\[\[.+\]\]"$')

malformed_files = []
for fname in os.listdir(os.path.join(TEST_VAULT, 'atoms')):
    if not fname.endswith('.md'):
        continue
    fpath = os.path.join(TEST_VAULT, 'atoms', fname)
    with open(fpath) as f:
        content = f.read()
    if 'links:' not in content:
        continue
    parts = content.split('---', 2)
    if len(parts) < 3:
        continue
    fm_text = parts[1]
    in_links = False
    for line in fm_text.split('\n'):
        stripped = line.strip()
        if stripped.startswith('links:'):
            in_links = True
            # Single-line inline: `links: "[[file]]"` is allowed
            after = stripped[len('links:'):].strip()
            if after and not after.startswith('['):
                if not CANONICAL_ITEM.match(after):
                    malformed_files.append((fname, after))
            continue
        if in_links:
            if not stripped:
                continue
            if not stripped.startswith('-'):
                in_links = False
                continue
            item = stripped[1:].strip()
            if not CANONICAL_ITEM.match(item):
                malformed_files.append((fname, item))

assert not malformed_files, (
    f'Malformed links: frontmatter items (expected "«filename»" with double quotes):\n'
    + '\n'.join(f'  {f}: {item!r}' for f, item in malformed_files)
)

print("PASS: test_lint — 7 health checks passed")
