#!/usr/bin/env python3
"""Test graph-analyze.py: clusters, hubs, orphans."""
import os
import subprocess
import sys


TEST_VAULT = sys.argv[1]
BUILD_SCRIPT = os.path.join(TEST_VAULT, 'agent', 'scripts', 'build-links-graph.py')
ANALYZE_SCRIPT = os.path.join(TEST_VAULT, 'agent', 'scripts', 'graph-analyze.py')
STATS_PATH = os.path.join(TEST_VAULT, 'agent', 'data', 'graph-stats.md')

subprocess.run(['python3', BUILD_SCRIPT], cwd=TEST_VAULT, capture_output=True, text=True)
result = subprocess.run(['python3', ANALYZE_SCRIPT], cwd=TEST_VAULT, capture_output=True, text=True)
assert result.returncode == 0, f"graph-analyze.py failed: {result.stderr}"

with open(STATS_PATH) as f:
    content = f.read()

assert 'Компоненты связности' in content, "Should have connectivity section"
assert 'Хабы' in content, "Should have hubs section"
assert 'Сироты' in content, "Should have orphans section"
assert 'Мосты' in content or 'Кластеры' in content, "Should have bridges or clusters"

# Орфан без связей should appear in orphans
assert 'Орфан без связей' in content, "Orphan note should be listed"

# Cluster section should exist
assert 'label propagation' in content or 'Кластеры' in content

print("PASS: test_graph_analyze")
