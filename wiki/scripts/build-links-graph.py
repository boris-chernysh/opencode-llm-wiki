#!/usr/bin/env python3
"""Build a link graph from Obsidian vault notes.

Extracts `links` frontmatter field and `[[wikilinks]]` from body,
builds an adjacency graph, and writes wiki/data/links-graph.json.
"""
import json
import os
import re
from collections import defaultdict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
DATA_DIR = os.path.join(PROJECT_ROOT, 'wiki', 'data')
CONFIG_PATH = os.path.join(PROJECT_ROOT, 'wiki', 'config.json')
SOURCE_DIRS = ['atoms']

def load_config():
    global SOURCE_DIRS
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, encoding='utf-8') as f:
                cfg = json.load(f)
            SOURCE_DIRS = cfg.get('source_dirs', {}).get('graph', SOURCE_DIRS)
        except (json.JSONDecodeError, KeyError):
            pass

def _unwrap_yaml_value(value):
    """Extract all [[...]] wikilink strings from a frontmatter value.

    Accepts the canonical quoted form '"[[file]]"', the unquoted form
    '[[file]]', and inline-list forms '"[[a]]", "[[b]]"' or
    '[["[[a]]", "[[b]]"]]'. Returns either a single wikilink string
    (if exactly one is found) or a list of wikilink strings.
    Non-string values are returned unchanged.
    """
    if not isinstance(value, str):
        return value
    s = value.strip()
    if not s:
        return s
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
        s = s[1:-1].strip()
    matches = re.findall(r'\[\[[^\]]+\]\]', s)
    if not matches:
        return s
    if len(matches) == 1:
        return matches[0]
    return matches


def parse_frontmatter(content):
    """Parse YAML-like frontmatter, return (fields_dict, body_text)."""
    fields = {}
    if not content.startswith('---'):
        return fields, content
    parts = content.split('---', 2)
    if len(parts) < 3:
        return fields, content
    fm_text = parts[1]
    body = parts[2]
    lines = fm_text.split('\n')
    in_list = False
    list_key = None
    list_values = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if in_list and stripped.startswith('-'):
            val = _unwrap_yaml_value(stripped[1:].strip())
            if isinstance(val, list):
                list_values.extend(val)
            elif val:
                list_values.append(val)
            continue
        elif in_list and not stripped.startswith('-'):
            if list_key and list_values:
                fields[list_key] = list_values
            in_list = False
            list_key = None
            list_values = []

        if ':' in stripped:
            key, _, value = stripped.partition(':')
            key = key.strip()
            value = value.strip()
            if not value:
                in_list = True
                list_key = key
                list_values = []
            else:
                fields[key] = _unwrap_yaml_value(value)

    if in_list and list_key and list_values:
        fields[list_key] = list_values

    return fields, body

def extract_content_wikilinks(body_text):
    """Extract [[wikilinks]] from body text (content after frontmatter)."""
    links = set()
    text = body_text
    if isinstance(text, str):
        text = text.strip()
        if len(text) >= 2 and text[0] == text[-1] and text[0] in ('"', "'"):
            text = text[1:-1].strip()
    for match in re.finditer(r'\[\[([^\]]+)\]\]', text):
        target = match.group(1)
        if '|' in target:
            target = target.split('|')[0].strip()
        if '#' in target:
            target = target.split('#')[0].strip()
        target = target.strip()
        if target:
            links.add(target)
    return links

def normalize_filename(name):
    """Ensure filename ends with .md, strip path separators."""
    name = name.strip().strip('/').strip('\\')
    if not name.lower().endswith('.md'):
        name += '.md'
    return name

def build_graph():
    load_config()
    os.makedirs(DATA_DIR, exist_ok=True)

    nodes = {}
    edges = []
    tag_index = defaultdict(set)

    for src_dir in SOURCE_DIRS:
        full_dir = os.path.join(PROJECT_ROOT, src_dir)
        if not os.path.isdir(full_dir):
            continue
        for root, dirs, files in os.walk(full_dir):
            for fname in files:
                if not fname.endswith('.md'):
                    continue
                filepath = os.path.join(root, fname)
                rel_path = os.path.relpath(filepath, PROJECT_ROOT)

                with open(filepath, encoding='utf-8') as f:
                    content = f.read()

                frontmatter, body = parse_frontmatter(content)

                tags = []
                if 'tags' in frontmatter:
                    raw = frontmatter['tags']
                    if isinstance(raw, list):
                        tags = [t.strip() for t in raw if t.strip()]
                    elif isinstance(raw, str):
                        tags = [raw.strip()]

                for tag in tags:
                    tag_index[tag].add(fname)

                fm_links = []
                if 'links' in frontmatter:
                    raw = frontmatter['links']
                    if isinstance(raw, list):
                        for item in raw:
                            wl = extract_content_wikilinks(item)
                            fm_links.extend(wl)
                    elif isinstance(raw, str):
                        fm_links.extend(extract_content_wikilinks(raw))

                body_links_raw = extract_content_wikilinks(body)
                body_links = {normalize_filename(link) for link in body_links_raw}
                fm_links_norm = {normalize_filename(link) for link in fm_links}

                all_out = fm_links_norm | body_links
                all_out.discard(fname)

                nodes[fname] = {
                    'tags': tags,
                    'links_out': sorted(all_out),
                    'links_in': [],
                    'degree_out': len(all_out),
                    'degree_in': 0,
                    'cluster': -1,
                    'path': rel_path,
                    'source_dir': src_dir
                }

                for target in all_out:
                    edges.append([fname, target])

    for fname, targets in nodes.items():
        for target in targets['links_out']:
            if target in nodes:
                nodes[target]['links_in'].append(fname)
                nodes[target]['degree_in'] += 1

    orphan_count = sum(1 for n in nodes.values() if n['degree_out'] == 0 and n['degree_in'] == 0)

    graph = {
        'nodes': nodes,
        'edges': edges,
        'stats': {
            'total_nodes': len(nodes),
            'total_edges': len(edges),
            'orphan_nodes': orphan_count,
            'tags_indexed': len(tag_index),
            'avg_degree': round(len(edges) / len(nodes), 1) if nodes else 0
        }
    }

    output_path = os.path.join(DATA_DIR, 'links-graph.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)

    print(f'Graph built: {graph["stats"]["total_nodes"]} nodes, {graph["stats"]["total_edges"]} edges')
    print(f'Orphans: {orphan_count}, Tags: {tag_index["__total__"] if "__total__" in tag_index else "N/A"}')
    print(f'Saved to {output_path}')

    return graph

if __name__ == '__main__':
    build_graph()
