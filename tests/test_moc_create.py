#!/usr/bin/env python3
"""Test wiki-moc create: cluster identification, MOC file validation."""
import sys
import os
import subprocess
import json

TEST_VAULT = sys.argv[1]

# Run graph pipeline
subprocess.run(['python3', os.path.join(TEST_VAULT, 'agent', 'scripts', 'build-links-graph.py')],
               cwd=TEST_VAULT, capture_output=True, text=True)
subprocess.run(['python3', os.path.join(TEST_VAULT, 'agent', 'scripts', 'graph-analyze.py')],
               cwd=TEST_VAULT, capture_output=True, text=True)

# Read graph to check cluster structure
graph_path = os.path.join(TEST_VAULT, 'agent', 'data', 'links-graph.json')
with open(graph_path, 'r') as f:
    graph = json.load(f)

clusters = graph.get('clusters', {})
assert len(clusters) > 0, "Should have clusters after analysis"

# Find a cluster with size >= 3 and check tag coherence
nodes = graph['nodes']
for label, members in clusters.items():
    if len(members) >= 3:
        # Check tag coherence
        tag_counts = {}
        for m in members:
            if m in nodes:
                for t in nodes[m].get('tags', []):
                    tag_counts[t] = tag_counts.get(t, 0) + 1
        # At least one tag should appear in multiple members
        common_tags = [t for t, c in tag_counts.items() if c >= 2]
        if common_tags:
            label_int = int(label) if label.lstrip('-').isdigit() else label
            print(f"  Cluster {label_int}: size={len(members)}, common_tags={common_tags[:3]}")
            break

# Verify moc-index.md was generated
moc_path = os.path.join(TEST_VAULT, 'agent', 'moc-index.md')
assert os.path.exists(moc_path), "moc-index.md should exist"

with open(moc_path, 'r') as f:
    moc_content = f.read()
assert 'MOC index' in moc_content, "Should have MOC index header"

print(f"PASS: test_moc_create — {len(clusters)} clusters, MOC index generated")
