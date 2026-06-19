import os
import re
import subprocess
import sys

#!/usr/bin/env python3
"""Test index-dates.py: monthly index files, note entries, directory structure."""

TEST_VAULT = sys.argv[1]
SCRIPT = os.path.join(TEST_VAULT, 'wiki', 'scripts', 'index-dates.py')
DATES_DIR = os.path.join(TEST_VAULT, 'wiki', 'dates')

result = subprocess.run(['python3', SCRIPT], cwd=TEST_VAULT, capture_output=True, text=True)
assert result.returncode == 0, f"index-dates.py failed: {result.stderr}"

assert os.path.isdir(DATES_DIR), "wiki/dates/ directory should exist"

year_dirs = [d for d in os.listdir(DATES_DIR) if os.path.isdir(os.path.join(DATES_DIR, d))]
assert len(year_dirs) >= 1, "Should have at least one year directory"

monthly_files = []
for ydir in year_dirs:
    ypath = os.path.join(DATES_DIR, ydir)
    for f in os.listdir(ypath):
        if f.endswith('.md'):
            monthly_files.append(os.path.join(ypath, f))

assert len(monthly_files) >= 1, "Should have at least one monthly index file"

for mf in monthly_files:
    with open(mf) as f:
        content = f.read()
    assert '---' in content, "Should have frontmatter"
    assert 'description:' in content, "Should have description field"

    wikilinks = re.findall(r'\[\[([^\]]+)\]\]', content)
    assert len(wikilinks) >= 1, f"Monthly file {mf} should have at least one note entry"

print("PASS: test_dates_index")
