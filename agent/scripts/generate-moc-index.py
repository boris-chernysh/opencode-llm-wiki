#!/usr/bin/env python3
"""Generate MOC (Map of Content) index from hub notes.

Scans atoms/ for notes with `links:` frontmatter field,
identifies hub notes (high out-degree), and generates agent/moc-index.md.
"""
import json
import os

from collections import defaultdict




SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
DATA_DIR = os.path.join(PROJECT_ROOT, 'agent', 'data')
GRAPH_PATH = os.path.join(DATA_DIR, 'links-graph.json')
OUTPUT_PATH = os.path.join(PROJECT_ROOT, 'agent', 'moc-index.md')
CONFIG_PATH = os.path.join(PROJECT_ROOT, 'agent', 'config.json')

MIN_LINKS = 5
MAX_ENTRIES = 50

def load_config():
    global MIN_LINKS
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, encoding='utf-8') as f:
                cfg = json.load(f)
            MIN_LINKS = cfg.get('thresholds', {}).get('min_cluster_size_for_moc', MIN_LINKS)
        except (json.JSONDecodeError, KeyError):
            pass

def load_graph():
    with open(GRAPH_PATH, encoding='utf-8') as f:
        return json.load(f)

def generate_index(graph):
    nodes = graph['nodes']

    hubs = []
    for name, node in nodes.items():
        degree = node['degree_out'] + node['degree_in']
        if degree >= MIN_LINKS:
            hubs.append((name, node, degree))

    hubs.sort(key=lambda x: x[2], reverse=True)
    hubs = hubs[:MAX_ENTRIES]

    clusters = defaultdict(list)
    for name, node in nodes.items():
        cluster_id = node.get('cluster', -1)
        clusters[str(cluster_id)].append(name)

    lines = [
        '---',
        'description: Индекс MOC-хабов (Maps of Content) — заметки-оглавления с высоким количеством связей.',
        '---',
        '',
        '# MOC index',
        ''
    ]

    for idx, (name, node, degree) in enumerate(hubs, 1):
        tags = ', '.join(f'`{t}`' for t in node.get('tags', [])[:3]) or '—'
        out_links = node.get('links_out', [])[:5]
        links_str = ', '.join(f'[[{link_name}]]' for link_name in out_links)
        cluster_id = node.get('cluster', -1)
        cluster_size = len(clusters.get(str(cluster_id), []))

        lines.append(f'## {idx}. [[{name}]]')
        lines.append(f'- Degree: {degree} (out: {node["degree_out"]}, in: {node["degree_in"]})')
        lines.append(f'- Tags: {tags}')
        lines.append(f'- Cluster: {cluster_id} (size: {cluster_size})')
        lines.append(f'- Linked: {links_str}')
        if len(node.get('links_out', [])) > 5:
            lines.append(f'  ... и ещё {len(node["links_out"]) - 5}')
        lines.append('')

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')

    print(f'Written MOC index ({len(hubs)} hubs) to {OUTPUT_PATH}')

def main():
    load_config()
    graph = load_graph()
    generate_index(graph)

if __name__ == '__main__':
    main()
