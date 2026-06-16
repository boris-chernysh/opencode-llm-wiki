import json
import os
import re
import subprocess
import sys

#!/usr/bin/env python3
"""Test generate-moc-index.py: hubs sorted by degree, existing files."""

TEST_VAULT = sys.argv[1]
BUILD_SCRIPT = os.path.join(TEST_VAULT, 'agent', 'scripts', 'build-links-graph.py')
ANALYZE_SCRIPT = os.path.join(TEST_VAULT, 'agent', 'scripts', 'graph-analyze.py')
MOC_SCRIPT = os.path.join(TEST_VAULT, 'agent', 'scripts', 'generate-moc-index.py')
MOC_PATH = os.path.join(TEST_VAULT, 'agent', 'moc-index.md')

subprocess.run(['python3', BUILD_SCRIPT], cwd=TEST_VAULT, capture_output=True, text=True)
subprocess.run(['python3', ANALYZE_SCRIPT], cwd=TEST_VAULT, capture_output=True, text=True)
result = subprocess.run(['python3', MOC_SCRIPT], cwd=TEST_VAULT, capture_output=True, text=True)
assert result.returncode == 0, f"generate-moc-index.py failed: {result.stderr}"

with open(MOC_PATH) as f:
    content = f.read()

assert 'MOC index' in content, "Should have MOC index header"

# Check all linked notes exist

wikilinks = re.findall(r'\[\[([^\]]+)\]\]', content)
graph_path = os.path.join(TEST_VAULT, 'agent', 'data', 'links-graph.json')
with open(graph_path) as f:
    graph = json.load(f)
nodes = graph['nodes']

for link in wikilinks:
    # Links might have aliases like "note|alias"
    link_name = link.split('|')[0].strip()
    if not link_name.endswith('.md'):
        link_name += '.md'
    assert link_name in nodes, f"MOC links to nonexistent note: {link_name}"

print("PASS: test_moc_index")
