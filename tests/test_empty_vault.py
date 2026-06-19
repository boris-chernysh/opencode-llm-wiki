#!/usr/bin/env python3
"""Regression: all scripts run on empty vault without crashing."""
import json
import os
import shutil
import subprocess
import tempfile

# Create empty vault
empty_vault = tempfile.mkdtemp(prefix='test-empty-vault-')
try:
    os.makedirs(os.path.join(empty_vault, 'atoms'))
    os.makedirs(os.path.join(empty_vault, 'daily notes'))

    # Copy agent scripts and config
    agent_dir = os.path.join(empty_vault, 'wiki')
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    shutil.copytree(os.path.join(repo_root, 'wiki'), agent_dir)

    scripts = [
        ('index-tags.py', 'index-tags'),
        ('generate-tags-index.py', 'generate-tags-index'),
        ('build-links-graph.py', 'build-links-graph'),
        ('graph-analyze.py', 'graph-analyze'),
        ('graph-suggest-links.py', 'graph-suggest-links'),
        ('tfidf-suggest.py', 'tfidf-suggest'),
        ('generate-moc-index.py', 'generate-moc-index'),
    ]

    for script, name in scripts:
        result = subprocess.run(
            ['python3', os.path.join(empty_vault, 'wiki', 'scripts', script)],
            cwd=empty_vault, capture_output=True, text=True
        )
        assert result.returncode == 0, f"{name} failed on empty vault: {result.stderr}"

    # Verify empty outputs
    tags_dir = os.path.join(empty_vault, 'wiki', 'tags')
    assert os.path.exists(tags_dir), "tags dir should exist"
    tag_files = [f for f in os.listdir(tags_dir) if f.endswith('.md')]
    assert len(tag_files) == 0, f"Empty vault should have 0 tag files, got {tag_files}"

    data_dir = os.path.join(empty_vault, 'wiki', 'data')
    if os.path.exists(data_dir):
        links_graph = os.path.join(data_dir, 'links-graph.json')
        if os.path.exists(links_graph):
            with open(links_graph) as f:
                graph = json.load(f)
            assert graph['stats']['total_nodes'] == 0, "Empty vault should have 0 nodes"

    print("PASS: test_empty_vault — all 7 scripts handle empty vault gracefully")
finally:
    shutil.rmtree(empty_vault, ignore_errors=True)
