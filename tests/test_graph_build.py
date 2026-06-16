import json
import os
import subprocess
import sys

#!/usr/bin/env python3
"""Test build-links-graph.py: nodes, edges, links_in/out consistency."""


TEST_VAULT = sys.argv[1]
BUILD_SCRIPT = os.path.join(TEST_VAULT, 'agent', 'scripts', 'build-links-graph.py')
GRAPH_PATH = os.path.join(TEST_VAULT, 'agent', 'data', 'links-graph.json')

result = subprocess.run(['python3', BUILD_SCRIPT], cwd=TEST_VAULT, capture_output=True, text=True)
assert result.returncode == 0, f"build-links-graph.py failed: {result.stderr}"

with open(GRAPH_PATH) as f:
    graph = json.load(f)

nodes = graph['nodes']
edges = graph['edges']
stats = graph['stats']

assert stats['total_nodes'] > 0, "Should have nodes"
assert stats['total_nodes'] >= 18, f"Expected 18+ atoms, got {stats['total_nodes']}"
assert stats['total_edges'] > 0, "Should have edges"

# Check links_out/links_in consistency
for fname, node in nodes.items():
    for target in node['links_out']:
        if target in nodes:
            assert fname in nodes[target]['links_in'], \
                f"Inconsistent: {fname} -> {target} but target.links_in missing {fname}"

# Verify source_dir is set
for fname, node in nodes.items():
    assert 'source_dir' in node, f"source_dir missing for {fname}"
    assert node['source_dir'] == 'atoms', f"{fname} source_dir should be atoms, got {node['source_dir']}"

# Broken link to nonexistent note should NOT be in nodes' links_out as a node
# (it appears in edges, but the target won't have a node entry)
assert 'несуществующая заметка.md' not in nodes, "Nonexistent note should not be a node"

print(f"PASS: test_graph_build — {stats['total_nodes']} nodes, {stats['total_edges']} edges, {stats['orphan_nodes']} orphans")
