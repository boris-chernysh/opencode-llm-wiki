import os
import subprocess
import sys

#!/usr/bin/env python3
"""Test tfidf-suggest.py: similarity > threshold, daily excluded, <1500 cap."""

TEST_VAULT = sys.argv[1]
BUILD_SCRIPT = os.path.join(TEST_VAULT, 'agent', 'scripts', 'build-links-graph.py')
SUGGEST_SCRIPT = os.path.join(TEST_VAULT, 'agent', 'scripts', 'tfidf-suggest.py')
OUTPUT_PATH = os.path.join(TEST_VAULT, 'agent', 'data', 'semantic-suggestions.md')

subprocess.run(['python3', BUILD_SCRIPT], cwd=TEST_VAULT, capture_output=True, text=True)
result = subprocess.run(['python3', SUGGEST_SCRIPT], cwd=TEST_VAULT, capture_output=True, text=True)
assert result.returncode == 0, f"tfidf-suggest.py failed: {result.stderr}"

with open(OUTPUT_PATH) as f:
    content = f.read()

assert 'Semantic Link Suggestions' in content, "Should have suggestions header"

# Count suggestions
lines = [line for line in content.split('\n') if line.startswith('| ') and '|' in line[2:]]
# Filter header and separator
data_lines = [line for line in lines if not line.startswith('| #') and not line.startswith('|---')]
assert len(data_lines) <= 50, f"Should be ≤ 50 suggestions, got {len(data_lines)}"

# Daily notes should NOT appear
assert '2025-01-01' not in content, "Daily notes should be excluded"

# The long articles should have similarity
if data_lines:
    for line in data_lines:
        parts = [p.strip() for p in line.split('|')]
        sim = float(parts[4])
        assert sim >= 0.20, f"Similarity should be >= 0.20, got {sim}"

# Check stdout mentions tokenized docs
assert 'Tokenized' in result.stdout

print(f"PASS: test_tfidf_suggest — {len(lines)} suggestions")
