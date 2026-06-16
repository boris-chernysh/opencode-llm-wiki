#!/usr/bin/env python3
"""Regression: all scripts use defaults without config.json."""
import sys
import os
import subprocess
import tempfile
import shutil

# Create vault with minimal content
vault = tempfile.mkdtemp(prefix='test-noconfig-')
try:
    os.makedirs(os.path.join(vault, 'atoms'))
    os.makedirs(os.path.join(vault, 'daily notes'))

    # Create a simple note
    with open(os.path.join(vault, 'atoms', 'test.md'), 'w') as f:
        f.write('---\ntags:\n  - test\n---\n# Test\n')

    # Copy agent scripts WITHOUT config.json
    agent_dir = os.path.join(vault, 'agent')
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    shutil.copytree(os.path.join(repo_root, 'agent'), agent_dir)
    # Remove config.json
    config_path = os.path.join(agent_dir, 'config.json')
    if os.path.exists(config_path):
        os.remove(config_path)

    scripts = [
        'index-tags.py',
        'generate-tags-index.py',
        'build-links-graph.py',
    ]

    for script in scripts:
        result = subprocess.run(
            ['python3', os.path.join(vault, 'agent', 'scripts', script)],
            cwd=vault, capture_output=True, text=True
        )
        assert result.returncode == 0, f"{script} failed without config: {result.stderr}"

    # Verify index-tags.py still works
    tags_dir = os.path.join(vault, 'agent', 'tags')
    tag_files = [f for f in os.listdir(tags_dir) if f.endswith('.md')]
    assert len(tag_files) > 0, "Should index tags without config"

    print("PASS: test_no_config — scripts use defaults without config.json")
finally:
    shutil.rmtree(vault, ignore_errors=True)
