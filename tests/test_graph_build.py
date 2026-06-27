import importlib.util
import json
import os
import subprocess
import sys

#!/usr/bin/env python3
"""Test build-links-graph.py: nodes, edges, links_in/out consistency."""


TEST_VAULT = sys.argv[1]
BUILD_SCRIPT = os.path.join(TEST_VAULT, 'wiki', 'scripts', 'build-links-graph.py')
GRAPH_PATH = os.path.join(TEST_VAULT, 'wiki', 'data', 'links-graph.json')

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

# Frontmatter `links:` field in all three forms must be counted.
# Each fixture has a single outgoing link to Здоровое питание.
# (Unquoted list form is tested by an in-memory unit test below — the
# canonical lint check rejects unquoted atoms in the fixture set.)
LINK_FIXTURES = {
    '202501010030 quoted-list.md',
    '202501010032 quoted-inline.md',
    '202501010033 inline-list.md',
}
TARGET = '202501010001 Здоровое питание.md'
for src in sorted(LINK_FIXTURES):
    assert src in nodes, f"Fixture {src} should be a node"
    assert TARGET in nodes[src]['links_out'], (
        f"{src} should have outgoing edge to {TARGET}, got {nodes[src]['links_out']}"
    )
    assert src in nodes[TARGET]['links_in'], (
        f"{TARGET} should have incoming edge from {src}, got {nodes[TARGET]['links_in']}"
    )

# In-memory unit test: parser must also count unquoted wikilinks in
# inline form (regression: previously `links: [[file]]` was treated as
# a YAML inline-list, the outer `[[]]` was sliced off, and the link
# was silently dropped).
spec = importlib.util.spec_from_file_location(
    'blg',
    os.path.join(TEST_VAULT, 'wiki', 'scripts', 'build-links-graph.py')
)
blg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(blg)

for unquoted_value in [
    '[[202501010001 Здоровое питание]]',
    '[[202501010001 Здоровое питание]], [[202501010002 Спорт и тренировки]]',
]:
    content = f'---\nlinks: {unquoted_value}\n---\n\nbody\n'
    fields, _ = blg.parse_frontmatter(content)
    raw = fields['links']
    if isinstance(raw, str):
        wikilinks = blg.extract_content_wikilinks(raw)
    else:
        wikilinks = set()
        for item in raw:
            wikilinks.update(blg.extract_content_wikilinks(item))
    assert '202501010001 Здоровое питание' in wikilinks, (
        f"Unquoted value {unquoted_value!r} should yield the wikilink, got {wikilinks}"
    )

print(f"PASS: test_graph_build — {stats['total_nodes']} nodes, {stats['total_edges']} edges, {stats['orphan_nodes']} orphans")
