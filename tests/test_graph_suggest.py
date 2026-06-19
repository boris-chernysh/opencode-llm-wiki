import os
import subprocess
import sys

#!/usr/bin/env python3
"""Test graph-suggest-links.py: Jaccard > 0, shared neighbors, max 50."""


TEST_VAULT = sys.argv[1]
BUILD_SCRIPT = os.path.join(TEST_VAULT, 'wiki', 'scripts', 'build-links-graph.py')
SUGGEST_SCRIPT = os.path.join(TEST_VAULT, 'wiki', 'scripts', 'graph-suggest-links.py')
SUGGEST_PATH = os.path.join(TEST_VAULT, 'wiki', 'data', 'link-suggestions.md')

subprocess.run(['python3', BUILD_SCRIPT], cwd=TEST_VAULT, capture_output=True, text=True)
result = subprocess.run(['python3', SUGGEST_SCRIPT], cwd=TEST_VAULT, capture_output=True, text=True)
assert result.returncode == 0, f"graph-suggest-links.py failed: {result.stderr}"

with open(SUGGEST_PATH) as f:
    content = f.read()

assert 'Link Suggestions' in content, "Should have suggestions header"

# Count suggestions in the table
lines = [line for line in content.split('\n') if line.startswith('| ') and line.count('|') >= 5 and not line.startswith('| #') and not line.startswith('|---')]
assert len(lines) <= 50, f"Should be ≤ 50 suggestions, got {len(lines)}"

# Daily notes should not appear in suggestions (both notes excluded)
assert '2025-01-01' not in content or 'daily-note' not in content, \
    "Daily notes should be excluded from suggestions"

# Verify Jaccard > 0 for suggestions
if lines:
    for line in lines:
        parts = [p.strip() for p in line.split('|')]
        jaccard = float(parts[4])
        assert jaccard > 0.0, f"Jaccard should be > 0, got {jaccard}"

print(f"PASS: test_graph_suggest — {len(lines)} suggestions")
