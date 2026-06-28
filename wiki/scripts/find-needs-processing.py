#!/usr/bin/env python3
"""Find notes whose frontmatter `tags:` list contains `need-processing`.

Walks `atoms/` (and optionally `daily notes/`) and prints the filename of
each match, one per line, capped at `max_results` (default 10).

This is the canonical discovery step for `wiki-ingest`. It only inspects
YAML frontmatter, so it ignores body text, headings, and filenames that
happen to contain the string "need-processing" — eliminating the
false positives produced by a naive grep.

Idempotent. Stdlib only.
"""

import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
CONFIG_PATH = os.path.join(PROJECT_ROOT, 'wiki', 'config.json')

TARGET_TAG = 'need-processing'
DEFAULT_SOURCE_DIRS = ['atoms']
DEFAULT_MAX_RESULTS = 10


def load_config():
    source_dirs = list(DEFAULT_SOURCE_DIRS)
    max_results = DEFAULT_MAX_RESULTS
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, encoding='utf-8') as f:
                cfg = json.load(f)
            configured = cfg.get('source_dirs', {}).get('ingest')
            if isinstance(configured, list) and configured:
                source_dirs = configured
            limits = cfg.get('thresholds', {})
            if isinstance(limits.get('max_ingest_per_run'), int):
                max_results = limits['max_ingest_per_run']
        except (json.JSONDecodeError, KeyError, TypeError):
            pass
    return source_dirs, max_results


def parse_frontmatter_tags(lines):
    """Extract tags from a list of frontmatter lines (the inner part between `---` markers).

    Supports both inline-list (`tags: [a, b]`) and block-list (`tags:\n  - a`) forms.
    """
    tags = []
    in_list = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('tags:'):
            value = stripped[len('tags:'):].strip()
            if value.startswith('[') and value.endswith(']'):
                for t in value[1:-1].split(','):
                    t = t.strip().strip('"').strip("'").strip()
                    if t:
                        tags.append(t)
                in_list = False
            elif value:
                tags.append(value)
                in_list = False
            else:
                in_list = True
        elif in_list and stripped.startswith('-'):
            t = stripped[1:].strip().strip('"').strip("'").strip()
            if t:
                tags.append(t)
        elif in_list and stripped and not stripped.startswith('-') and not stripped.startswith('#'):
            in_list = False
    return tags


def frontmatter_has_tag(filepath, tag):
    """Return True iff `tag` is present in the note's frontmatter `tags:` list."""
    try:
        with open(filepath, encoding='utf-8') as f:
            content = f.read()
    except (OSError, UnicodeDecodeError):
        return False

    if not content.startswith('---'):
        return False
    parts = content.split('---', 2)
    if len(parts) < 3:
        return False

    fm_lines = parts[1].split('\n')
    tags = parse_frontmatter_tags(fm_lines)
    target = tag.lower()
    return any(t.lower() == target for t in tags)


def find_needs_processing(source_dirs, max_results):
    matches = []
    for src_dir in source_dirs:
        full_dir = os.path.join(PROJECT_ROOT, src_dir)
        if not os.path.isdir(full_dir):
            continue
        for root, _dirs, files in os.walk(full_dir):
            for name in sorted(files):
                if not name.endswith('.md'):
                    continue
                filepath = os.path.join(root, name)
                if frontmatter_has_tag(filepath, TARGET_TAG):
                    matches.append(name)
                    if len(matches) >= max_results:
                        return matches
    return matches


def main():
    source_dirs, max_results = load_config()
    results = find_needs_processing(source_dirs, max_results)
    for name in results:
        print(name)
    print(f'Found {len(results)} note(s) with #{TARGET_TAG} in frontmatter (limit {max_results}).',
          file=sys.stderr)


if __name__ == '__main__':
    main()
